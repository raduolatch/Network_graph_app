import sqlite3
import json
from datetime import datetime

DB_NAME = "network_graph.db"

def init_db():
    """Inisialisasi database dan buat tabel jika belum ada."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Tabel untuk menyimpan graph (progress)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS graphs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            nodes TEXT NOT NULL,
            edges TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabel untuk menyimpan history aksi
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            graph_id INTEGER,
            action TEXT NOT NULL,
            detail TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (graph_id) REFERENCES graphs(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Database berhasil diinisialisasi.")


def save_graph(name, nodes, edges):
    """Simpan atau update graph ke database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    nodes_json = json.dumps(list(nodes))
    edges_json = json.dumps(list(edges))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Cek apakah graph dengan nama ini sudah ada
    cursor.execute("SELECT id FROM graphs WHERE name = ?", (name,))
    row = cursor.fetchone()

    if row:
        graph_id = row[0]
        cursor.execute(
            "UPDATE graphs SET nodes=?, edges=?, updated_at=? WHERE id=?",
            (nodes_json, edges_json, now, graph_id)
        )
    else:
        cursor.execute(
            "INSERT INTO graphs (name, nodes, edges, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (name, nodes_json, edges_json, now, now)
        )
        graph_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return graph_id


def load_graph(name):
    """Load graph dari database berdasarkan nama."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT nodes, edges FROM graphs WHERE name = ?", (name,))
    row = cursor.fetchone()
    conn.close()

    if row:
        nodes = json.loads(row[0])
        edges = json.loads(row[1])
        return nodes, edges
    return None, None


def get_all_graphs():
    """Ambil semua nama graph yang tersimpan."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, updated_at FROM graphs ORDER BY updated_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows


def log_history(graph_id, action, detail=""):
    """Catat aksi ke tabel history."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO history (graph_id, action, detail) VALUES (?, ?, ?)",
        (graph_id, action, detail)
    )
    conn.commit()
    conn.close()


def get_history(graph_id):
    """Ambil history berdasarkan graph_id."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT action, detail, timestamp FROM history WHERE graph_id = ? ORDER BY timestamp DESC",
        (graph_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def delete_graph(name):
    """Hapus graph dari database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM graphs WHERE name = ?", (name,))
    conn.commit()
    conn.close()
