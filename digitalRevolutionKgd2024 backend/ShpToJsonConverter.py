import geopandas as gpd
import os


def shp_to_geojson(shp_path, output_path):
    """
    Конвертация SHP в GeoJSON.

    :param shp_path: Путь к исходному SHP-файлу.
    :param output_path: Путь для сохранения выходного GeoJSON-файла.
    """
    try:
        # Чтение SHP файла
        gdf = gpd.read_file(shp_path)

        # Запись в GeoJSON
        gdf.to_file(output_path, driver="GeoJSON")

        print(f"Файл успешно сохранён в {output_path}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")


# Пример использования
shp_file = "shp/Выходы_метро.shp"  # замените на путь к вашему SHP файлу
output_geojson = "out.geojson"  # путь для сохранения GeoJSON
shp_to_geojson(shp_file, output_geojson)