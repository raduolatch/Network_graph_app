"""
Network Graph Analyzer — Main UI
Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
import plotly.graph_objects as go

from database import init_db, save_graph, load_graph, get_all_graphs, log_history, get_history

# Panggil saat aplikasi pertama kali jalan
init_db()

from algorithms import (
    get_adjacency_matrix,
    get_degree_table,
    check_connected,
    dijkstra_shortest_path,
    bfs_traversal,
    dfs_traversal,
)
from graph_visual import plot_network_with_shortest_path

# ── Komponen UI & Helper dari file baru ──────────────────────────────────────
from ui_components import (
    metric_card,
    section_label,
    panel_metric,
    empty_state,
    graph_header,
    top_nodes_strip,
    neighbor_chips,
    sidebar_section,
)
from utils import (
    generate_graph,
    safe_avg_path,
    safe_diameter,
    compute_centrality,
    get_node_centrality,
    validate_edge_input,
    build_graph_from_edges,
    format_number,
    truncate_path_str,
)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Network Graph Analyzer",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_css(path: str):
    with open(path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("style.css")


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image("logo.png", width=80)
    st.markdown(
        '<div class="sidebar-logo-text">Network Graph Analyzer</div>',
        unsafe_allow_html=True,
    )

    sidebar_section("Data Source")

    data_source = st.selectbox(
        "Input Type",
        ["Generate Random Graph", "Upload Edge List (.csv)", "Paste Edge Data"],
        label_visibility="collapsed",
    )

    uploaded_file = None
    pasted_data   = ""

    if data_source == "Upload Edge List (.csv)":
        uploaded_file = st.file_uploader(
            "Upload CSV columns: source, target, weight",
            type=["csv"],
            label_visibility="collapsed",
        )

    elif data_source == "Paste Edge Data":
        pasted_data = st.text_area(
            "Paste edges",
            placeholder="A,B,5\nA,C,2\nC,D,1\nB,D,4",
            height=120,
            label_visibility="collapsed",
        )

    sidebar_section("Graph Config")

    if data_source == "Generate Random Graph":
        graph_type = st.selectbox(
            "Graph Model",
            [
                "Random (Erdős–Rényi)",
                "Scale-Free (Barabási–Albert)",
                "Small-World (Watts–Strogatz)",
                "Complete",
            ],
        )
        n_nodes = st.slider("Nodes", 10, 300, 50, step=10)
        n_edges = st.slider("Edges", 10, 800, 80, step=10)
    else:
        graph_type      = "Custom"
        n_nodes, n_edges = 0, 0

    directed = st.toggle("Directed Graph", value=False)

    sidebar_section("Visualization")
    layout_algo = st.selectbox(
        "Layout Algorithm", ["Spring", "Circular", "Kamada-Kawai", "Spectral"]
    )
    color_by = st.selectbox("Color Nodes By", ["Degree", "Betweenness", "Uniform"])

    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("⚡  Analyze Graph", use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="font-size:0.65rem; color:#4b5563;
                    font-family:'Space Mono',monospace; line-height:1.8;">
            NGA v1.0.0<br>
            Built with Streamlit + NetworkX<br>
            © 2025 Your Name
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────

col_logo, col_title = st.columns([1, 8])

with col_logo:
    st.image("logo.png", width=60)

with col_title:
    st.markdown(
        """
        <div>
            <div class="nga-title">Network Graph Analyzer</div>
            <div class="nga-subtitle">TOPOLOGY · CENTRALITY · PATH ANALYSIS</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# GRAPH BUILDING
# ─────────────────────────────────────────────────────────────────────────────

G = None

if run_btn:
    # Reset centrality cache setiap graph baru di-generate
    st.session_state.pop("centrality_cache", None)
    st.session_state.pop("centrality_key",   None)

    with st.spinner("Building graph..."):

        if data_source == "Generate Random Graph":
            G = generate_graph(n_nodes, n_edges, graph_type)  # bug-fixed dari utils
            if directed:
                G = G.to_directed()
            st.session_state["graph"]       = G
            st.session_state["graph_label"] = (
                f"{graph_type} · {G.number_of_nodes()}N · {G.number_of_edges()}E"
            )

        elif data_source == "Upload Edge List (.csv)" and uploaded_file:
            df         = pd.read_csv(uploaded_file)
            source_col = df.columns[0]
            target_col = df.columns[1]

            if len(df.columns) >= 3:
                weight_col = df.columns[2]
                G = nx.from_pandas_edgelist(
                    df,
                    source=source_col,
                    target=target_col,
                    edge_attr=weight_col,
                    create_using=nx.DiGraph() if directed else nx.Graph(),
                )
                nx.set_edge_attributes(
                    G,
                    {
                        (row[source_col], row[target_col]): float(row[weight_col])
                        for _, row in df.iterrows()
                    },
                    "weight",
                )
            else:
                G = nx.from_pandas_edgelist(
                    df,
                    source=source_col,
                    target=target_col,
                    create_using=nx.DiGraph() if directed else nx.Graph(),
                )
                for u, v in G.edges():
                    G[u][v]["weight"] = 1

            st.session_state["graph"]       = G
            st.session_state["graph_label"] = (
                f"Uploaded · {G.number_of_nodes()}N · {G.number_of_edges()}E"
            )

        elif data_source == "Paste Edge Data" and pasted_data.strip():
            # Bug-fix: sekarang pakai validate_edge_input() agar error per baris terlihat
            edges, errors = validate_edge_input(pasted_data)

            if errors:
                for err in errors:
                    st.sidebar.warning(err)

            if edges:
                G = build_graph_from_edges(edges, directed=directed)
                st.session_state["graph"]       = G
                st.session_state["graph_label"] = (
                    f"Pasted · {G.number_of_nodes()}N · {G.number_of_edges()}E"
                )
            else:
                st.error("Tidak ada edge valid yang bisa di-parse. Cek format input.")

        # Jika run_btn tapi source tidak ada data (misal CSV belum upload),
        # tetap load graph lama dari session agar tidak kosong
        if G is None and "graph" in st.session_state:
            G = st.session_state["graph"]

elif "graph" in st.session_state:
    G = st.session_state["graph"]


# ─────────────────────────────────────────────────────────────────────────────
# EMPTY STATE  →  semua kode di bawah hanya jalan kalau G valid
# ─────────────────────────────────────────────────────────────────────────────

if G is not None:

    # ─────────────────────────────────────────────────────────────────────────
    # GRAPH METRICS (top bar)
    # ─────────────────────────────────────────────────────────────────────────

    n           = G.number_of_nodes()
    e           = G.number_of_edges()
    density     = round(nx.density(G), 4)
    G_undir     = G.to_undirected() if G.is_directed() else G
    components  = nx.number_connected_components(G_undir)
    avg_clust   = round(nx.average_clustering(G_undir), 4)
    degrees     = dict(G.degree())
    avg_degree  = round(np.mean(list(degrees.values())), 2) if degrees else 0
    is_connected = check_connected(G)

    avg_path = safe_avg_path(G, G_undir)
    diam     = safe_diameter(G_undir)

    label = st.session_state.get("graph_label", "")
    graph_header(label, is_connected, G.is_directed())

    section_label("Graph Metrics")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: metric_card(format_number(n), "Nodes")
    with c2: metric_card(format_number(e), "Edges")
    with c3: metric_card(density, "Density")
    with c4: metric_card(avg_degree, "Avg Degree")
    with c5: metric_card(avg_clust, "Clustering")
    with c6: metric_card(components, "Components")

    st.markdown("<br>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # TABS
    # ─────────────────────────────────────────────────────────────────────────

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📡 Graph View",
        "🧭 Shortest Path",
        "📊 Centrality",
        "🔍 Node Explorer",
        "📋 Data",
    ])

    # ── TAB 1 : Graph View ───────────────────────────────────────────────────

    with tab1:
        section_label("Network Visualization")

        fig = plot_network_with_shortest_path(G, layout_algo, color_by)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        col_a, col_b = st.columns(2)
        with col_a:
            panel_metric("📏 Avg Shortest Path", avg_path, color="#00f5c4")
        with col_b:
            panel_metric("📐 Diameter", diam, color="#7c5cfc")

    # ── TAB 2 : Shortest Path ────────────────────────────────────────────────

    with tab2:
        section_label("Shortest Path / Rute Terpendek")

        node_list = list(G.nodes())

        if len(node_list) >= 2:
            col_sp1, col_sp2 = st.columns(2)
            with col_sp1:
                source_node = st.selectbox("Pilih Node Awal",   node_list, key="source_node")
            with col_sp2:
                target_node = st.selectbox("Pilih Node Tujuan", node_list, key="target_node")

            if st.button("Cari Rute Terpendek", use_container_width=True):
                result = dijkstra_shortest_path(G, source_node, target_node)

                if result["success"]:
                    shortest_path = result["path"]
                    st.success("Rute terbaik: " + truncate_path_str(shortest_path))
                    st.info(f"Total jarak / bobot: {result['distance']}")

                    fig_sp = plot_network_with_shortest_path(
                        G, layout_algo, color_by, shortest_path=shortest_path
                    )
                    st.plotly_chart(fig_sp, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.error(result["message"])
        else:
            st.warning("Minimal graph harus memiliki 2 node.")

    # ── TAB 3 : Centrality ───────────────────────────────────────────────────

    with tab3:
        section_label("Centrality Analysis")

        with st.spinner("Computing centrality..."):
            cent_df = compute_centrality(G)

        st.markdown("**🏆 Top 5 Most Influential Nodes by Betweenness**")
        top_nodes_strip(cent_df.head(5))

        st.markdown("<br>", unsafe_allow_html=True)

        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            fig_deg = go.Figure(go.Bar(
                x=cent_df["Node"].astype(str).tolist()[:30],
                y=cent_df["Degree"].tolist()[:30],
                marker=dict(
                    color=cent_df["Degree"].tolist()[:30],
                    colorscale=[[0, "#7c5cfc"], [1, "#00f5c4"]],
                ),
            ))
            fig_deg.update_layout(
                title=dict(text="Degree Centrality", font=dict(color="#e8eaf0", size=13, family="Space Mono")),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(17,24,39,0.95)",
                xaxis=dict(showticklabels=False, gridcolor="rgba(107,114,128,0.1)"),
                yaxis=dict(gridcolor="rgba(107,114,128,0.1)", color="#6b7280"),
                margin=dict(l=10, r=10, t=40, b=10),
            )
            st.plotly_chart(fig_deg, use_container_width=True, config={"displayModeBar": False})

        with col_chart2:
            fig_bet = go.Figure(go.Bar(
                x=cent_df["Node"].astype(str).tolist()[:30],
                y=cent_df["Betweenness"].tolist()[:30],
                marker=dict(
                    color=cent_df["Betweenness"].tolist()[:30],
                    colorscale=[[0, "#ff6b6b"], [1, "#00f5c4"]],
                ),
            ))
            fig_bet.update_layout(
                title=dict(text="Betweenness Centrality", font=dict(color="#e8eaf0", size=13, family="Space Mono")),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(17,24,39,0.95)",
                xaxis=dict(showticklabels=False, gridcolor="rgba(107,114,128,0.1)"),
                yaxis=dict(gridcolor="rgba(107,114,128,0.1)", color="#6b7280"),
                margin=dict(l=10, r=10, t=40, b=10),
            )
            st.plotly_chart(fig_bet, use_container_width=True, config={"displayModeBar": False})

        st.dataframe(cent_df, use_container_width=True, height=280)

    # ── TAB 4 : Node Explorer ────────────────────────────────────────────────

    with tab4:
        section_label("Node Explorer")

        node_list     = list(G.nodes())
        selected_node = st.selectbox("Select a Node", node_list, key="node_sel")

        if selected_node is not None:
            neighbors = list(G.neighbors(selected_node))
            deg       = G.degree(selected_node)

            cent_vals = get_node_centrality(G, selected_node)
            bc_val    = cent_vals["betweenness"]
            cc_val    = cent_vals["closeness"]

            n1, n2, n3, n4 = st.columns(4)
            with n1: metric_card(deg,              "Degree")
            with n2: metric_card(len(neighbors),   "Neighbors")
            with n3: metric_card(bc_val,           "Betweenness")
            with n4: metric_card(cc_val,           "Closeness")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"**Neighbors of Node `{selected_node}`:**")

            neighbor_chips(neighbors)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### Traversal")

            col_bfs, col_dfs = st.columns(2)
            with col_bfs:
                bfs_result = bfs_traversal(G, selected_node)
                st.write("BFS:")
                st.code(truncate_path_str(bfs_result, max_show=30))
            with col_dfs:
                dfs_result = dfs_traversal(G, selected_node)
                st.write("DFS:")
                st.code(truncate_path_str(dfs_result, max_show=30))

    # ── TAB 5 : Data ─────────────────────────────────────────────────────────

    with tab5:
        section_label("Raw Graph Data")

        col_d1, col_d2 = st.columns(2)

        with col_d1:
            with st.expander("📋 Edge List", expanded=True):
                edges_df = pd.DataFrame(
                    [(u, v, data.get("weight", 1)) for u, v, data in G.edges(data=True)],
                    columns=["Source", "Target", "Weight"],
                )
                st.dataframe(edges_df, use_container_width=True, height=300)
                st.download_button(
                    "⬇ Download Edges CSV",
                    edges_df.to_csv(index=False),
                    "edges.csv",
                    "text/csv",
                )

        with col_d2:
            with st.expander("🔢 Degree Distribution", expanded=True):
                deg_df = (
                    get_degree_table(G)
                    .sort_values("Degree", ascending=False)
                    .reset_index(drop=True)
                )
                st.dataframe(deg_df, use_container_width=True, height=300)
                st.download_button(
                    "⬇ Download Degree CSV",
                    deg_df.to_csv(index=False),
                    "degree.csv",
                    "text/csv",
                )

        section_label("Adjacency Matrix", margin_top="1rem")
        adj_matrix = get_adjacency_matrix(G)
        st.dataframe(adj_matrix, use_container_width=True)

        section_label("Degree Distribution Histogram", margin_top="1rem")
        deg_vals = [d for _, d in G.degree()]

        fig_hist = go.Figure(go.Histogram(
            x=deg_vals,
            nbinsx=30,
            marker=dict(
                color="#00f5c4",
                opacity=0.8,
                line=dict(color="#7c5cfc", width=1),
            ),
        ))
        fig_hist.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(17,24,39,0.95)",
            xaxis=dict(title="Degree", color="#6b7280", gridcolor="rgba(107,114,128,0.1)"),
            yaxis=dict(title="Count",  color="#6b7280", gridcolor="rgba(107,114,128,0.1)"),
            margin=dict(l=10, r=10, t=10, b=10),
            bargap=0.05,
            height=250,
        )
        st.plotly_chart(fig_hist, use_container_width=True, config={"displayModeBar": False})

else:
    empty_state()
