import geopandas as gpd
import json

def parse_geo(gdf, load_test_result):
    # Инициализация списка для удаления дорог
    delete_roads = []
    overload_roads = []

    # Поиск и добавление строк, которые удовлетворяют условиям
    for road in gdf["id"]:
        if road in load_test_result:
            if load_test_result[road] < 10:
                # Преобразование строки GeoDataFrame в формат Feature и добавление в список
                row = gdf[gdf['id'] == road].iloc[0]  # Получаем строку
                feature = {
                    "type": "Feature",
                    "geometry": row["geometry"].__geo_interface__,  # Преобразование геометрии
                    "properties": row.drop("geometry").to_dict()  # Преобразование атрибутов
                }
                delete_roads.append(feature)
            elif load_test_result[road] > 800:
                row = gdf[gdf['id'] == road].iloc[0]  # Получаем строку
                feature = {
                    "type": "Feature",
                    "geometry": row["geometry"].__geo_interface__,  # Преобразование геометрии
                    "properties": row.drop("geometry").to_dict()  # Преобразование атрибутов
                }
                overload_roads.append(feature)

    # Формируем новый GeoJSON с уникальными features
    merged_geojson = {
        "type": "FeatureCollection",
        "features": delete_roads
    }

    # Преобразуем словарь в GeoDataFrame
    tmp = gpd.GeoDataFrame.from_features(merged_geojson['features'])

    # Сохраняем результат в GeoJSON файл
    tmp.to_file('red_roads.geojson', driver='GeoJSON')

    print("GeoJSON файл с удалёнными дорогами создан")

    # Подмножество строк, которые нужно удалить из gdf
    tmp = gpd.read_file('red_roads.geojson')

    # Используем метод .isin() для фильтрации строк в gdf, которых нет в tmp
    # Предполагаем, что у вас есть уникальный идентификатор, например, "id"
    filtered_gdf = gdf[~gdf['id'].isin(tmp['id'])]

    # Формируем новый GeoJSON с уникальными features
    merged_geojson = {
        "type": "FeatureCollection",
        "features": overload_roads
    }

    # Преобразуем словарь в GeoDataFrame
    tmp = gpd.GeoDataFrame.from_features(merged_geojson['features'])

    # Сохраняем результат в GeoJSON файл
    tmp.to_file('overload_roads.geojson', driver='GeoJSON')

    print("GeoJSON файл с перегруженными дорогами создан")

    # Подмножество строк, которые нужно удалить из gdf
    tmp = gpd.read_file('overload_roads.geojson')

    # Используем метод .isin() для фильтрации строк в gdf, которых нет в tmp
    # Предполагаем, что у вас есть уникальный идентификатор, например, "id"
    new_filtered_gdf = filtered_gdf[~filtered_gdf['id'].isin(tmp['id'])]

    # Сохраняем отфильтрованный GeoDataFrame в новый GeoJSON файл
    new_filtered_gdf.to_file('grey_roads.geojson', driver='GeoJSON')

    print("GeoJSON файл с обычными дорогами создан")


if __name__ == "__main__":
    # Чтение GeoJSON файла
    gdf = gpd.read_file('data/ТестДороги.geojson')
    # Чтение файла JSON
    with open('data/loadtest_result.json', 'r', encoding='utf-8') as file:
        load_test_result = json.load(file)
    parse_geo(gdf, load_test_result)