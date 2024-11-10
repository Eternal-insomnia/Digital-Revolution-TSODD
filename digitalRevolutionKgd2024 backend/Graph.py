import json
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial.distance import cdist, euclidean
import AStar_GOD

from scipy.spatial import KDTree

def calculate_polygon_centroid(coords):
    """Вычисляет центроид для одного полигона"""
    flat_coords = np.array(coords[0])
    centroid_x = np.mean([coord[0] for coord in flat_coords])
    centroid_y = np.mean([coord[1] for coord in flat_coords])
    return centroid_x, centroid_y


def calculate_multipolygon_centroid(multi_coords):
    """Вычисляет общий центроид для мультиполигона"""
    centroids = []
    for polygon in multi_coords:
        centroid = calculate_polygon_centroid([polygon[0]])
        centroids.append(centroid)
    return np.mean([c[0] for c in centroids]), np.mean([c[1] for c in centroids])


def find_nearest_road_point(building_pos, road_nodes_pos):
    """
    Находит ближайшую точку дороги к зданию

    Args:
        building_pos: tuple (x, y) - координаты здания
        road_nodes_pos: dict - словарь с координатами точек дорог

    Returns:
        str: id ближайшей точки дороги
    """
    building_coords = np.array([[building_pos[0], building_pos[1]]])
    road_coords = np.array([[pos[0], pos[1]] for pos in road_nodes_pos.values()])
    road_node_ids = list(road_nodes_pos.keys())

    if len(road_coords) == 0:
        return None

    distances = cdist(building_coords, road_coords).flatten()
    nearest_idx = np.argmin(distances)
    return road_node_ids[nearest_idx]


def are_points_close(point1, point2, threshold=0.01):
    """
    Проверяет, находятся ли две точки в пределах заданного порога.

    Args:
        point1 (tuple): Координаты первой точки (x, y)
        point2 (tuple): Координаты второй точки (x, y)
        threshold (float): Порог для проверки близости (по умолчанию 0.01)

    Returns:
        bool: True, если точки близки, иначе False.
    """
    return euclidean(point1, point2) < threshold


def merge_road_points(road_points):
    """
    Мержит точки дорог с одинаковыми координатами в одну.

    Аргументы:
    road_points: dict - словарь с точками дорог

    Возвращает:
    dict - обновленный словарь с объединенными точками
    """
    merged_points = {}
    point_id_map = {}  # Маппинг старых точек на новые

    for point, coords in road_points.items():
        # Если такой координаты еще нет, добавляем
        if coords not in merged_points.values():
            merged_points[point] = coords
            point_id_map[coords] = point
        else:
            # Если такие координаты уже есть, то ищем существующую точку
            existing_point = point_id_map[coords]
            # Объединяем с существующей точкой, если они одинаковые
            if existing_point != point:
                # Обновить маппинг точек на основе существующих координат
                point_id_map[coords] = existing_point
                # Здесь можно добавить логику для объединения данных о точках
                # Например, если у точек разные цвета или типы, мы можем обновить их
                # в merged_points или создать правила для слияния.
                pass

    return merged_points


# Порог для соединения точек
DIST_THRESHOLD = 0.01  # Пороговое расстояние, которое определяет, что точки можно считать близкими

def create_road_network_graph(buildings_geojson, roads_geojson):
    # Создаем направленный граф
    G = nx.Graph()

    # Словарь для хранения точек дорог
    road_points = {}

    # Сначала добавляем все дороги и их точки
    for feature in roads_geojson['features']:
        if feature['geometry']['type'] == 'LineString':
            coords = feature['geometry']['coordinates']
            id = feature['id']
            road_id = f"r_{id}"

            # Добавляем узлы для начала и конца дороги
            start_point = f"{road_id}_start"
            end_point = f"{road_id}_end"

            start_coords = (coords[0][0], coords[0][1])
            end_coords = (coords[-1][0], coords[-1][1])

            # Сохраняем координаты точек дорог
            road_points[start_point] = start_coords
            road_points[end_point] = end_coords

            G.add_node(start_point,
                       pos=start_coords,
                       node_type='junction',
                       node_color='blue',
                       node_size=50)
            G.add_node(end_point,
                       pos=end_coords,
                       node_type='junction',
                       node_color='blue',
                       node_size=50)

            # Добавляем ребро для дороги
            distance = np.linalg.norm(np.array(start_coords) - np.array(end_coords))
            road_type = feature['properties'].get('ROAD_CATEG', 'Unknown')
            is_footpath = feature['properties'].get('Foot', 0) == 1

            G.add_edge(start_point, end_point,
                       id=id,
                       weight=distance,
                       road_type=road_type,
                       is_footpath=is_footpath)

    # Теперь добавляем здания и связываем их с ближайшими точками дорог
    for feature in buildings_geojson['features']:
        geom_type = feature['geometry']['type']
        feature_id = f"b_{feature['id']}"

        # Определяем тип объекта и его параметры
        if feature['properties'].get('TrType'):
            building_type = "ot"
            node_type = 'transport_stop'
            node_color = 'yellow'
            node_size = 200
        elif feature['properties'].get('Text') and feature['properties'].get('Number'):
            building_type = "metro"
            node_type = 'metro'
            node_color = 'purple'
            node_size = 300
        elif feature['properties'].get('Type') == "Школы":
            building_type = "school"
            node_type = 'building'
            node_color = 'red'
            apartments = feature['properties'].get('Apartments')
            node_size = 200
        elif feature['properties'].get('Type') == "Дошкольные":
            building_type = "sad"
            node_type = 'building'
            node_color = 'red'
            apartments = feature['properties'].get('Apartments')
            node_size = 200
        else:
            node_type = 'building'
            building_type = "building"
            node_color = 'red'
            apartments = feature['properties'].get('Apartments')
            apartments = 0 if apartments is None else float(apartments)
            node_size = apartments / 10 + 100 if apartments else 100

        # Вычисляем координаты центроида
        if geom_type == 'Polygon':
            centroid_x, centroid_y = calculate_polygon_centroid(feature['geometry']['coordinates'])
        elif geom_type == 'MultiPolygon':
            centroid_x, centroid_y = calculate_multipolygon_centroid(feature['geometry']['coordinates'])
        elif geom_type == 'Point':
            coords = feature['geometry']['coordinates']
            centroid_x, centroid_y = coords[0], coords[1]
        else:
            continue


        # Добавляем узел здания в граф
        G.add_node(feature_id,
                   pos=(centroid_x, centroid_y),
                   node_type=node_type,
                   building_type = building_type,
                   node_color=node_color,
                   node_size=node_size)

        # Находим ближайшую точку дороги и создаем связь
        nearest_road_point = find_nearest_road_point((centroid_x, centroid_y), road_points)
        if nearest_road_point:
            # Добавляем ребро между зданием и ближайшей точкой дороги
            G.add_edge(feature_id, nearest_road_point,
                       id=None,
                       weight=1.0,
                       road_type='building_connection',
                       is_footpath=True)
            G.add_edge(nearest_road_point, feature_id,
                       id=None,
                       weight=1.0,
                       road_type='building_connection',
                       is_footpath=True)

    # Соединяем точки дорог, если они достаточно близки
    road_nodes = list(road_points.keys())
    for i in range(len(road_nodes)):
        for j in range(i + 1, len(road_nodes)):
            node1 = road_nodes[i]
            node2 = road_nodes[j]
            coords1 = np.array(road_points[node1])
            coords2 = np.array(road_points[node2])

            # Если расстояние между точками меньше порога, соединяем их
            if np.linalg.norm(coords1 - coords2) < DIST_THRESHOLD:
                road_id = f"{node1}_{node2}"
                G.add_edge(node1, node2, ids=[road_id], weight=np.linalg.norm(coords1 - coords2))

    return G


def visualize_graph(G):
    plt.figure(figsize=(15, 15))

    # Получаем позиции узлов
    pos = nx.get_node_attributes(G, 'pos')

    # Рисуем рёбра (дороги)
    edges = G.edges(data=True)
    road_edges = [(u, v) for u, v, d in edges if not d.get('is_footpath', False)]
    footpath_edges = [(u, v) for u, v, d in edges if
                      d.get('is_footpath', False) and d.get('road_type') != 'building_connection']
    building_connections = [(u, v) for u, v, d in edges if d.get('road_type') == 'building_connection']

    # Рисуем различные типы рёбер
    nx.draw_networkx_edges(G, pos, edgelist=road_edges, edge_color='gray', width=2)
    nx.draw_networkx_edges(G, pos, edgelist=footpath_edges, edge_color='green', style='dashed', width=1)
    nx.draw_networkx_edges(G, pos, edgelist=building_connections, edge_color='orange', style='dotted', width=1,
                           alpha=0.5)

    # Группируем узлы по типам
    node_types = {
        'building': {'nodes': [], 'color': 'red', 'sizes': []},
        'transport_stop': {'nodes': [], 'color': 'yellow', 'sizes': []},
        'metro': {'nodes': [], 'color': 'purple', 'sizes': []},
        'junction': {'nodes': [], 'color': 'blue', 'sizes': []}
    }

    for node, attr in G.nodes(data=True):
        node_type = attr.get('node_type', 'junction')
        if node_type in node_types:
            node_types[node_type]['nodes'].append(node)
            node_types[node_type]['sizes'].append(attr.get('node_size', 50))

    # Рисуем узлы по типам
    for node_type, data in node_types.items():
        if data['nodes']:
            nx.draw_networkx_nodes(G, pos,
                                   nodelist=data['nodes'],
                                   node_color=data['color'],
                                   node_size=data['sizes'],
                                   alpha=0.6)

    # Добавляем легенду
    legend_elements = [
        plt.Line2D([0], [0], color='gray', linewidth=2, label='Дороги'),
        plt.Line2D([0], [0], color='green', linestyle='--', label='Пешеходные дорожки'),
        plt.Line2D([0], [0], color='orange', linestyle=':', label='Связи зданий'),
        plt.scatter([0], [0], c='red', alpha=0.6, s=100, label='Здания'),
        plt.scatter([0], [0], c='yellow', alpha=0.6, s=100, label='Остановки'),
        plt.scatter([0], [0], c='purple', alpha=0.6, s=100, label='Метро'),
        plt.scatter([0], [0], c='blue', alpha=0.6, s=50, label='Перекрёстки')
    ]
    plt.legend(handles=legend_elements, loc='upper right')

    plt.title("Граф дорожной сети")
    plt.axis('equal')
    plt.grid(True)

    return plt


def get_largest_connected_component(G):
    # Находим все компоненты связности в графе
    connected_components = list(nx.connected_components(G))

    # Находим компонент с максимальным числом узлов
    largest_component = max(connected_components, key=len)

    # Создаём новый граф, содержащий только этот компонент
    largest_subgraph = G.subgraph(largest_component).copy()

    return largest_subgraph

def get_typed_nodes(G, type = "building"):
    nodes = []
    # Проходим по всем узлам графа
    for node, attr in G.nodes(data=True):
        if attr.get('building_type') == type:
            nodes.append(node)
    return nodes


def get_graph(buildings, roads):
    G = create_road_network_graph(buildings, roads)
    return get_largest_connected_component(G)


def clean_graph_attributes(G):
    for node, attrs in G.nodes(data=True):
        for key, value in attrs.items():
            if value is None:
                attrs[key] = ""  # или замените на другое значение, например "unknown"

    for u, v, attrs in G.edges(data=True):
        for key, value in attrs.items():
            if value is None:
                attrs[key] = ""  # или замените на другое значение, например "unknown"

    return G

# Пример использования
if __name__ == "__main__":
    # Загрузка данных из файлов
    with open('graph_geojson/buildings.geojson', 'r', encoding='utf-8') as f:
        buildings_data = json.load(f)

    with open('graph_geojson/roads.geojson', 'r', encoding='utf-8') as f:
        roads_data = json.load(f)

    # Создание графа и получение информации о зданиях
    G = create_road_network_graph(buildings_data, roads_data)
    G = get_largest_connected_component(G)
    G = clean_graph_attributes(G)
    # simplify_graph(G)
    # Сохранение информации о зданиях в JSON

    # Визуализация графа
    # plt = visualize_graph(G)
    # plt.show()

    # print(G.nodes(data=True))
    # print(G.nodes.get("b_129").get("node_type"))
    # print(get_typed_nodes(G, "metro"))



    # AStar_GOD.find_alternative_paths(G, AStar_GOD.heuristic_func, start_node, goal_node)

