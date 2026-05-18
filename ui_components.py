"""
ui_components.py
Reusable HTML/UI component functions untuk Network Graph Analyzer.

Cara pakai di app.py:
    from ui_components import (
        metric_card, badge, section_label,
        panel, empty_state, info_row
    )
"""

import streamlit as st

# METRIC CARD
def metric_card(value, label: str, delta: str = None, color: str = "accent") -> None:
    """
    Kartu metrik dengan nilai besar + label kecil di bawahnya.

    Args:
        value  : Nilai utama yang ditampilkan (int, float, str).
        label  : Label deskriptif di bawah nilai.
        delta  : Teks opsional di baris ketiga (misal: perubahan / satuan).
        color  : Warna nilai — "accent" (cyan), "purple", "red".

    Contoh:
        metric_card(42, "Nodes")
        metric_card(3.14, "Avg Path", delta="weighted")
        metric_card("N/A", "Diameter", color="red")
    """
    color_map = {
        "accent": "var(--accent)",
        "purple": "var(--accent2)",
        "red":    "var(--accent3)",
    }
    value_color = color_map.get(color, "var(--accent)")
    delta_html  = f'<div class="metric-delta">▲ {delta}</div>' if delta else ""

    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color:{value_color};">{value}</div>
        <div class="metric-label">{label}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

# BADGE
def badge(text: str, color: str = "green") -> str:
    """
    Kembalikan HTML string badge inline.
    Gunakan dengan st.markdown(..., unsafe_allow_html=True).

    Args:
        text  : Teks di dalam badge.
        color : "green" | "purple" | "red"

    Returns:
        str: HTML <span> badge.

    Contoh:
        st.markdown(badge("CONNECTED") + badge("DIRECTED", "purple"),
                    unsafe_allow_html=True)
    """
    valid = {"green", "purple", "red"}
    color = color if color in valid else "green"
    return f'<span class="badge badge-{color}">{text}</span>'


# SECTION LABEL
def section_label(text: str, margin_top: str = "0") -> None:
    """
    Label judul section bergaya monospace uppercase + garis separator.

    Args:
        text       : Teks label.
        margin_top : Nilai CSS margin-top (misal: "1rem").

    Contoh:
        section_label("Graph Metrics")
        section_label("Adjacency Matrix", margin_top="1.5rem")
    """
    st.markdown(
        f'<div class="section-label" style="margin-top:{margin_top};">{text}</div>',
        unsafe_allow_html=True,
    )

# PANEL
def panel(title: str, body_html: str, border_color: str = "var(--border2)") -> None:
    """
    Kotak panel dark dengan judul dan konten HTML bebas.

    Args:
        title        : Judul panel (teks biasa).
        body_html    : Konten HTML di dalam panel.
        border_color : Warna border CSS (default: ungu transparan).

    Contoh:
        panel(
            "📏 Avg Shortest Path",
            '<span style="font-family:monospace;font-size:1.5rem;color:#00f5c4;">2.34</span>',
        )
    """
    st.markdown(f"""
    <div class="nga-panel" style="border-color:{border_color};">
        <div class="nga-panel-title">{title}</div>
        {body_html}
    </div>
    """, unsafe_allow_html=True)


def panel_metric(title: str, value, color: str = "#00f5c4") -> None:
    """
    Shortcut panel dengan satu angka besar — paling sering dipakai
    untuk Avg Path, Diameter, dll.

    Args:
        title : Judul panel.
        value : Nilai yang ditampilkan.
        color : Warna teks nilai.

    Contoh:
        panel_metric("📐 Diameter", 5, color="#7c5cfc")
        panel_metric("📏 Avg Path", "N/A")
    """
    body = (
        f'<div style="font-family:\'Space Mono\',monospace;'
        f'font-size:1.5rem;color:{color};">{value}</div>'
    )
    panel(title, body)

# EMPTY STATE
def empty_state(
    icon: str = "🕸️",
    title: str = "No Graph Loaded",
    subtitle: str = 'Configure your graph in the sidebar, then click <strong style="color:#00f5c4;">⚡ Analyze Graph</strong>',
) -> None:
    """
    Tampilkan placeholder kosong di tengah layar saat belum ada graph.

    Args:
        icon     : Emoji / karakter ikon besar.
        title    : Judul placeholder.
        subtitle : Sub-teks (mendukung HTML inline).

    Contoh:
        empty_state()
        empty_state("📂", "No File Uploaded", "Drag a CSV to get started")
    """
    st.markdown(f"""
    <div style="
        text-align:center; padding:5rem 2rem;
        background:rgba(17,24,39,0.6); border-radius:20px;
        border:1px dashed rgba(0,245,196,0.2);
        margin-top:1rem;
    ">
        <div style="font-size:3.5rem; margin-bottom:1rem;">{icon}</div>
        <div style="font-size:1.1rem; font-weight:700; color:#e8eaf0; margin-bottom:0.5rem;">
            {title}
        </div>
        <div style="font-size:0.8rem; color:#6b7280; font-family:'Space Mono',monospace;">
            {subtitle}
        </div>
    </div>
    """, unsafe_allow_html=True)

# GRAPH HEADER BAR (label + badges)
def graph_header(label: str, is_connected: bool, is_directed: bool) -> None:
    """
    Bar tipis di atas metrik yang menampilkan label graph + badge status.

    Args:
        label        : Teks label graph (misal "Random · 50N · 80E").
        is_connected : Apakah graph terhubung.
        is_directed  : Apakah graph berarah.

    Contoh:
        graph_header("Uploaded · 12N · 18E", is_connected=True, is_directed=False)
    """
    conn_badge = (
        badge("CONNECTED", "green")
        if is_connected
        else badge("DISCONNECTED", "red")
    )
    dir_badge = (
        badge("DIRECTED", "purple")
        if is_directed
        else badge("UNDIRECTED", "green")
    )

    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:10px;
                margin-bottom:1.2rem; flex-wrap:wrap;">
        <span style="font-family:'Space Mono',monospace;
                     font-size:0.8rem; color:#6b7280;">{label}</span>
        {conn_badge}
        {dir_badge}
    </div>
    """, unsafe_allow_html=True)

# TOP-N NODES CARD STRIP
def top_nodes_strip(top_df, n: int = 5) -> None:
    """
    Tampilkan strip N kartu node paling berpengaruh (berdasarkan Betweenness).

    Args:
        top_df : DataFrame dengan kolom Node, Betweenness (sudah di-sort).
        n      : Jumlah node yang ditampilkan (default 5).

    Contoh:
        top_nodes_strip(cent_df.head(5))
    """
    cols = st.columns(n)
    rows = list(top_df.head(n).iterrows())

    for i, (_, row) in enumerate(rows):
        with cols[i]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="font-size:1.2rem;">#{i + 1}</div>
                <div class="metric-label">Node {row['Node']}</div>
                <div class="metric-delta">B: {row['Betweenness']}</div>
            </div>
            """, unsafe_allow_html=True)


# NEIGHBOR LIST (monospace chip row)
def neighbor_chips(neighbors: list, max_show: int = 50) -> None:
    """
    Tampilkan neighbors sebagai chip monospace satu baris,
    dengan truncate otomatis jika terlalu banyak.

    Args:
        neighbors : List node tetangga.
        max_show  : Maksimum chip yang ditampilkan.

    Contoh:
        neighbor_chips(list(G.neighbors(selected_node)))
    """
    if not neighbors:
        st.info("This node has no neighbors.")
        return

    shown    = neighbors[:max_show]
    overflow = len(neighbors) - max_show
    chips    = " · ".join([f"`{nb}`" for nb in shown])

    suffix = (
        f' <span style="color:#6b7280;">+{overflow} more</span>'
        if overflow > 0 else ""
    )

    st.markdown(
        f'<div style="font-family:\'Space Mono\',monospace; font-size:0.8rem;'
        f'color:#00f5c4; line-height:2;">{chips}{suffix}</div>',
        unsafe_allow_html=True,
    )


# SIDEBAR SECTION HEADER
def sidebar_section(title: str) -> None:
    """
    Header section monospace di sidebar (pengganti st.markdown hardcoded).

    Args:
        title : Teks header section.

    Contoh:
        sidebar_section("Graph Config")
    """
    st.markdown(
        f'<div class="sidebar-section">{title}</div>',
        unsafe_allow_html=True,
    )