import json
import os
from datetime import date

import pytest

from extractor import extract, parse_date_id, parse_money

BASE = os.path.join(os.path.dirname(__file__), "..", "samples")


def load(name):
    with open(os.path.join(BASE, name), encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def gedung():
    return extract(load("tender_gedung.txt"))


@pytest.fixture(scope="module")
def jalan():
    return extract(load("tender_jalan.txt"))


@pytest.fixture(scope="module")
def irigasi():
    return extract(load("tender_irigasi.txt"))


# ---------- parse_money ----------

def test_parse_money_format_baku():
    assert parse_money("Rp 12.450.000.000,00") == 12_450_000_000


def test_parse_money_tanpa_sen():
    assert parse_money("Rp 6.875.500.000") == 6_875_500_000


def test_parse_money_miliar():
    assert parse_money("Rp 2,5 miliar") == 2_500_000_000


def test_parse_money_juta():
    assert parse_money("Rp 750 juta") == 750_000_000


def test_parse_money_kosong():
    assert parse_money("tidak ada angka") is None
    assert parse_money("") is None


# ---------- parse_date_id ----------

def test_parse_date_november():
    assert parse_date_id("Jumat, 27 November 2026 pukul 23.59 WIB") == date(2026, 11, 27)


def test_parse_date_desember():
    assert parse_date_id("Senin, 7 Desember 2026") == date(2026, 12, 7)


def test_parse_date_kosong():
    assert parse_date_id("belum ditentukan") is None


# ---------- identitas paket ----------

def test_gedung_nama_paket(gedung):
    assert "Gedung Kantor Dinas Terpadu" in gedung["nama_paket"]


def test_gedung_instansi(gedung):
    assert "Pekerjaan Umum" in gedung["instansi"]


def test_gedung_hps(gedung):
    assert gedung["nilai_hps_rp"] == 12_450_000_000


def test_gedung_tahun_dan_sumber(gedung):
    assert gedung["tahun_anggaran"] == 2026
    assert "APBD" in gedung["sumber_dana"]


def test_jalan_hps(jalan):
    assert jalan["nilai_hps_rp"] == 6_875_500_000


def test_irigasi_hps(irigasi):
    assert irigasi["nilai_hps_rp"] == 3_275_000_000


# ---------- jadwal ----------

def test_gedung_jadwal_lengkap(gedung):
    j = gedung["jadwal"]
    assert j["penjelasan"] == "2026-11-16"
    assert j["batas_pemasukan"] == "2026-11-27"
    assert j["pembukaan"] == "2026-11-28"
    assert j["masa_sanggah"] == "2026-11-30"
    assert j["pengumuman_pemenang"] == "2026-12-07"


def test_jalan_batas_pemasukan(jalan):
    assert jalan["jadwal"]["batas_pemasukan"] == "2026-11-11"


def test_irigasi_pengumuman(irigasi):
    assert irigasi["jadwal"]["pengumuman_pemenang"] == "2026-11-30"


# ---------- kualifikasi ----------

def test_gedung_sbu(gedung):
    assert gedung["kualifikasi"]["sbu"] == ["BG002"]


def test_jalan_sbu(jalan):
    assert jalan["kualifikasi"]["sbu"] == ["BS001"]


def test_irigasi_sbu(irigasi):
    assert irigasi["kualifikasi"]["sbu"] == ["SI002"]


def test_gedung_pengalaman(gedung):
    assert gedung["kualifikasi"]["pengalaman_min_rp"] == 8_000_000_000
    assert gedung["kualifikasi"]["pengalaman_dalam_tahun"] == 4


def test_gedung_modal(gedung):
    assert gedung["kualifikasi"]["modal_min_rp"] == 2_500_000_000


def test_jalan_modal(jalan):
    assert jalan["kualifikasi"]["modal_min_rp"] == 1_500_000_000


def test_gedung_tenaga_ahli(gedung):
    tenaga = gedung["kualifikasi"]["tenaga_ahli"]
    assert len(tenaga) == 2
    assert any("Bangunan Gedung" in t for t in tenaga)


def test_gedung_peralatan(gedung):
    assert gedung["kualifikasi"]["peralatan"] == ["Tower Crane", "Concrete Pump", "Scaffolding"]


def test_jalan_peralatan(jalan):
    assert "Asphalt Mixing Plant" in jalan["kualifikasi"]["peralatan"]


def test_gedung_dokumen(gedung):
    assert len(gedung["dokumen_wajib"]) == 6
    assert "Laporan Keuangan Teraudit Tahun Terakhir" in gedung["dokumen_wajib"]


def test_irigasi_dokumen(irigasi):
    assert "SBU SI002" in irigasi["dokumen_wajib"]
