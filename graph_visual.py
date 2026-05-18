import networkx as nx
import plotly.graph_objects as go

def plot_network_with_shortest_path(G: nx.Graph, layout: str, color_by: str, shortest_path=None) -> go.Figure:
    """
    Fungsi visualisasi graph menggunakan Plotly, mendukung highlight Shortest Path 
    dan menampilkan bobot (weight) pada edge jika tersedia.
    """
    # 1. Alokasi Algoritma Layout Posisi
    layout_funcs = {
        "Spring": nx.spring_layout,
        "Circular": nx.circular_layout,
        "Kamada-Kawai": nx.kamada_kawai_layout,
        "Spectral": nx.spectral_layout,
    }
    pos = layout_funcs.get(layout, nx.spring_layout)(G, seed=42)

    # 2. Logika Pewarnaan Node Berdasarkan Centrality / Pilihan User
    if color_by == "Degree":
        degrees = dict(G.degree())
        max_deg = max(degrees.values()) if degrees else 1
        node_colors = [degrees[n] / max_deg for n in G.nodes()]
    elif color_by == "Betweenness":
        bc = nx.betweenness_centrality(G)
        node_colors = [bc[n] for n in G.nodes()]
    else:
        node_colors = [0.5] * G.number_of_nodes()

    # Overwrite warna node jika masuk dalam Shortest Path
    if shortest_path:
        # 1.0 mewakili ujung atas warna (di colorscale kita atur jadi warna kontras, misal merah)
        node_colors = [1.0 if n in shortest_path else node_colors[i] for i, n in enumerate(G.nodes())]

    # 3. Logika Pembuatan Edges (Garis & Bobot)
    # Membuat set pasang node dalam shortest path untuk pencarian instan O(1)
    path_edges = set()
    if shortest_path:
        for i in range(len(shortest_path) - 1):
            path_edges.add((shortest_path[i], shortest_path[i+1]))
            path_edges.add((shortest_path[i+1], shortest_path[i]))

    # Kita pecah menjadi dua trace agar ketebalan & warna garis terpendek bisa dibedakan
    edge_x, edge_y = [], []
    sp_edge_x, sp_edge_y = [], []
    
    # Untuk menyimpan teks posisi bobot di tengah garis (Edge Labels)
    edge_label_x, edge_label_y, edge_label_text = [], [], []

    for u, v, data in G.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        
        # Cek apakah edge dilewati shortest path
        if (u, v) in path_edges:
            sp_edge_x += [x0, x1, None]
            sp_edge_y += [y0, y1, None]
        else:
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]
            
        # Ambil bobot (weight) jika ada untuk dijadikan label di tengah garis
        if 'weight' in data:
            edge_label_x.append((x0 + x1) / 2)
            edge_label_y.append((y0 + y1) / 2)
            edge_label_text.append(str(data['weight']))

    # Trace 1: Edge Standar
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        mode="lines",
        line=dict(width=1.0, color="rgba(0,245,196,0.15)"),
        hoverinfo="none",
    )

    # Trace 2: Edge Shortest Path (Di-highlight lebih tebal)
    sp_edge_trace = go.Scatter(
        x=sp_edge_x, y=sp_edge_y,
        mode="lines",
        line=dict(width=3.5, color="#ff6b6b"),  # Warna merah kontras matching dengan tema neon
        hoverinfo="none",
    )
    
    # Trace 3: Label Bobot Edge (Menggunakan mode markers dengan opacity 0 agar hanya teks yang terlihat)
    edge_label_trace = go.Scatter(
        x=edge_label_x, y=edge_label_y,
        mode="markers+text",
        text=edge_label_text,
        textposition="middle center",
        textfont=dict(size=9, color="#00f5c4", family="Space Mono"),
        marker=dict(opacity=0),
        hoverinfo="none"
    )

    # 4. Logika Pembuatan Nodes
    node_x = [pos[n][0] for n in G.nodes()]
    node_y = [pos[n][1] for n in G.nodes()]
    node_text = [f"Node {n}<br>Degree: {G.degree(n)}" for n in G.nodes()]
    degrees_list = [G.degree(n) for n in G.nodes()]

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers",
        hoverinfo="text",
        text=node_text,
        marker=dict(
            showscale=True,
            colorscale=[[0, "#7c5cfc"], [0.5, "#00f5c4"], [1, "#ff6b6b"]], # 1.0 otomatis jadi merah
            color=node_colors,
            size=[8 + d * 2 for d in degrees_list],
            colorbar=dict(
                thickness=12,
                title=dict(text=color_by, font=dict(color="#6b7280", size=11)),
                tickfont=dict(color="#6b7280", size=9),
                bgcolor="rgba(0,0,0,0)",
                bordercolor="rgba(0,245,196,0.2)",
            ),
            line=dict(width=1, color="rgba(0,245,196,0.4)"),
        ),
    )

    # 5. Gabungkan semua ke objek Figure Plotly
    fig = go.Figure(
        data=[edge_trace, sp_edge_trace, edge_label_trace, node_trace],
        layout=go.Layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(17,24,39,0.95)",
            showlegend=False,
            hovermode="closest",
            margin=dict(b=10, l=10, r=10, t=10),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            font=dict(family="Space Mono, monospace", color="#6b7280"),
        ),
    )
    return fig