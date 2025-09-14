import sqlite3

DB_NAME = "sobrickz.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Tabel Master Barang
    c.execute("""
    CREATE TABLE IF NOT EXISTS barang (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama_barang TEXT NOT NULL,
        satuan TEXT NOT NULL
    )
    """)

    # Tabel SO Harian (Cafe)
    c.execute("""
    CREATE TABLE IF NOT EXISTS so_harian (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tanggal DATE NOT NULL,
        shift TEXT NOT NULL,
        barang_id INTEGER NOT NULL,
        qty_awal REAL DEFAULT 0,
        qty_in REAL DEFAULT 0,
        qty_out REAL DEFAULT 0,
        qty_akhir REAL DEFAULT 0,
        nama_so TEXT NOT NULL,
        FOREIGN KEY (barang_id) REFERENCES barang(id)
    )
    """)

    # Tabel SO Gudang
    c.execute("""
    CREATE TABLE IF NOT EXISTS stok_gudang (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tanggal DATE NOT NULL,
        barang_id INTEGER NOT NULL,
        qty_awal REAL DEFAULT 0,
        qty_in REAL DEFAULT 0,
        qty_out REAL DEFAULT 0,
        qty_akhir REAL DEFAULT 0,
        nama_so TEXT NOT NULL,
        FOREIGN KEY (barang_id) REFERENCES barang(id)
    )
    """)

    conn.commit()
    conn.close()
    print("✅ Database berhasil di-setup!")

if __name__ == "__main__":
    init_db()
