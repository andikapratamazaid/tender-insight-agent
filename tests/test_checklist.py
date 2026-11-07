import json
import os
from datetime import date

import pytest

from checklist import build_checklist
from extractor import extract
from llm_summary import narrate
from report import build_report

BASE = os.path.join(os.path.dirname(__file__), "..", "samples")
ANALYSIS_DATE = date(2026, 11, 7)


@pytest.fixture(scope="module")
def profile():
    with open(os.path.join(BASE, "company_profile.json"), encoding="utf-8") as f:
        return json.load(f)


def analyze(name, profile):
    with open(os.path.join(BASE, name), encoding="utf-8") as f:
        extracted = extract(f.read())
    return extracted, build_checklist(extracted, profile, ANALYSIS_DATE)


def item(result, name):
    return next(i for i in result["items"] if i["item"] == name)


def test_gedung_rekomendasi_bid(profile):
    _, result = analyze("tender_gedung.txt", profile)
    assert result["rekomendasi"] == "BID"


def test_gedung_skor(profile):
    _, result = analyze("tender_gedung.txt", profile)
    assert result["skor"] == 87


def test_gedung_item_inti_ok(profile):
    _, result = analyze("tender_gedung.txt", profile)
    assert item(result, "sbu")["status"] == "OK"
    assert item(result, "pengalaman")["status"] == "OK"
    assert item(result, "modal")["status"] == "OK"


def test_gedung_dokumen_kurang_tahun_audit(profile):
    _, result = analyze("tender_gedung.txt", profile)
    dok = item(result, "dokumen")
    assert dok["status"] == "KURANG"
    assert "Teraudit" in dok["detail"]


def test_gedung_peralatan_kurang_scaffolding(profile):
    _, result = analyze("tender_gedung.txt", profile)
    per = item(result, "peralatan")
    assert per["status"] == "KURANG"
    assert "Scaffolding" in per["detail"]


def test_jalan_rekomendasi_catatan(profile):
    _, result = analyze("tender_jalan.txt", profile)
    assert result["rekomendasi"] == "BID DENGAN CATATAN"


def test_jalan_skor(profile):
    _, result = analyze("tender_jalan.txt", profile)
    assert result["skor"] == 80


def test_jalan_waktu_kurang(profile):
    _, result = analyze("tender_jalan.txt", profile)
    waktu = item(result, "waktu")
    assert waktu["status"] == "KURANG"
    assert "4 hari" in waktu["detail"]


def test_jalan_peralatan_gagal(profile):
    _, result = analyze("tender_jalan.txt", profile)
    assert item(result, "peralatan")["status"] == "GAGAL"


def test_irigasi_rekomendasi_nobid(profile):
    _, result = analyze("tender_irigasi.txt", profile)
    assert result["rekomendasi"] == "NO-BID"


def test_irigasi_sbu_gagal_keras(profile):
    _, result = analyze("tender_irigasi.txt", profile)
    sbu = item(result, "sbu")
    assert sbu["status"] == "GAGAL"
    assert sbu["hard"] is True


def test_profil_tanpa_sbu_semua_nobid():
    kosong = {"sbu": [], "modal_disetor_rp": 0, "pengalaman": [], "tenaga_ahli": [], "peralatan": [], "dokumen": []}
    with open(os.path.join(BASE, "tender_gedung.txt"), encoding="utf-8") as f:
        extracted = extract(f.read())
    result = build_checklist(extracted, kosong, ANALYSIS_DATE)
    assert result["rekomendasi"] == "NO-BID"


def test_batas_lewat_jadi_nobid(profile):
    with open(os.path.join(BASE, "tender_gedung.txt"), encoding="utf-8") as f:
        extracted = extract(f.read())
    result = build_checklist(extracted, profile, date(2026, 12, 1))
    assert item(result, "waktu")["status"] == "GAGAL"
    assert result["rekomendasi"] == "NO-BID"


def test_laporan_mengandung_rekomendasi(profile):
    extracted, result = analyze("tender_gedung.txt", profile)
    report = build_report(extracted, result, ANALYSIS_DATE)
    assert "## Rekomendasi: BID" in report
    assert "Skor total: 87/100" in report
    assert "Batas Akhir Pemasukan Penawaran" in report


def test_narasi_templat_tanpa_kunci_api(profile, monkeypatch):
    monkeypatch.delenv("TENDER_INSIGHT_LLM_API_KEY", raising=False)
    extracted, result = analyze("tender_irigasi.txt", profile)
    teks = narrate(extracted, result)
    assert "NO-BID" in teks
    assert "3.275.000.000" in teks
