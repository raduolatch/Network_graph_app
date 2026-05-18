import matplotlib.pyplot as plt
import networkx as nx

def draw_network_graph(G, shortest_path=None, node_color="#3498db", edge_color="#bdc3c7", highlight_color="#e74c3c"):
    """
    Fungsi untuk menggambar network graph dengan NetworkX dan Matplotlib.
    
    Parameters:
    - G (nx.Graph): Objek graph dari NetworkX.
    - shortest_path (list): List of nodes yang membentuk jalur terpendek (opsional).
    - node_color (str): Warna default untuk node.
    - edge_color (str): Warna default untuk edge.
    - highlight_color (str): Warna untuk highlight node/edge pada shortest path.
    
    Returns:
    - fig (matplotlib.figure.Figure): Objek figure untuk ditampilkan di Streamlit.
    """
    # 1. Mengatur ukuran figure
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # 2. Mengatur posisi graph agar rapi (menggunakan Spring Layout)
    # k mengatur jarak antar node, seed memastikan posisi konsisten setiap di-render
    pos = nx.spring_layout(G, k=0.5, seed=42)
    
    # 3. Menentukan warna node berdasarkan shortest path
    node_colors = []
    for node in G.nodes():
        if shortest_path and node in shortest_path:
            node_colors.append(highlight_color)
        else:
            node_colors.append(node_color)
            
    # 4. Menentukan warna dan ketebalan edge berdasarkan shortest path
    edge_colors = []
    edge_widths = []
    
    # Buat set pasangan node dalam shortest path untuk pencarian yang cepat (dua arah)
    path_edges = set()
    if shortest_path:
        for i in range(len(shortest_path) - 1):
            u, v = shortest_path[i], shortest_path[i+1]
            path_edges.add((u, v))
            path_edges.add((v, u)) # Antisipasi jika graph tidak berarah
            
    for u, v in G.edges():
        if (u, v) in path_edges:
            edge_colors.append(highlight_color)
            edge_widths.append(3.0)  # Lebih tebal untuk highlight
        else:
            edge_colors.append(edge_color)
            edge_widths.append(1.5)  # Ketebalan standar

    # 5. Menggambar Node dan Edge
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=600, ax=ax)
    nx.draw_networkx_edges(G, pos, edge_color=edge_colors, width=edge_widths, ax=ax)
    
    # 6. Menampilkan Label Node
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold", font_color="white", ax=ax)
    
    # 7. Menampilkan Bobot Edge (Weight)
    # Mengambil attribute 'weight' dari setiap edge jika ada
    edge_labels = nx.get_edge_attributes(G, 'weight')
    if edge_labels:
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=9, ax=ax)
        
    # Menghilangkan axis Matplotlib agar tampilan bersih
    ax.axis('off')
    plt.tight_layout()
    
    return fig