import streamlit as st

st.set_page_config(
    page_title="Network Graph Analyzer",
    layout="wide"
)

st.title("Network Graph Analyzer")

st.sidebar.header("Input Graf")

st.text_area(
    "Masukkan edge"
)

st.subheader("Visualisasi Graf")

st.subheader("Adjacency Matrix")

st.subheader("Analisis Graf")