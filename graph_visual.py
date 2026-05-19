import networkx as nx
import plotly.graph_objects as go


def plot_network_with_shortest_path(
    G: nx.Graph,
    layout: str,
    color_by: str,
    shortest_path=None
) -> go.Figure:
    """
    Visualisasi graph menggunakan Plotly.
    Mendukung:
    - node dan edge
    - label bobot edge
    - warna node berdasarkan degree / betweenness / uniform
    - highlight shortest path
    """

    # Layout graph
    if layout == "Spring":
        pos = nx.spring_layout(G, seed=42)
    elif layout == "Circular":
        pos = nx.circular_layout(G)
    elif layout == "Kamada-Kawai":
        pos = nx.kamada_kawai_layout(G)
    elif layout == "Spectral":
        pos = nx.spectral_layout(G)
    else:
        pos = nx.spring_layout(G, seed=42)

    # Warna node
    if color_by == "Degree":
        degrees = dict(G.degree())
        max_deg = max(degrees.values()) if degrees else 1
        node_colors = [
            degrees[node] / max_deg if max_deg != 0 else 0.5
            for node in G.nodes()
        ]

    elif color_by == "Betweenness":
        try:
            bc = nx.betweenness_centrality(G, weight="weight")
            node_colors = [bc[node] for node in G.nodes()]
        except Exception:
            node_colors = [0.5] * G.number_of_nodes()

    else:
        node_colors = [0.5] * G.number_of_nodes()

    # Highlight node yang masuk shortest path
    if shortest_path:
        node_colors = [
            1.0 if node in shortest_path else node_colors[index]
            for index, node in enumerate(G.nodes())
        ]

    # Buat edge shortest path
    path_edges = set()

    if shortest_path:
        for i in range(len(shortest_path) - 1):
            u = shortest_path[i]
            v = shortest_path[i + 1]

            path_edges.add((u, v))

            # Kalau graph tidak berarah, tambahkan pasangan kebalikannya
            if not G.is_directed():
                path_edges.add((v, u))

    edge_x = []
    edge_y = []

    sp_edge_x = []
    sp_edge_y = []

    edge_label_x = []
    edge_label_y = []
    edge_label_text = []

    # Edge biasa dan edge shortest path
    for u, v, data in G.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]

        if (u, v) in path_edges:
            sp_edge_x += [x0, x1, None]
            sp_edge_y += [y0, y1, None]
        else:
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]

        weight = data.get("weight", 1)

        edge_label_x.append((x0 + x1) / 2)
        edge_label_y.append((y0 + y1) / 2)
        edge_label_text.append(str(weight))

    # Trace edge biasa
    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines",
        line=dict(
            width=1.0,
            color="rgba(0,245,196,0.15)"
        ),
        hoverinfo="none",
    )

    # Trace edge shortest path
    sp_edge_trace = go.Scatter(
        x=sp_edge_x,
        y=sp_edge_y,
        mode="lines",
        line=dict(
            width=4,
            color="#ff6b6b"
        ),
        hoverinfo="none",
    )

    # Trace label bobot edge
    edge_label_trace = go.Scatter(
        x=edge_label_x,
        y=edge_label_y,
        mode="markers+text",
        text=edge_label_text,
        textposition="middle center",
        textfont=dict(
            size=9,
            color="#00f5c4",
            family="Space Mono"
        ),
        marker=dict(opacity=0),
        hoverinfo="none",
    )

    # Node
    node_x = [pos[node][0] for node in G.nodes()]
    node_y = [pos[node][1] for node in G.nodes()]

    node_text = [
        f"Node {node}<br>Degree: {G.degree(node)}"
        for node in G.nodes()
    ]

    degrees_list = [G.degree(node) for node in G.nodes()]

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        hoverinfo="text",
        text=node_text,
        marker=dict(
            showscale=True,
            colorscale=[
                [0, "#7c5cfc"],
                [0.5, "#00f5c4"],
                [1, "#ff6b6b"]
            ],
            color=node_colors,
            size=[10 + degree * 2 for degree in degrees_list],
            colorbar=dict(
                thickness=12,
                title=dict(
                    text=color_by,
                    font=dict(
                        color="#6b7280",
                        size=11
                    )
                ),
                tickfont=dict(
                    color="#6b7280",
                    size=9
                ),
                bgcolor="rgba(0,0,0,0)",
                bordercolor="rgba(0,245,196,0.2)",
            ),
            line=dict(
                width=1,
                color="rgba(0,245,196,0.4)"
            ),
        ),
    )

    fig = go.Figure(
        data=[
            edge_trace,
            sp_edge_trace,
            edge_label_trace,
            node_trace
        ],
        layout=go.Layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(17,24,39,0.95)",
            showlegend=False,
            hovermode="closest",
            margin=dict(
                b=10,
                l=10,
                r=10,
                t=10
            ),
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False
            ),
            font=dict(
                family="Space Mono, monospace",
                color="#6b7280"
            ),
        ),
    )

    return fig