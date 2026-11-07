import json
import os
from datetime import date

import pytest

from ai_insight import build_insight, generate_questions
from checklist import build_checklist, fuzzy_contains
from extractor import extract
from risk import analyze_risk

BASE = os.path.join(os.path.dirname(__file__), "..", "samples")
AD = date(2026, 11, 7)


@pytest.fixture(scope="module")
def profile():
    with open(os.path.join(BASE, "company_profile.json"), encoding="utf-8") as f:
        return json.load(f)


def analyze(name, profile):
    with open(os.path.join(BASE, name), encoding="utf-8") as f:
        extracted = extract(f.read())
    result = build_checklist(extracted, profile, AD)
    risk = analyze_risk(extracted, result, AD)
    return extracted, result, risk


# ---------- field baru versi 2 ----------

def test_jangka_waktu_terbaca(profile):
    e, _, _ = analyze("tender_gedung.txt", profile)
    assert e["jangka_waktu_hari"] == 180


def test_metode_dan_kontrak_gedung(profile):
    e, _, _ = analyze("tender_gedung.txt", profile)
    assert e["metode_evaluasi"] == "Sistem Gugur"
    assert e["jenis_kontrak"] == "Kontrak Harga Satuan"


def test_metode_dan_kontrak_irigasi(profile):
    e, _, _ = analyze("tender_irigasi.txt", profile)
    assert e["metode_evaluasi"] == "Sistem Nilai"
    assert e["jenis_kontrak"] == "Kontrak Lumsum"


def test_confidence_gedung_tinggi(profile):
    e, _, _ = analyze("tender_gedung.txt", profile)
    assert e["confidence"]["identitas"] == "tinggi"
    assert e["confidence"]["jadwal"] == "tinggi"
    assert e["confidence"]["pelaksanaan"] == "tinggi"


def test_confidence_dokumen_kosong_rendah():
    e = extract("Nama Paket: Contoh Saja\n")
    assert e["confidence"]["dokumen"] == "rendah"
    assert e["confidence"]["kualifikasi"] == "rendah"


# ---------- fuzzy matching ----------

def test_fuzzy_persis_dan_kurung():
    assert fuzzy_contains("Ahli K3 Konstruksi (SKA Madya)", ["Ahli K3 Konstruksi"])


def test_fuzzy_teraudit_tetap_berbeda():
    # Kata penentu "teraudit" membuat kemiripan hanya 0.80, di bawah ambang 0.85.
    assert not fuzzy_contains(
        "Laporan Keuangan Teraudit Tahun Terakhir", ["Laporan Keuangan Tahun Terakhir"]
    )


def test_fuzzy_tidak_mirip_sama_sekali():
    assert not fuzzy_contains("Asphalt Mixing Plant", ["Tower Crane", "Excavator"])


# ---------- risk engine ----------

def test_risiko_gedung_sedang_39(profile):
    _, _, risk = analyze("tender_gedung.txt", profile)
    assert risk["level"] == "Sedang"
    assert risk["skor_risiko"] == 39


def test_risiko_jalan_tinggi(profile):
    _, _, risk = analyze("tender_jalan.txt", profile)
    assert risk["level"] == "Tinggi"
    assert risk["skor_risiko"] == 100


def test_risiko_jalan_faktor_dak(profile):
    _, _, risk = analyze("tender_jalan.txt", profile)
    dana = next(f for f in risk["faktor"] if f["faktor"] == "Sumber dana")
    assert dana["level"] == "Sedang"
    assert "DAK" in dana["detail"]


def test_risiko_irigasi_sedang_40(profile):
    _, _, risk = analyze("tender_irigasi.txt", profile)
    assert risk["level"] == "Sedang"
    assert risk["skor_risiko"] == 40


def test_risiko_lima_faktor(profile):
    _, _, risk = analyze("tender_gedung.txt", profile)
    assert len(risk["faktor"]) == 5


# ---------- ai insight ----------

def test_pertanyaan_gedung_ada_teraudit(profile):
    e, r, risk = analyze("tender_gedung.txt", profile)
    insight = build_insight(e, r, risk)
    teks = " ".join(insight["pertanyaan_aanwijzing"])
    assert "Teraudit" in teks
    assert len(insight["pertanyaan_aanwijzing"]) >= 3


def test_pertanyaan_jalan_ada_peralatan_dan_waktu(profile):
    e, r, risk = analyze("tender_jalan.txt", profile)
    teks = " ".join(generate_questions(e, r))
    assert "peralatan" in teks.lower()
    assert "jadwal" in teks.lower()


def test_opini_kedua_struktur(profile):
    e, r, risk = analyze("tender_gedung.txt", profile)
    opini = build_insight(e, r, risk)["opini_kedua"]
    assert set(opini.keys()) == {"risiko_utama", "peluang", "strategi"}
    assert all(isinstance(v, list) and v for v in opini.values())


def test_opini_nobid_menyarankan_tidak_maksa(profile):
    e, r, risk = analyze("tender_irigasi.txt", profile)
    opini = build_insight(e, r, risk)["opini_kedua"]
    assert any("Jangan memaksakan" in s for s in opini["strategi"])
