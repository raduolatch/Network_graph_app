import networkx as nx
import pandas as pd


def get_adjacency_matrix(G):
    return nx.to_pandas_adjacency(G, weight="weight")


def get_degree_table(G):
    data = []

    for node, degree in G.degree():
        data.append({
            "Node": node,
            "Degree": degree
        })

    return pd.DataFrame(data)


def check_connected(G):
    if G.number_of_nodes() == 0:
        return False

    if G.is_directed():
        return nx.is_weakly_connected(G)
    else:
        return nx.is_connected(G)


def get_components_count(G):
    if G.number_of_nodes() == 0:
        return 0

    if G.is_directed():
        return nx.number_weakly_connected_components(G)
    else:
        return nx.number_connected_components(G)


def dijkstra_shortest_path(G, source, target):
    try:
        path = nx.shortest_path(G, source=source, target=target, weight="weight")
        distance = nx.shortest_path_length(G, source=source, target=target, weight="weight")

        return {
            "success": True,
            "path": path,
            "distance": distance,
            "message": "Jalur terpendek berhasil ditemukan."
        }

    except nx.NetworkXNoPath:
        return {
            "success": False,
            "path": [],
            "distance": None,
            "message": "Tidak ada jalur antara node tersebut."
        }

    except nx.NodeNotFound:
        return {
            "success": False,
            "path": [],
            "distance": None,
            "message": "Node tidak ditemukan dalam graf."
        }


def bfs_traversal(G, start_node):
    try:
        return list(nx.bfs_tree(G, start_node).nodes())
    except nx.NodeNotFound:
        return []


def dfs_traversal(G, start_node):
    try:
        return list(nx.dfs_preorder_nodes(G, start_node))
    except nx.NodeNotFound:
        return []


def get_graph_summary(G):
    return {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "density": round(nx.density(G), 4),
        "connected": check_connected(G),
        "components": get_components_count(G)
    }