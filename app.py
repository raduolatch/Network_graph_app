"""
Network Graph Analyzer — Main UI
Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
import plotly.graph_objects as go
import random
from pathlib import Path

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Network Graph Analyzer",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── INJECT CSS ──────────────────────────────────────────────────────────────
def load_css(path: str):
    with open(path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("style.css")



# ─── HELPER: RENDER METRIC CARD ──────────────────────────────────────────────
def metric_card(value, label, delta=None):
    delta_html = f'<div class="metric-delta">▲ {delta}</div>' if delta else ""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


# ─── HELPER: GENERATE RANDOM GRAPH ───────────────────────────────────────────
def generate_graph(n_nodes: int, n_edges: int, graph_type: str) -> nx.Graph:
    if graph_type == "Random (Erdős–Rényi)":
        p = (2 * n_edges) / (n_nodes * (n_nodes - 1)) if n_nodes > 1 else 0
        G = nx.erdos_renyi_graph(n_nodes, p, seed=42)
    elif graph_type == "Scale-Free (Barabási–Albert)":
        m = max(1, n_edges // n_nodes)
        G = nx.barabasi_albert_graph(n_nodes, m, seed=42)
    elif graph_type == "Small-World (Watts–Strogatz)":
        k = max(2, min(n_nodes - 1, n_edges // n_nodes * 2))
        G = nx.watts_strogatz_graph(n_nodes, k, 0.3, seed=42)
    else:
        G = nx.complete_graph(n_nodes)
    return G


# ─── HELPER: PLOTLY NETWORK VISUALIZATION ─────────────────────────────────────
def plot_network(G: nx.Graph, layout: str, color_by: str) -> go.Figure:
    # Layout
    layout_funcs = {
        "Spring": nx.spring_layout,
        "Circular": nx.circular_layout,
        "Kamada-Kawai": nx.kamada_kawai_layout,
        "Spectral": nx.spectral_layout,
    }
    pos = layout_funcs.get(layout, nx.spring_layout)(G, seed=42)

    # Node colors
    if color_by == "Degree":
        degrees = dict(G.degree())
        max_deg = max(degrees.values()) if degrees else 1
        node_colors = [degrees[n] / max_deg for n in G.nodes()]
    elif color_by == "Betweenness":
        bc = nx.betweenness_centrality(G)
        node_colors = [bc[n] for n in G.nodes()]
    else:
        node_colors = [0.5] * G.number_of_nodes()

    # Edges
    edge_x, edge_y = [], []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        mode="lines",
        line=dict(width=0.8, color="rgba(0,245,196,0.18)"),
        hoverinfo="none",
    )

    # Nodes
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
            colorscale=[[0, "#7c5cfc"], [0.5, "#00f5c4"], [1, "#ff6b6b"]],
            color=node_colors,
            size=[6 + d * 2 for d in degrees_list],
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

    fig = go.Figure(
        data=[edge_trace, node_trace],
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


# ═════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.image("logo.png", width=80)  # sesuaikan nama file & ukurannya
    st.markdown('<div class="sidebar-logo-text">Network Graph Analyzer</div>', unsafe_allow_html=True)

    # ── Graph Source ──────────────────────────────────────────────────────────
    st.markdown('<div class="sidebar-section">// Data Source</div>', unsafe_allow_html=True)
    data_source = st.selectbox(
        "Input Type",
        ["Generate Random Graph", "Upload Edge List (.csv)", "Paste Edge Data"],
        label_visibility="collapsed",
    )

    uploaded_file = None
    pasted_data = ""

    if data_source == "Upload Edge List (.csv)":
        uploaded_file = st.file_uploader(
            "Upload CSV (columns: source, target)",
            type=["csv"],
            label_visibility="collapsed",
        )
    elif data_source == "Paste Edge Data":
        pasted_data = st.text_area(
            "Paste edges (source,target per line)",
            placeholder="0,1\n1,2\n2,3\n0,3",
            height=120,
            label_visibility="collapsed",
        )

    # ── Graph Config ──────────────────────────────────────────────────────────
    st.markdown('<div class="sidebar-section">// Graph Config</div>', unsafe_allow_html=True)

    if data_source == "Generate Random Graph":
        graph_type = st.selectbox(
            "Graph Model",
            ["Random (Erdős–Rényi)", "Scale-Free (Barabási–Albert)", "Small-World (Watts–Strogatz)", "Complete"],
        )
        n_nodes = st.slider("Nodes", 10, 300, 50, step=10)
        n_edges = st.slider("Edges", 10, 800, 80, step=10)
    else:
        graph_type = "Custom"
        n_nodes, n_edges = 0, 0

    directed = st.toggle("Directed Graph", value=False)

    # ── Visualization ─────────────────────────────────────────────────────────
    st.markdown('<div class="sidebar-section">// Visualization</div>', unsafe_allow_html=True)
    layout_algo = st.selectbox("Layout Algorithm", ["Spring", "Circular", "Kamada-Kawai", "Spectral"])
    color_by = st.selectbox("Color Nodes By", ["Degree", "Betweenness", "Uniform"])

    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("⚡  Analyze Graph", use_container_width=True)

    # ── Info ──────────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.65rem; color:#4b5563; font-family:'Space Mono',monospace; line-height:1.8;">
        NGA v1.0.0<br>
        Built with Streamlit + NetworkX<br>
        © 2025 Your Name
    </div>
    """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
#  MAIN CONTENT
# ═════════════════════════════════════════════════════════════════════════════

# ── Header ────────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.image("logo.png", width=60)
with col_title:
    st.markdown("""
    <div>
        <div class="nga-title">Network Graph Analyzer</div>
        <div class="nga-subtitle">// TOPOLOGY · CENTRALITY · PATH ANALYSIS</div>
    </div>
    """, unsafe_allow_html=True)

# ── Build Graph ───────────────────────────────────────────────────────────────
G = None

if run_btn or "graph" in st.session_state:
    with st.spinner("Building graph..."):
        if data_source == "Generate Random Graph":
            G = generate_graph(n_nodes, n_edges, graph_type)
            st.session_state["graph"] = G
            st.session_state["graph_label"] = f"{graph_type} · {n_nodes}N · {G.number_of_edges()}E"

        elif data_source == "Upload Edge List (.csv)" and uploaded_file:
            df = pd.read_csv(uploaded_file)
            G = nx.from_pandas_edgelist(df, source=df.columns[0], target=df.columns[1],
                                        create_using=nx.DiGraph() if directed else nx.Graph())
            st.session_state["graph"] = G
            st.session_state["graph_label"] = f"Uploaded · {G.number_of_nodes()}N · {G.number_of_edges()}E"

        elif data_source == "Paste Edge Data" and pasted_data.strip():
            edges = [line.strip().split(",") for line in pasted_data.strip().splitlines() if "," in line]
            G = nx.DiGraph() if directed else nx.Graph()
            G.add_edges_from([(e[0].strip(), e[1].strip()) for e in edges])
            st.session_state["graph"] = G
            st.session_state["graph_label"] = f"Pasted · {G.number_of_nodes()}N · {G.number_of_edges()}E"

        else:
            if "graph" in st.session_state:
                G = st.session_state["graph"]

elif "graph" in st.session_state:
    G = st.session_state["graph"]


# ── No Graph Yet ──────────────────────────────────────────────────────────────
if G is None:
    st.markdown("""
    <div style="
        text-align:center; padding:5rem 2rem;
        background:rgba(17,24,39,0.6); border-radius:20px;
        border:1px dashed rgba(0,245,196,0.2);
        margin-top:1rem;
    ">
        <div style="font-size:3.5rem; margin-bottom:1rem;">🕸️</div>
        <div style="font-size:1.1rem; font-weight:700; color:#e8eaf0; margin-bottom:0.5rem;">
            No Graph Loaded
        </div>
        <div style="font-size:0.8rem; color:#6b7280; font-family:'Space Mono',monospace;">
            Configure your graph in the sidebar, then click <strong style="color:#00f5c4;">⚡ Analyze Graph</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ── Compute Stats ─────────────────────────────────────────────────────────────
n = G.number_of_nodes()
e = G.number_of_edges()
density = round(nx.density(G), 4)
G_undir = G.to_undirected() if directed else G
components = nx.number_connected_components(G_undir)
avg_clustering = round(nx.average_clustering(G_undir), 4)
degrees = dict(G.degree())
avg_degree = round(np.mean(list(degrees.values())), 2)
try:
    avg_path = round(nx.average_shortest_path_length(G_undir), 3) if nx.is_connected(G_undir) else "N/A (disconnected)"
except Exception:
    avg_path = "N/A"

# Badge
is_connected = nx.is_connected(G_undir)
conn_badge = '<span class="badge badge-green">CONNECTED</span>' if is_connected else '<span class="badge badge-red">DISCONNECTED</span>'
dir_badge = '<span class="badge badge-purple">DIRECTED</span>' if directed else '<span class="badge badge-green">UNDIRECTED</span>'
label = st.session_state.get("graph_label", "")

st.markdown(f"""
<div style="display:flex; align-items:center; gap:10px; margin-bottom:1.2rem; flex-wrap:wrap;">
    <span style="font-family:'Space Mono',monospace; font-size:0.8rem; color:#6b7280;">{label}</span>
    {conn_badge}
    {dir_badge}
</div>
""", unsafe_allow_html=True)

# ── Metric Row ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">// Graph Metrics</div>', unsafe_allow_html=True)
c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1: metric_card(n, "Nodes")
with c2: metric_card(e, "Edges")
with c3: metric_card(density, "Density")
with c4: metric_card(avg_degree, "Avg Degree")
with c5: metric_card(avg_clustering, "Clustering")
with c6: metric_card(components, "Components")

st.markdown("<br>", unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📡  Graph View", "📊  Centrality", "🔍  Node Explorer", "📋  Data"])

# ─── TAB 1: Graph Visualization ───────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-label">// Network Visualization</div>', unsafe_allow_html=True)
    fig = plot_network(G, layout_algo, color_by)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Avg path & diameter
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"""
        <div class="nga-panel">
            <div class="nga-panel-title">📏 Avg Shortest Path</div>
            <div style="font-family:'Space Mono',monospace; font-size:1.5rem; color:#00f5c4;">{avg_path}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_b:
        try:
            diam = nx.diameter(G_undir) if is_connected else "N/A"
        except Exception:
            diam = "N/A"
        st.markdown(f"""
        <div class="nga-panel">
            <div class="nga-panel-title">📐 Diameter</div>
            <div style="font-family:'Space Mono',monospace; font-size:1.5rem; color:#7c5cfc;">{diam}</div>
        </div>
        """, unsafe_allow_html=True)

# ─── TAB 2: Centrality ────────────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-label">// Centrality Analysis</div>', unsafe_allow_html=True)

    with st.spinner("Computing centrality..."):
        deg_centrality = nx.degree_centrality(G)
        try:
            between_centrality = nx.betweenness_centrality(G, normalized=True)
        except Exception:
            between_centrality = {n: 0 for n in G.nodes()}
        try:
            close_centrality = nx.closeness_centrality(G)
        except Exception:
            close_centrality = {n: 0 for n in G.nodes()}
        try:
            eigen_centrality = nx.eigenvector_centrality(G, max_iter=500)
        except Exception:
            eigen_centrality = {n: 0 for n in G.nodes()}

    cent_df = pd.DataFrame({
        "Node": list(G.nodes()),
        "Degree": [round(deg_centrality[n], 4) for n in G.nodes()],
        "Betweenness": [round(between_centrality[n], 4) for n in G.nodes()],
        "Closeness": [round(close_centrality[n], 4) for n in G.nodes()],
        "Eigenvector": [round(eigen_centrality[n], 4) for n in G.nodes()],
    }).sort_values("Betweenness", ascending=False).reset_index(drop=True)

    # Top-5 influential nodes
    top5 = cent_df.head(5)
    st.markdown("**🏆 Top 5 Most Influential Nodes (by Betweenness)**")
    t_cols = st.columns(5)
    for i, (_, row) in enumerate(top5.iterrows()):
        with t_cols[i]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="font-size:1.2rem;">#{i+1}</div>
                <div class="metric-label">Node {row['Node']}</div>
                <div class="metric-delta">B: {row['Betweenness']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        fig_deg = go.Figure(go.Bar(
            x=cent_df["Node"].astype(str).tolist()[:30],
            y=cent_df["Degree"].tolist()[:30],
            marker=dict(color=cent_df["Degree"].tolist()[:30], colorscale=[[0, "#7c5cfc"], [1, "#00f5c4"]]),
        ))
        fig_deg.update_layout(
            title=dict(text="Degree Centrality (Top 30)", font=dict(color="#e8eaf0", size=13, family="Space Mono")),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(17,24,39,0.95)",
            xaxis=dict(showticklabels=False, gridcolor="rgba(107,114,128,0.1)"),
            yaxis=dict(gridcolor="rgba(107,114,128,0.1)", color="#6b7280"),
            margin=dict(l=10, r=10, t=40, b=10),
        )
        st.plotly_chart(fig_deg, use_container_width=True, config={"displayModeBar": False})

    with col_chart2:
        fig_bet = go.Figure(go.Bar(
            x=cent_df["Node"].astype(str).tolist()[:30],
            y=cent_df["Betweenness"].tolist()[:30],
            marker=dict(color=cent_df["Betweenness"].tolist()[:30], colorscale=[[0, "#ff6b6b"], [1, "#00f5c4"]]),
        ))
        fig_bet.update_layout(
            title=dict(text="Betweenness Centrality (Top 30)", font=dict(color="#e8eaf0", size=13, family="Space Mono")),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(17,24,39,0.95)",
            xaxis=dict(showticklabels=False, gridcolor="rgba(107,114,128,0.1)"),
            yaxis=dict(gridcolor="rgba(107,114,128,0.1)", color="#6b7280"),
            margin=dict(l=10, r=10, t=40, b=10),
        )
        st.plotly_chart(fig_bet, use_container_width=True, config={"displayModeBar": False})

    st.dataframe(cent_df, use_container_width=True, height=280)

# ─── TAB 3: Node Explorer ─────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-label">// Node Explorer</div>', unsafe_allow_html=True)

    node_list = list(G.nodes())
    selected_node = st.selectbox("Select a Node", node_list, key="node_sel")

    if selected_node is not None:
        neighbors = list(G.neighbors(selected_node))
        deg = G.degree(selected_node)
        bc_val = round(nx.betweenness_centrality(G).get(selected_node, 0), 4)
        cc_val = round(nx.closeness_centrality(G).get(selected_node, 0), 4)

        n1, n2, n3, n4 = st.columns(4)
        with n1: metric_card(deg, "Degree")
        with n2: metric_card(len(neighbors), "Neighbors")
        with n3: metric_card(bc_val, "Betweenness")
        with n4: metric_card(cc_val, "Closeness")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"**Neighbors of Node `{selected_node}`:**")
        if neighbors:
            neighbor_str = " · ".join([f"`{nb}`" for nb in neighbors[:50]])
            st.markdown(f'<div style="font-family:\'Space Mono\',monospace; font-size:0.8rem; color:#00f5c4; line-height:2;">{neighbor_str}</div>', unsafe_allow_html=True)
        else:
            st.info("This node has no neighbors (isolated node).")

        # Ego graph visualization
        if deg > 0:
            with st.expander("🔭 Ego Graph (1-hop neighborhood)"):
                ego = nx.ego_graph(G, selected_node, radius=1)
                ego_pos = nx.spring_layout(ego, seed=42)
                ex, ey = [], []
                for u, v in ego.edges():
                    x0, y0 = ego_pos[u]; x1, y1 = ego_pos[v]
                    ex += [x0, x1, None]; ey += [y0, y1, None]
                ego_colors = ["#ff6b6b" if n == selected_node else "#00f5c4" for n in ego.nodes()]
                fig_ego = go.Figure([
                    go.Scatter(x=ex, y=ey, mode="lines", line=dict(width=1, color="rgba(0,245,196,0.2)"), hoverinfo="none"),
                    go.Scatter(
                        x=[ego_pos[n][0] for n in ego.nodes()],
                        y=[ego_pos[n][1] for n in ego.nodes()],
                        mode="markers+text",
                        text=[str(n) for n in ego.nodes()],
                        textposition="top center",
                        textfont=dict(size=9, color="#e8eaf0", family="Space Mono"),
                        marker=dict(size=14, color=ego_colors, line=dict(width=1.5, color="rgba(255,255,255,0.3)")),
                    ),
                ])
                fig_ego.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(17,24,39,0.95)",
                    showlegend=False,
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    margin=dict(l=5, r=5, t=5, b=5),
                    height=300,
                )
                st.plotly_chart(fig_ego, use_container_width=True, config={"displayModeBar": False})

# ─── TAB 4: Data ──────────────────────────────────────────────────────────────
with tab4:
    st.markdown('<div class="section-label">// Raw Graph Data</div>', unsafe_allow_html=True)

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        with st.expander("📋 Edge List", expanded=True):
            edges_df = pd.DataFrame(G.edges(), columns=["Source", "Target"])
            st.dataframe(edges_df, use_container_width=True, height=300)
            csv_edges = edges_df.to_csv(index=False)
            st.download_button("⬇ Download Edges CSV", csv_edges, "edges.csv", "text/csv")

    with col_d2:
        with st.expander("🔢 Degree Distribution", expanded=True):
            deg_df = pd.DataFrame([(n, d) for n, d in G.degree()], columns=["Node", "Degree"])
            deg_df = deg_df.sort_values("Degree", ascending=False).reset_index(drop=True)
            st.dataframe(deg_df, use_container_width=True, height=300)
            csv_deg = deg_df.to_csv(index=False)
            st.download_button("⬇ Download Degree CSV", csv_deg, "degree.csv", "text/csv")

    # Degree distribution histogram
    st.markdown('<div class="section-label" style="margin-top:1rem;">// Degree Distribution Histogram</div>', unsafe_allow_html=True)
    deg_vals = [d for _, d in G.degree()]
    fig_hist = go.Figure(go.Histogram(
        x=deg_vals, nbinsx=30,
        marker=dict(color="#00f5c4", opacity=0.8, line=dict(color="#7c5cfc", width=1)),
    ))
    fig_hist.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(17,24,39,0.95)",
        xaxis=dict(title="Degree", color="#6b7280", gridcolor="rgba(107,114,128,0.1)"),
        yaxis=dict(title="Count", color="#6b7280", gridcolor="rgba(107,114,128,0.1)"),
        margin=dict(l=10, r=10, t=10, b=10),
        bargap=0.05,
        height=250,
    )
    st.plotly_chart(fig_hist, use_container_width=True, config={"displayModeBar": False})
