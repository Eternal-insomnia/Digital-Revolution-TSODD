import geopandas as gpd
from fastapi import UploadFile, HTTPException
from io import BytesIO
import zipfile
import os
import tempfile
import json
from datetime import datetime
from shapely.geometry import Point, LineString
from shapely.ops import unary_union
import pandas as pd

class GeojsonService:
    async def shp_to_geojson(
            self,
            shp_files: list[UploadFile],
            shx_files: list[UploadFile],
            dbf_files: list[UploadFile],
            prj_files: list[UploadFile],
            cpg_files: list[UploadFile]
    ) -> list[str]:
        if not (len(shp_files) == len(shx_files) == len(dbf_files) == len(prj_files) == len(cpg_files)):
            raise HTTPException(status_code=400, detail="Error: Each shapefile dataset must include .shp, .shx, .dbf, .prj, and .cpg files.")

        # Массив для хранения всех GeoJSON-данных
        geojson_list = []

        # Обрабатываем каждый набор файлов
        for i in range(len(shp_files)):
            # Создаем zip-архив в памяти
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zip_archive:
                # Записываем каждый файл в архив
                for ext, file in {"shp": shp_files[i], "shx": shx_files[i], "dbf": dbf_files[i], "prj": prj_files[i],
                                  "cpg": cpg_files[i]}.items():
                    zip_archive.writestr(f"upload.{ext}", await file.read())
            zip_buffer.seek(0)

            # Создаем временный файл для zip-архива
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_zip_file:
                temp_zip_file.write(zip_buffer.getvalue())
                temp_zip_file_path = temp_zip_file.name

            # Читаем zip-архив с помощью GeoPandas
            try:
                gdf = gpd.read_file(f"zip://{temp_zip_file_path}")
                geojson_data = json.loads(gdf.to_json())

                geojson_data["name"] = os.path.splitext(shp_files[i].filename)[0]  # Добавляем название файла
                geojson_list.append(geojson_data)

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error processing shapefile set {i + 1}: {str(e)}")
            finally:
                # Удаляем временный файл после чтения
                os.remove(temp_zip_file_path)

        # Возвращаем все GeoJSON-файлы в виде JSON-ответа
        return geojson_list

    def save_geojson(self, geojson_data):
        if isinstance(geojson_data, str):
            geojson_data = json.loads(geojson_data)
        os.makedirs("geojson", exist_ok=True)
        filename = f"geojson/{datetime.now().strftime('%Y%m%d%H%M%S')}.geojson"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(geojson_data, f, ensure_ascii=False, indent=4)

    def merge_houses(self, geojson_list):
        # Регулярное выражение для поиска нужных названий
        pattern = r"House_\d+очередь_ЖК"

        # Массив для всех уникальных feature
        all_features = []
        seen_features = set()  # Для отслеживания уникальных объектов

        # Проходим по всем geojson в списке
        for geojson_data in geojson_list:
            # Проверяем, что имя файла соответствует паттерну
            if geojson_data.get("name", "").startswith("House_") and "очередь_ЖК" in geojson_data["name"]:
                # Добавляем все features из этого geojson, избегая дубли
                for feature in geojson_data["features"]:
                    feature_id = json.dumps(feature["geometry"])  # Используем геометрию для уникальности
                    if feature_id not in seen_features:
                        seen_features.add(feature_id)
                        all_features.append(feature)

        # Формируем новый GeoJSON с уникальными features
        merged_geojson = {
            "type": "FeatureCollection",
            "name": "Houses_ЖК",  # Название для объединенного GeoJSON
            "crs": geojson_list[0]["crs"],  # Копируем CRS из первого GeoJSON
            "features": all_features
        }

        return merged_geojson

    def correct_shapefile_order(self, shapefile_path):
        # Загружаем shapefile
        gdf = gpd.read_file(shapefile_path)

        # Исправляем геометрию, если кольца имеют неправильный порядок обхода
        gdf['geometry'] = gdf['geometry'].apply(lambda x: x if x.is_valid else x.buffer(0))

        return gdf

    def add_base_objects(self, merged_geojson, geojson_list):
        # Преобразуем объединенный GeoJSON в GeoDataFrame
        merged_gdf = gpd.GeoDataFrame.from_features(merged_geojson["features"], crs="EPSG:3857")

        # Множество для хранения всех домов из объединенного geojson
        merged_houses = unary_union(merged_gdf.geometry)

        # Функция для проверки расстояния (1 км)
        def within_1km(geom, reference_geom):
            return geom.distance(reference_geom) <= 1000

        # 1. Добавляем выходы метро (если есть)
        metro_gdf = None
        for geojson_data in geojson_list:
            if geojson_data.get("name", "").startswith("Выходы_метро"):
                metro_gdf = gpd.GeoDataFrame.from_features(geojson_data["features"], crs="EPSG:3857")
                metro_gdf = metro_gdf[
                    metro_gdf.geometry.apply(lambda x: isinstance(x, Point))]  # Оставляем только точки
                break

        if metro_gdf is not None:
            merged_gdf = pd.concat([merged_gdf, metro_gdf], ignore_index=True)

        # 2. Добавляем остановки общественного транспорта (если есть)
        ot_gdf = None
        for geojson_data in geojson_list:
            if geojson_data.get("name", "").startswith("Остановки_ОТ"):
                ot_gdf = gpd.GeoDataFrame.from_features(geojson_data["features"], crs="EPSG:3857")
                ot_gdf = ot_gdf[ot_gdf.geometry.apply(lambda x: isinstance(x, Point))]  # Оставляем только точки
                break

        if ot_gdf is not None:
            # Фильтруем только те остановки, которые находятся в радиусе 1 км от любого дома
            ot_gdf = ot_gdf[ot_gdf.geometry.apply(lambda x: any(within_1km(x, house) for house in merged_houses.geoms))]
            merged_gdf = pd.concat([merged_gdf, ot_gdf], ignore_index=True)

        # 3. Добавляем дома из "Дома_исходные" (если есть)
        houses_gdf = None
        for geojson_data in geojson_list:
            if geojson_data.get("name", "").startswith("Дома_исходные"):
                houses_gdf = gpd.GeoDataFrame.from_features(geojson_data["features"], crs="EPSG:3857")
                break

        if houses_gdf is not None:
            valid_houses = []
            for _, house in houses_gdf.iterrows():
                house_geom = house.geometry
                # Проверяем, что дом не пересекается с уже добавленными
                if not any(house_geom.intersects(existing_house) for existing_house in merged_houses.geoms):
                    # Проверяем, что дом находится не дальше 1 км от любого дома из объединенного GeoJSON
                    if any(within_1km(house_geom, existing_house) for existing_house in merged_houses.geoms):
                        valid_houses.append(house)

            # Добавляем валидные дома
            if valid_houses:
                valid_houses_gdf = gpd.GeoDataFrame(valid_houses, crs=houses_gdf.crs)
                merged_gdf = pd.concat([merged_gdf, valid_houses_gdf], ignore_index=True)

        # Формируем итоговый GeoJSON
        merged_geojson = merged_gdf.to_json()
        merged_geojson = json.loads(merged_geojson)
        return merged_geojson

    def add_roads(self, merged_geojson, geojson_list):
        # Преобразуем объединенный GeoJSON в GeoDataFrame
        merged_gdf = gpd.GeoDataFrame.from_features(merged_geojson["features"], crs="EPSG:3857")

        # Множество для хранения всех домов из объединенного geojson
        merged_houses = unary_union(merged_gdf.geometry)

        # Функция для проверки расстояния (1 км)
        def within_1km(geom, reference_geom):
            return geom.distance(reference_geom) <= 1000

        # Найдем все файлы с дорогами
        roads_gdf_list = []
        for geojson_data in geojson_list:
            if geojson_data.get("name", "").startswith("Streets_"):
                roads_gdf = gpd.GeoDataFrame.from_features(geojson_data["features"], crs="EPSG:3857")
                roads_gdf = roads_gdf[
                    roads_gdf.geometry.apply(lambda x: isinstance(x, LineString))]  # Оставляем только линии
                roads_gdf_list.append(roads_gdf)

        # Объединяем все дороги в один GeoDataFrame
        all_roads_gdf = pd.concat(roads_gdf_list, ignore_index=True) if roads_gdf_list else None

        if all_roads_gdf is not None:
            # Фильтруем только те дороги, которые находятся в радиусе 1 км от любого дома
            valid_roads = all_roads_gdf[
                all_roads_gdf.geometry.apply(lambda x: any(within_1km(x, house) for house in merged_houses.geoms))]

            # Убираем дубликаты дорог (если дороги повторяются в разных файлах)
            valid_roads = valid_roads.drop_duplicates(subset=["geometry"])

            # Формируем итоговый GeoJSON с только дорогами
            roads_geojson = valid_roads.to_json()
            roads_geojson = json.loads(roads_geojson)
            return roads_geojson
        else:
            return None