import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import io
from reportlab.platypus import SimpleDocTemplate
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

DB_NAME = "sobrickz.db"

# === Koneksi DB ===
def get_connection():
    return sqlite3.connect(DB_NAME)

# === Export ke Excel ===
def export_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Rekap")
    return output.getvalue()

# === Export ke PDF ===
def export_pdf(df, title="Rekap Data"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    data = [df.columns.tolist()] + df.values.tolist()
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightblue),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ]))
    elements = [Paragraph(title, styles["Title"]), table]
    doc.build(elements)
    return buffer.getvalue()

# === Sidebar Menu ===
menu = st.sidebar.radio("📌 Pilih Menu", [
    "Input SO Harian", "Rekap Harian",
    "SO Gudang", "Rekap Gudang",
    "Master Barang"
])

# === Input SO Harian ===
if menu == "Input SO Harian":
    st.title("📋 Input SO Harian (Cafe)")
    conn = get_connection()
    barang = pd.read_sql_query("SELECT * FROM barang", conn)
    conn.close()

    tanggal = st.date_input("Tanggal", value=date.today())
    shift = st.selectbox("Shift", ["Pagi", "Sore"])
    nama_so = st.text_input("Nama Petugas SO")
    barang_pilih = st.selectbox("Pilih Barang", barang["nama_barang"] if not barang.empty else [])

    if barang_pilih:
        barang_id = barang.loc[barang["nama_barang"] == barang_pilih, "id"].values[0]

        # Ambil qty akhir kemarin
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT qty_akhir FROM so_harian 
            WHERE barang_id = ? AND tanggal < ? 
            ORDER BY tanggal DESC LIMIT 1
        """, (barang_id, str(tanggal)))
        row = c.fetchone()
        conn.close()

        qty_awal_default = row[0] if row else 0

        qty_awal = st.number_input("Qty Awal", min_value=0.0, step=0.1, value=float(qty_awal_default))
        qty_in = st.number_input("Qty In", min_value=0.0, step=0.1, value=0.0)
        qty_akhir = st.number_input("Qty Akhir", min_value=0.0, step=0.1, value=0.0)
        qty_out = (qty_awal + qty_in) - qty_akhir

        st.info(f"Out = ({qty_awal} + {qty_in}) - {qty_akhir} = {qty_out}")

        if st.button("💾 Simpan SO Harian"):
            conn = get_connection()
            c = conn.cursor()
            c.execute("""
                INSERT INTO so_harian 
                (tanggal, shift, barang_id, qty_awal, qty_in, qty_out, qty_akhir, nama_so)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(tanggal), shift, barang_id, qty_awal, qty_in, qty_out, qty_akhir, nama_so))
            conn.commit()
            conn.close()
            st.success("✅ Data SO Harian berhasil disimpan!")

# === Rekap Harian ===
elif menu == "Rekap Harian":
    st.title("📊 Rekap SO Harian")

    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT s.id, s.tanggal, s.shift, b.nama_barang, 
               s.qty_awal, s.qty_in, s.qty_out, s.qty_akhir, s.nama_so
        FROM so_harian s
        LEFT JOIN barang b ON s.barang_id = b.id
        ORDER BY s.tanggal DESC, s.shift
    """, conn)
    conn.close()

    if df.empty:
        st.warning("⚠️ Belum ada data SO Harian")
    else:
        # Header tabel
        cols = st.columns([2, 1, 2, 2, 2, 2, 2, 2, 2])
        headers = ["Tanggal", "Shift", "Barang", "Awal", "In", "Out", "Akhir", "Petugas", "Aksi"]
        for col, header in zip(cols, headers):
            col.markdown(f"**{header}**")

        # Isi tabel
        for _, row in df.iterrows():
            cols = st.columns([2, 1, 2, 2, 2, 2, 2, 2, 2])
            cols[0].write(row["tanggal"])
            cols[1].write(row["shift"])
            cols[2].write(row["nama_barang"])
            cols[3].write(row["qty_awal"])
            cols[4].write(row["qty_in"])
            cols[5].write(row["qty_out"])
            cols[6].write(row["qty_akhir"])
            cols[7].write(row["nama_so"])
            if cols[8].button("🗑 Hapus", key=f"hapus_harian_{row['id']}"):
                conn = get_connection()
                c = conn.cursor()
                c.execute("DELETE FROM so_harian WHERE id = ?", (row['id'],))
                conn.commit()
                conn.close()
                st.success(f"✅ Data {row['nama_barang']} ({row['tanggal']}, {row['shift']}) dihapus!")
                st.rerun()

        # Export
        df_export = df.drop(columns="id")
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("⬇️ Export Excel", export_excel(df_export), "rekap_harian.xlsx")
        with col2:
            st.download_button("⬇️ Export PDF", export_pdf(df_export, "Rekap SO Harian"), "rekap_harian.pdf")

# === Input SO Gudang ===
elif menu == "SO Gudang":
    st.title("📦 Input SO Gudang")
    conn = get_connection()
    barang = pd.read_sql_query("SELECT * FROM barang", conn)
    conn.close()

    tanggal = st.date_input("Tanggal", value=date.today())
    nama_so = st.text_input("Nama Petugas Gudang")
    barang_pilih = st.selectbox("Pilih Barang", barang["nama_barang"] if not barang.empty else [])

    if barang_pilih:
        barang_id = barang.loc[barang["nama_barang"] == barang_pilih, "id"].values[0]

        # Ambil qty akhir kemarin
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT qty_akhir FROM stok_gudang 
            WHERE barang_id = ? AND tanggal < ? 
            ORDER BY tanggal DESC LIMIT 1
        """, (barang_id, str(tanggal)))
        row = c.fetchone()
        conn.close()

        qty_awal_default = row[0] if row else 0

        qty_awal = st.number_input("Qty Awal Gudang", min_value=0.0, step=0.1, value=float(qty_awal_default))
        qty_in = st.number_input("Qty In Gudang", min_value=0.0, step=0.1, value=0.0)
        qty_akhir = st.number_input("Qty Akhir Gudang", min_value=0.0, step=0.1, value=0.0)
        qty_out = (qty_awal + qty_in) - qty_akhir

        st.info(f"Out = ({qty_awal} + {qty_in}) - {qty_akhir} = {qty_out}")

        if st.button("💾 Simpan SO Gudang"):
            conn = get_connection()
            c = conn.cursor()
            c.execute("""
                INSERT INTO stok_gudang 
                (tanggal, barang_id, qty_awal, qty_in, qty_out, qty_akhir, nama_so)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (str(tanggal), barang_id, qty_awal, qty_in, qty_out, qty_akhir, nama_so))
            conn.commit()
            conn.close()
            st.success("✅ Data SO Gudang berhasil disimpan!")

# === Rekap Gudang ===
elif menu == "Rekap Gudang":
    st.title("📊 Rekap SO Gudang")
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT g.id, g.tanggal, b.nama_barang,
               g.qty_awal, g.qty_in, g.qty_out, g.qty_akhir, g.nama_so
        FROM stok_gudang g
        LEFT JOIN barang b ON g.barang_id = b.id
        ORDER BY g.tanggal DESC
    """, conn)
    conn.close()

    if df.empty:
        st.warning("⚠️ Belum ada data SO Gudang")
    else:
        # Header tabel
        cols = st.columns([2, 2, 1, 1, 1, 1, 2, 1])
        headers = ["Tanggal", "Barang", "Awal", "In", "Out", "Akhir", "Petugas", "Aksi"]
        for col, header in zip(cols, headers):
            col.markdown(f"**{header}**")

        # Isi tabel
        for _, row in df.iterrows():
            cols = st.columns([2, 2, 1, 1, 1, 1, 2, 1])
            cols[0].write(row["tanggal"])
            cols[1].write(row["nama_barang"])
            cols[2].write(row["qty_awal"])
            cols[3].write(row["qty_in"])
            cols[4].write(row["qty_out"])
            cols[5].write(row["qty_akhir"])
            cols[6].write(row["nama_so"])
            if cols[7].button("🗑 Hapus", key=f"hapus_gudang_{row['id']}"):
                conn = get_connection()
                c = conn.cursor()
                c.execute("DELETE FROM stok_gudang WHERE id = ?", (row['id'],))
                conn.commit()
                conn.close()
                st.success(f"✅ Data {row['nama_barang']} ({row['tanggal']}) dihapus!")
                st.rerun()

        df_export = df.drop(columns="id")
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("⬇️ Export Excel", export_excel(df_export), "rekap_gudang.xlsx")
        with col2:
            st.download_button("⬇️ Export PDF", export_pdf(df_export, "Rekap SO Gudang"), "rekap_gudang.pdf")

# === Master Barang ===
elif menu == "Master Barang":
    st.title("📦 Master Barang")
    nama_baru = st.text_input("Nama Barang Baru")
    satuan_baru = st.text_input("Satuan (Kg, Liter, Pcs, dll)")

    if st.button("➕ Tambah Barang"):
        if nama_baru and satuan_baru:
            conn = get_connection()
            c = conn.cursor()
            c.execute("INSERT INTO barang (nama_barang, satuan) VALUES (?, ?)", (nama_baru, satuan_baru))
            conn.commit()
            conn.close()
            st.success(f"✅ Barang '{nama_baru}' berhasil ditambahkan!")

    conn = get_connection()
    df_barang = pd.read_sql_query("SELECT * FROM barang", conn)
    conn.close()
    st.dataframe(df_barang)

    if not df_barang.empty:
        barang_hapus = st.selectbox("Pilih Barang untuk Hapus", df_barang["nama_barang"])
        if st.button("🗑 Hapus Barang"):
            conn = get_connection()
            c = conn.cursor()
            c.execute("DELETE FROM barang WHERE nama_barang = ?", (barang_hapus,))
            conn.commit()
            conn.close()
            st.warning(f"❌ Barang '{barang_hapus}' sudah dihapus.")

