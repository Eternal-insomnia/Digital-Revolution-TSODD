import networkx as nx
from queue import PriorityQueue


def dijkstra(graph, start, goal, forbidden_nodes=None):
    if forbidden_nodes is None:
        forbidden_nodes = set()
    else:
        forbidden_nodes = set(forbidden_nodes)

    # Инициализация
    distances = {node: float('inf') for node in graph.nodes}
    distances[start] = 0

    pq = PriorityQueue()
    pq.put((0, start))

    predecessors = {node: None for node in graph.nodes}
    visited = set()

    while not pq.empty():
        current_distance, current_node = pq.get()

        if current_node == goal:
            # Восстанавливаем путь
            path = []
            while current_node is not None:
                path.append(current_node)
                current_node = predecessors[current_node]
            path.reverse()
            return distances[goal], path

        if current_node in visited or current_node in forbidden_nodes:
            continue

        visited.add(current_node)

        # Проверяем всех соседей
        for neighbor in graph.neighbors(current_node):
            if neighbor in forbidden_nodes:
                continue

            edge_weight = graph[current_node][neighbor]['weight']
            new_distance = distances[current_node] + edge_weight

            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                pq.put((new_distance, neighbor))
                predecessors[neighbor] = current_node

    return float('inf'), []


def find_alternative_paths(graph, start, goal, num_paths=3):
    paths = []
    forbidden_nodes = set()

    for i in range(num_paths):
        # Ищем кратчайший путь с текущими запрещенными узлами
        distance, path = dijkstra(graph, start, goal, forbidden_nodes)

        if not path:
            # Если путь не найден, пробуем разблокировать узлы
            temp_forbidden = forbidden_nodes.copy()
            found_path = False

            for node in list(forbidden_nodes):
                temp_forbidden.remove(node)
                distance, path = dijkstra(graph, start, goal, temp_forbidden)
                if path:
                    forbidden_nodes = temp_forbidden
                    found_path = True
                    break

            if not found_path:
                break

        if path:
            paths.append(path)
            print(f"Путь{i} - {distance}")
            # Добавляем промежуточные узлы в запрещенные
            forbidden_nodes.update(path[1:-1])

    return paths
