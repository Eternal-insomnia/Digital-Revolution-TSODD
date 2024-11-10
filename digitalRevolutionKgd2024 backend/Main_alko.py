import random
import json
import pickle
from collections import Counter
import networkx as nx
import Graph
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

import AStar_GOD as Astar


def assign_choice():
    choices = ['school', 'sad', 'metro', 'ot', 'skip', 'default']
    probabilities = [0.05, 0.05, 0.05, 0.05, 0.35, 0.45]
    return random.choices(choices, probabilities)[0]


def choose_route():
    # Генерация случайного числа от 0 до 1
    rand_value = random.random()
    if rand_value < 0.7:
        return 1  # 70% вероятность — по 1 маршруту
    elif rand_value < 0.9:
        return 2  # 20% вероятность — по 2 маршруту
    else:
        return 3  # 10% вероятность — по 3 маршруту


def process_building(G, root_building, population_data):
    print(f"Обработка здания {root_building}" )
    final_map = Counter()
    house_id = root_building  # Получить из ноды значение HouseId TODO
    schools = Graph.get_typed_nodes(G, "school")
    nearest_school, tmp = nearest_object(G, root_building, schools)
    school_routes = Astar.find_alternative_paths(G, root_building, nearest_school)

    # Получить список детсадов
    sads = Graph.get_typed_nodes(G, "sad")
    nearest_sad, tmp = nearest_object(G, root_building, sads)
    sad_routes = Astar.find_alternative_paths(G, root_building, nearest_sad)

    # Получить список остановок
    oTs = Graph.get_typed_nodes(G, "ot")
    nearest_oT, tmp = nearest_object(G, root_building, oTs)
    oT_routes = Astar.find_alternative_paths(G, root_building, nearest_oT)

    # Получить список входов в метро
    metros = Graph.get_typed_nodes(G, "metro")
    nearest_metro, distance = nearest_object(G, root_building, metros)
    metro_routes = Astar.find_alternative_paths(G, root_building, nearest_metro)

    population = population_data.get(str(house_id), 0)

    for _ in range(population):
        my_map = {}
        if random.random() < 0.3:
            continue
        choice = assign_choice()
        if choice == 'skip':
            continue  # Пропускаем текущую итерацию

        elif choice == 'school':
            my_map = add_increment_for_edges(G, root_building, nearest_school, school_routes)

        elif choice == 'sad':
            my_map = add_increment_for_edges(G, root_building, nearest_sad, sad_routes)

        elif choice == 'metro':
            my_map = add_increment_for_edges(G, root_building, nearest_metro, metro_routes)

        elif choice == 'ot':
            my_map = add_increment_for_edges(G, root_building, nearest_oT, oT_routes)

        elif choice == 'default':
            if distance < 1000:
                default_choice = "metro"
            else:
                default_choice = "ot"
            fin_ans = 0
            if default_choice == "metro":
                fin_ans = 1 if random.random() < 0.9 else 2
            else:
                fin_ans = 1 if random.random() < 0.1 else 2

            if fin_ans == 1:
                my_map = add_increment_for_edges(G, root_building, nearest_metro, metro_routes)
            else:
                my_map = add_increment_for_edges(G, root_building, nearest_oT, oT_routes)

        final_map += Counter(my_map)

    return final_map


def process_buildings(G, root_buildings):
    with open('population_data.json', 'r') as file:
        population_data = json.load(file)

    # Создаем словарь для хранения общего счётчика
    final_map = Counter()

    # Устанавливаем количество потоков
    with ThreadPoolExecutor(max_workers=12) as executor:
        # Запускаем выполнение process_building для каждого root_building параллельно
        future_to_building = {executor.submit(process_building, G, b, population_data): b for b in root_buildings}

        # Собираем результаты
        for future in as_completed(future_to_building):
            result = future.result()
            final_map += result  # Суммируем результат в общий счётчик

    # Сохраняем результат
    with open("trafic.json", "w", encoding="utf-8") as file:
        json.dump(dict(final_map), file, ensure_ascii=False, indent=4)


def add_increment_for_edges(G, startId, purpose, routes):
    route = choose_route()
    if route == 1:
        cur_route = routes[0]

    elif route == 2:
        cur_route = routes[1]
    else:
        cur_route = routes[2]
    previous_node = "Init"
    answer = {}
    for node in cur_route:
        if previous_node == "Init":
            previous_node = node
            continue
        else:
            edge = G[previous_node][node]
            cur_id = edge.get("id")
            if cur_id in answer:
                answer[cur_id] += 1
            else:
                answer[cur_id] = 1
    return answer


def nearest_object(G, startId, objects):
    min_distance = float('inf')
    answer = ""
    for object in objects:
        distance, route = Astar.dijkstra(G, startId, object)
        if distance < min_distance:
            min_distance = distance
            answer = object
    return answer, min_distance

with open("graph.pkl", "rb") as f:
    G = pickle.load(f)
buildings = Graph.get_typed_nodes(G)
process_buildings(G, buildings)