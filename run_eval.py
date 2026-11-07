"""Evaluasi akurasi ekstraksi pada set contoh di samples/.

Menjalankan ekstraksi + checklist pada setiap dokumen contoh dan
membandingkan 9 field per dokumen dengan samples/expected.json
(nama paket, instansi, HPS, SBU, pengalaman, modal, batas pemasukan,
pengumuman pemenang, rekomendasi). Tanggal analisis dikunci agar
hasil dapat direproduksi.

Pakai: python run_eval.py
"""

import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from checklist import build_checklist
from extractor import extract

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")


def main():
    with open(os.path.join(BASE, "expected.json"), encoding="utf-8") as f:
        spec = json.load(f)
    with open(os.path.join(BASE, spec["profil"]), encoding="utf-8") as f:
        profile = json.load(f)
    analysis_date = date.fromisoformat(spec["tanggal_analisis"])

    total, correct = 0, 0
    for case in spec["kasus"]:
        with open(os.path.join(BASE, case["file"]), encoding="utf-8") as f:
            extracted = extract(f.read())
        result = build_checklist(extracted, profile, analysis_date)
        checks = [
            ("nama_paket", case["nama_paket_mengandung"] in (extracted["nama_paket"] or "")),
            ("instansi", case["instansi_mengandung"] in (extracted["instansi"] or "")),
            ("nilai_hps_rp", extracted["nilai_hps_rp"] == case["nilai_hps_rp"]),
            ("sbu", extracted["kualifikasi"]["sbu"] == case["sbu"]),
            ("pengalaman_min_rp", extracted["kualifikasi"]["pengalaman_min_rp"] == case["pengalaman_min_rp"]),
            ("modal_min_rp", extracted["kualifikasi"]["modal_min_rp"] == case["modal_min_rp"]),
            ("batas_pemasukan", extracted["jadwal"].get("batas_pemasukan") == case["batas_pemasukan"]),
            ("pengumuman_pemenang", extracted["jadwal"].get("pengumuman_pemenang") == case["pengumuman_pemenang"]),
            ("rekomendasi", result["rekomendasi"] == case["rekomendasi"]),
        ]
        print(f"== {case['file']} (skor {result['skor']}/100, {result['rekomendasi']})")
        for name, ok in checks:
            total += 1
            correct += 1 if ok else 0
            print(f"   [{'OK' if ok else 'GAGAL'}] {name}")
    pct = (correct / total * 100) if total else 0
    print(f"\nAkurasi pada set contoh: {correct}/{total} field benar ({pct:.1f}%)")
    return 0 if correct == total else 1


if __name__ == "__main__":
    sys.exit(main())
