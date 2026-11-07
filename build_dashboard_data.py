"""Bangun dashboard/data.js dari hasil analisis nyata atas data contoh.

Dashboard HTML membaca window.TENDER_DATA dari berkas ini, sehingga
angka yang tampil di dashboard selalu sama dengan keluaran CLI.

Pakai: python build_dashboard_data.py
"""

import json
import os
from datetime import date

from cli import analyze_file

BASE = os.path.dirname(os.path.abspath(__file__))
SAMPLES = ["tender_gedung.txt", "tender_jalan.txt", "tender_irigasi.txt"]
ANALYSIS_DATE = date(2026, 11, 7)

ITEM_LABEL = {
    "sbu": "SBU sesuai bidang",
    "pengalaman": "Pengalaman sejenis",
    "modal": "Modal disetor",
    "tenaga_ahli": "Tenaga ahli",
    "peralatan": "Peralatan utama",
    "dokumen": "Dokumen wajib",
    "waktu": "Waktu persiapan",
}

JADWAL_LABEL = {
    "penjelasan": "Aanwijzing",
    "batas_pemasukan": "Batas pemasukan",
    "pembukaan": "Pembukaan",
    "masa_sanggah": "Masa sanggah",
    "pengumuman_pemenang": "Pengumuman pemenang",
}


def main():
    with open(os.path.join(BASE, "samples", "company_profile.json"), encoding="utf-8") as f:
        profile = json.load(f)
    data = {"tanggal_analisis": ANALYSIS_DATE.isoformat(), "profil": profile["nama"], "tender": []}
    for name in SAMPLES:
        extracted, result, risk, insight = analyze_file(
            os.path.join(BASE, "samples", name), profile, ANALYSIS_DATE
        )
        data["tender"].append(
            {
                "berkas": name,
                "nama_paket": extracted["nama_paket"],
                "instansi": extracted["instansi"],
                "nilai_hps_rp": extracted["nilai_hps_rp"],
                "jangka_waktu_hari": extracted["jangka_waktu_hari"],
                "skor": result["skor"],
                "rekomendasi": result["rekomendasi"],
                "risiko": {"level": risk["level"], "skor": risk["skor_risiko"]},
                "checklist": [
                    {
                        "item": ITEM_LABEL.get(i["item"], i["item"]),
                        "status": i["status"],
                        "bobot": i["bobot"],
                        "skor": i["skor"],
                        "detail": i["detail"],
                    }
                    for i in result["items"]
                ],
                "jadwal": [
                    {"tahap": JADWAL_LABEL.get(k, k), "tanggal": v}
                    for k, v in extracted["jadwal"].items()
                ],
                "pertanyaan": insight["pertanyaan_aanwijzing"],
            }
        )
    out = os.path.join(BASE, "dashboard", "data.js")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("window.TENDER_DATA = ")
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write(";\n")
    print(f"Ditulis: {out} ({len(data['tender'])} tender)")


if __name__ == "__main__":
    main()
