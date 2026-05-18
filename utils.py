"""
utils.py
Helper functions untuk Network Graph Analyzer.

Modul ini menangani:
  - generate_graph()        : Pembuatan graph acak berbagai model
  - safe_avg_path()         : Hitung avg shortest path tanpa freeze
  - safe_diameter()         : Hitung diameter graph dengan fallback
  - compute_centrality()    : Hitung semua centrality sekaligus + cache
  - format_number()         : Format angka besar jadi 1.2K / 3.4M
  - truncate_path_str()     : Ubah list path jadi string ringkas
  - validate_edge_input()   : Validasi baris paste / upload CSV

Catatan performa:
  - Fungsi compute_centrality() di-cache via st.session_state agar
    tidak dihitung ulang setiap kali user klik tab / pilih node.
  - safe_avg_path() skip otomatis untuk graph > MAX_PATH_NODES node
    karena O(n² log n) sangat berat untuk graph besar.
"""

import networkx as nx
import numpy as np
import pandas as pd
import streamlit as st
from typing import Optional, Any

# KONSTANTA
# Batas node untuk auto-skip komputasi berat
MAX_PATH_NODES   = 500   # avg_shortest_path & diameter
MAX_EIGEN_NODES  = 2000  # eigenvector centrality

# GRAPH GENERATION
def generate_graph(n_nodes: int, n_edges: int, graph_type: str) -> nx.Graph:
    """
    Buat graph sintetis berdasarkan model yang dipilih.

    Bug-fix dari versi app.py:
      - n_edges di-clamp agar tidak melebihi max edges yang mungkin
        (mencegah overflow di model Complete / Erdős–Rényi).
      - Semua edge diberi atribut weight=1 secara default.

    Args:
        n_nodes    : Jumlah node.
        n_edges    : Jumlah edge yang diinginkan (best-effort).
        graph_type : Nama model graph (string dari selectbox).

    Returns:
        nx.Graph siap pakai.

    Contoh:
        G = generate_graph(50, 80, "Random (Erdős–Rényi)")
    """
    # Clamp n_edges: max teori untuk undirected simple graph = n*(n-1)/2
    max_possible = max(1, n_nodes * (n_nodes - 1) // 2)
    n_edges      = min(n_edges, max_possible)

    if graph_type == "Random (Erdős–Rényi)":
        p = (2 * n_edges) / (n_nodes * (n_nodes - 1)) if n_nodes > 1 else 0
        p = min(p, 1.0)  # pastikan probabilitas tidak > 1
        G = nx.erdos_renyi_graph(n_nodes, p, seed=42)

    elif graph_type == "Scale-Free (Barabási–Albert)":
        m = max(1, min(n_edges // n_nodes, n_nodes - 1))
        G = nx.barabasi_albert_graph(n_nodes, m, seed=42)

    elif graph_type == "Small-World (Watts–Strogatz)":
        k = max(2, min(n_nodes - 1, (n_edges // n_nodes) * 2))
        k = k if k % 2 == 0 else k - 1  # Watts–Strogatz butuh k genap
        k = max(2, k)
        G = nx.watts_strogatz_graph(n_nodes, k, 0.3, seed=42)

    elif graph_type == "Complete":
        # Complete graph: abaikan n_edges (sudah max)
        G = nx.complete_graph(n_nodes)

    else:
        G = nx.erdos_renyi_graph(n_nodes, 0.1, seed=42)

    # Pastikan semua edge punya atribut weight
    for u, v in G.edges():
        G[u][v]["weight"] = 1

    return G

# SAFE COMPUTE — AVG SHORTEST PATH
def safe_avg_path(G: nx.Graph, G_undir: nx.Graph) -> Any:
    """
    Hitung average shortest path length dengan pengaman:
      - Skip jika graph tidak connected (return "N/A").
      - Skip jika node > MAX_PATH_NODES (return "Too large").
      - Tangkap semua exception tanpa crash.

    Bug-fix: versi app.py menghitung ini di top-level setiap rerender,
    yang bisa freeze Streamlit untuk graph besar. Pindahkan ke sini
    dan panggil hanya saat dibutuhkan.

    Args:
        G       : Graph asli (untuk cek directed/undirected).
        G_undir : Versi undirected dari G.

    Returns:
        float | str: Nilai avg path atau string keterangan.
    """
    if not nx.is_connected(G_undir):
        return "N/A"

    if G_undir.number_of_nodes() > MAX_PATH_NODES:
        return "Too large"

    try:
        return round(
            nx.average_shortest_path_length(G_undir, weight="weight"), 3
        )
    except Exception:
        return "N/A"

# SAFE COMPUTE — DIAMETER
def safe_diameter(G_undir: nx.Graph) -> Any:
    """
    Hitung diameter graph dengan pengaman koneksi & ukuran.

    Args:
        G_undir : Graph undirected.

    Returns:
        int | str: Diameter atau string keterangan.
    """
    if not nx.is_connected(G_undir):
        return "N/A"

    if G_undir.number_of_nodes() > MAX_PATH_NODES:
        return "Too large"

    try:
        return nx.diameter(G_undir)
    except Exception:
        return "N/A"


# CENTRALITY — COMPUTE + SESSION CACHE
def compute_centrality(G: nx.Graph) -> pd.DataFrame:
    """
    Hitung degree, betweenness, closeness, dan eigenvector centrality
    sekaligus, lalu kembalikan sebagai DataFrame.

    Cache key: jumlah node + edge + apakah directed.
    Jika graph tidak berubah, kembalikan hasil dari session_state
    tanpa hitung ulang — mencegah lag O(n³) tiap klik tab/node.

    Bug-fix: di app.py tab4, betweenness dihitung ulang setiap kali
    user memilih node (O(n³) per klik). Fungsi ini menyimpannya di
    session_state["centrality_cache"].

    Args:
        G : Graph NetworkX.

    Returns:
        pd.DataFrame dengan kolom: Node, Degree, Betweenness,
        Closeness, Eigenvector.
    """
    cache_key = (G.number_of_nodes(), G.number_of_edges(), G.is_directed())

    if (
        "centrality_cache" in st.session_state
        and st.session_state.get("centrality_key") == cache_key
    ):
        return st.session_state["centrality_cache"]

    # Degree centrality
    deg_c = nx.degree_centrality(G)

    # Betweenness centrality
    try:
        bet_c = nx.betweenness_centrality(G, normalized=True, weight="weight")
    except Exception:
        bet_c = {node: 0.0 for node in G.nodes()}

    # Closeness centrality
    try:
        clo_c = nx.closeness_centrality(G, distance="weight")
    except Exception:
        clo_c = {node: 0.0 for node in G.nodes()}

    # Eigenvector centrality — skip untuk graph sangat besar
    if G.number_of_nodes() <= MAX_EIGEN_NODES:
        try:
            eig_c = nx.eigenvector_centrality(G, max_iter=500, weight="weight")
        except Exception:
            eig_c = {node: 0.0 for node in G.nodes()}
    else:
        eig_c = {node: 0.0 for node in G.nodes()}

    df = pd.DataFrame({
        "Node":        list(G.nodes()),
        "Degree":      [round(deg_c[n], 4) for n in G.nodes()],
        "Betweenness": [round(bet_c[n], 4) for n in G.nodes()],
        "Closeness":   [round(clo_c[n], 4) for n in G.nodes()],
        "Eigenvector": [round(eig_c[n], 4) for n in G.nodes()],
    }).sort_values("Betweenness", ascending=False).reset_index(drop=True)

    # Simpan ke cache
    st.session_state["centrality_cache"] = df
    st.session_state["centrality_key"]   = cache_key

    return df


def get_node_centrality(G: nx.Graph, node) -> dict:
    """
    Ambil nilai centrality untuk satu node dari cache.
    Efisien karena tidak hitung ulang — pakai compute_centrality().

    Args:
        G    : Graph NetworkX.
        node : ID node.

    Returns:
        dict dengan key: betweenness, closeness.
    """
    df  = compute_centrality(G)
    row = df[df["Node"] == node]

    if row.empty:
        return {"betweenness": 0.0, "closeness": 0.0}

    return {
        "betweenness": float(row["Betweenness"].iloc[0]),
        "closeness":   float(row["Closeness"].iloc[0]),
    }

# FORMAT HELPERS
def format_number(n: Any) -> str:
    """
    Format angka besar menjadi singkatan mudah dibaca.

    Args:
        n : Angka (int/float) atau string "N/A" / "Too large".

    Returns:
        str: Angka diformat.

    Contoh:
        format_number(1200)     → "1.2K"
        format_number(3400000)  → "3.4M"
        format_number(42)       → "42"
        format_number("N/A")    → "N/A"
    """
    if not isinstance(n, (int, float)):
        return str(n)

    if abs(n) >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    elif abs(n) >= 1_000:
        return f"{n / 1_000:.1f}K"
    else:
        return str(n)


def truncate_path_str(path: list, max_show: int = 10) -> str:
    """
    Ubah list path node menjadi string "A → B → C ... (N more)".

    Args:
        path     : List node dalam path.
        max_show : Maksimum node yang ditampilkan sebelum ellipsis.

    Returns:
        str: String path yang sudah diformat.

    Contoh:
        truncate_path_str([0, 1, 2, 3, 4, 5], max_show=4)
        → "0 → 1 → 2 → 3 ... (+2 more)"
    """
    if not path:
        return ""

    if len(path) <= max_show:
        return " → ".join(map(str, path))

    shown    = path[:max_show]
    overflow = len(path) - max_show
    return " → ".join(map(str, shown)) + f" ... (+{overflow} more)"


# EDGE INPUT VALIDATION
def validate_edge_input(raw: str) -> tuple[list[tuple], list[str]]:
    """
    Parse dan validasi teks edge yang di-paste user.

    Format yang diterima per baris:
      - "A,B"        → edge tanpa bobot (weight=1)
      - "A,B,5"      → edge dengan bobot 5
      - "A,B,3.14"   → edge dengan bobot float

    Bug-fix: versi app.py tidak memberi feedback baris mana yang gagal
    di-parse, sehingga user tidak tahu ada input yang salah.

    Args:
        raw : String multi-baris dari st.text_area.

    Returns:
        Tuple (edges, errors):
          - edges  : List (source, target, weight) yang valid.
          - errors : List string pesan error per baris bermasalah.

    Contoh:
        edges, errors = validate_edge_input("A,B,5\\nA,C\\nBAD LINE")
        # edges  = [("A","B",5.0), ("A","C",1.0)]
        # errors = ["Line 3: 'BAD LINE' — expected format: source,target[,weight]"]
    """
    edges  = []
    errors = []

    for i, line in enumerate(raw.strip().splitlines(), start=1):
        line = line.strip()
        if not line:
            continue

        parts = [p.strip() for p in line.split(",")]

        if len(parts) == 2:
            source, target = parts
            if not source or not target:
                errors.append(f"Line {i}: '{line}' — source atau target kosong.")
                continue
            edges.append((source, target, 1.0))

        elif len(parts) >= 3:
            source, target = parts[0], parts[1]
            if not source or not target:
                errors.append(f"Line {i}: '{line}' — source atau target kosong.")
                continue
            try:
                weight = float(parts[2])
            except ValueError:
                errors.append(
                    f"Line {i}: '{line}' — bobot '{parts[2]}' bukan angka valid."
                )
                continue
            edges.append((source, target, weight))

        else:
            errors.append(
                f"Line {i}: '{line}' — format tidak valid "
                f"(expected: source,target[,weight])."
            )

    return edges, errors



# GRAPH BUILD FROM VALIDATED EDGES
def build_graph_from_edges(
    edges: list[tuple],
    directed: bool = False,
) -> nx.Graph:
    """
    Buat graph dari list (source, target, weight) yang sudah divalidasi.

    Args:
        edges    : Output dari validate_edge_input().
        directed : True untuk DiGraph.

    Returns:
        nx.Graph atau nx.DiGraph.

    Contoh:
        edges, _ = validate_edge_input(pasted_data)
        G = build_graph_from_edges(edges, directed=False)
    """
    G = nx.DiGraph() if directed else nx.Graph()

    for source, target, weight in edges:
        G.add_edge(source, target, weight=weight)

    return G


# GRAPH SUMMARY
def get_graph_summary(G: nx.Graph) -> dict:
    """
    Ringkasan statistik dasar graph dalam satu dict.

    Args:
        G : Graph NetworkX.

    Returns:
        dict dengan key: nodes, edges, density, directed,
        avg_degree, clustering.

    Contoh:
        summary = get_graph_summary(G)
        print(summary["avg_degree"])
    """
    degrees = dict(G.degree())

    return {
        "nodes":       G.number_of_nodes(),
        "edges":       G.number_of_edges(),
        "density":     round(nx.density(G), 4),
        "directed":    G.is_directed(),
        "avg_degree":  round(np.mean(list(degrees.values())), 2) if degrees else 0,
        "clustering":  round(
            nx.average_clustering(
                G.to_undirected() if G.is_directed() else G
            ), 4
        ),
    }