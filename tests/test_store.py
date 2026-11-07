import json
import os
from datetime import date

import store
from cli import analyze_file

BASE = os.path.join(os.path.dirname(__file__), "..", "samples")
AD = date(2026, 11, 7)


def test_simpan_dan_rekap(tmp_path):
    db = str(tmp_path / "test.db")
    conn = store.connect(db)
    store.init_db(conn)
    with open(os.path.join(BASE, "company_profile.json"), encoding="utf-8") as f:
        profile = json.load(f)
    for name in ["tender_gedung.txt", "tender_jalan.txt", "tender_irigasi.txt"]:
        e, r, risk, ins = analyze_file(os.path.join(BASE, name), profile, AD)
        row_id = store.save_analysis(conn, name, e, r, risk, ins, AD)
        assert row_id > 0
    rekap = store.recap_by_recommendation(conn)
    by_rec = {row["rekomendasi"]: row["jumlah_paket"] for row in rekap}
    assert by_rec == {"BID": 1, "BID DENGAN CATATAN": 1, "NO-BID": 1}
    total = conn.execute("SELECT COUNT(*) AS n FROM analisis_tender").fetchone()["n"]
    assert total == 3
    conn.close()


def test_skema_memakai_berkas_sql():
    assert os.path.exists(store.SCHEMA_PATH)
    assert os.path.exists(store.QUERIES_PATH)
    with open(store.SCHEMA_PATH, encoding="utf-8") as f:
        assert "CREATE TABLE" in f.read()
