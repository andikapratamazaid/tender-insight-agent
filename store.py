"""Penyimpanan riwayat analisis ke SQLite memakai berkas SQL di db/.

Skema hidup di db/schema.sql dan contoh query rekap di db/queries.sql,
jadi lapisan SQL-nya adalah berkas SQL sungguhan, bukan string yang
tersembunyi di kode Python.
"""

import os
import sqlite3

BASE = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(BASE, "db", "schema.sql")
QUERIES_PATH = os.path.join(BASE, "db", "queries.sql")


def connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn):
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()


def save_analysis(conn, berkas, extracted, result, risk, insight, analysis_date):
    """Simpan satu hasil analisis, kembalikan id barisnya."""
    cur = conn.execute(
        """
        INSERT INTO analisis_tender (
            tanggal_analisis, berkas, nama_paket, instansi, nilai_hps_rp,
            jangka_waktu_hari, skor_kesiapan, rekomendasi, level_risiko,
            skor_risiko, jumlah_pertanyaan
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            analysis_date.isoformat(),
            berkas,
            extracted.get("nama_paket"),
            extracted.get("instansi"),
            extracted.get("nilai_hps_rp"),
            extracted.get("jangka_waktu_hari"),
            result["skor"],
            result["rekomendasi"],
            risk["level"],
            risk["skor_risiko"],
            len(insight["pertanyaan_aanwijzing"]),
        ),
    )
    conn.commit()
    return cur.lastrowid


def recap_by_recommendation(conn):
    rows = conn.execute(
        """
        SELECT rekomendasi, COUNT(*) AS jumlah_paket, AVG(skor_kesiapan) AS rata_rata_skor
        FROM analisis_tender
        GROUP BY rekomendasi
        ORDER BY jumlah_paket DESC
        """
    ).fetchall()
    return [dict(r) for r in rows]
