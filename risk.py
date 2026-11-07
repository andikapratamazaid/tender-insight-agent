"""Risk Engine: menilai risiko mengikuti tender dari angka hasil ekstraksi.

Lima faktor dinilai terpisah lalu digabung menjadi skor risiko 0-100 dan
level Rendah / Sedang / Tinggi. Semua ambang dinyatakan eksplisit di sini
agar dapat diaudit dan diubah sesuai selera risiko perusahaan.
"""

from datetime import date

# Ambang intensitas pelaksanaan (rupiah nilai pekerjaan per hari kalender).
INTENSITAS_SEDANG = 50_000_000
INTENSITAS_TINGGI = 100_000_000


def _faktor(nama, level, poin, detail):
    return {"faktor": nama, "level": level, "poin": poin, "detail": detail}


def _f_jadwal(extracted, analysis_date):
    raw = extracted.get("jadwal", {}).get("batas_pemasukan")
    if not raw:
        return _faktor("Jadwal pemasukan", "Sedang", 15, "Batas pemasukan tidak terbaca, perlu konfirmasi manual.")
    sisa = (date.fromisoformat(raw) - analysis_date).days
    if sisa < 0:
        return _faktor("Jadwal pemasukan", "Tinggi", 40, f"Batas pemasukan sudah lewat {-sisa} hari.")
    if sisa <= 4:
        return _faktor("Jadwal pemasukan", "Tinggi", 30, f"Sisa {sisa} hari menuju batas pemasukan, persiapan sangat mepet.")
    if sisa <= 9:
        return _faktor("Jadwal pemasukan", "Sedang", 15, f"Sisa {sisa} hari menuju batas pemasukan.")
    return _faktor("Jadwal pemasukan", "Rendah", 0, f"Sisa {sisa} hari menuju batas pemasukan, cukup aman.")


def _f_jendela(extracted):
    j = extracted.get("jadwal", {})
    if "penjelasan" not in j or "batas_pemasukan" not in j:
        return _faktor("Jendela persiapan", "Sedang", 10, "Tanggal penjelasan atau batas pemasukan tidak lengkap.")
    rentang = (date.fromisoformat(j["batas_pemasukan"]) - date.fromisoformat(j["penjelasan"])).days
    if rentang < 7:
        return _faktor("Jendela persiapan", "Tinggi", 20, f"Hanya {rentang} hari dari aanwijzing ke batas pemasukan.")
    if rentang < 14:
        return _faktor("Jendela persiapan", "Sedang", 10, f"{rentang} hari dari aanwijzing ke batas pemasukan.")
    return _faktor("Jendela persiapan", "Rendah", 0, f"{rentang} hari dari aanwijzing ke batas pemasukan, longgar.")


def _f_intensitas(extracted):
    hps = extracted.get("nilai_hps_rp")
    hari = extracted.get("jangka_waktu_hari")
    if not hps or not hari:
        return _faktor("Intensitas pelaksanaan", "Sedang", 15, "HPS atau jangka waktu tidak terbaca, intensitas tidak dapat dihitung.")
    per_hari = hps // hari
    label = f"Nilai pekerjaan Rp {per_hari:,}/hari selama {hari} hari kalender.".replace(",", ".")
    if per_hari > INTENSITAS_TINGGI:
        return _faktor("Intensitas pelaksanaan", "Tinggi", 30, label + " Sangat padat, butuh sumber daya besar sejak awal.")
    if per_hari >= INTENSITAS_SEDANG:
        return _faktor("Intensitas pelaksanaan", "Sedang", 15, label + " Cukup padat, perlu mobilisasi cepat.")
    return _faktor("Intensitas pelaksanaan", "Rendah", 0, label)


def _f_kualifikasi(checklist_result):
    gagal = [i for i in checklist_result["items"] if i["status"] == "GAGAL"]
    kurang = [i for i in checklist_result["items"] if i["status"] == "KURANG"]
    poin = min(30, len(gagal) * 20 + len(kurang) * 7)
    if gagal:
        level = "Tinggi"
    elif kurang:
        level = "Sedang"
    else:
        level = "Rendah"
    detail = f"{len(gagal)} item gugur dan {len(kurang)} item kurang dari checklist kesiapan."
    return _faktor("Kesiapan kualifikasi", level, poin, detail)


def _f_dana(extracted):
    sumber = (extracted.get("sumber_dana") or "").upper()
    if "DAK" in sumber:
        return _faktor("Sumber dana", "Sedang", 10, "Dana DAK terikat petunjuk teknis dan jadwal pencairan, perhatikan risiko termin pembayaran.")
    if sumber:
        return _faktor("Sumber dana", "Rendah", 0, f"Sumber dana {extracted.get('sumber_dana')} adalah pola pendanaan standar.")
    return _faktor("Sumber dana", "Sedang", 10, "Sumber dana tidak terbaca dari dokumen.")


def analyze_risk(extracted, checklist_result, analysis_date):
    """Hitung skor dan level risiko beserta faktor-faktornya."""
    faktor = [
        _f_jadwal(extracted, analysis_date),
        _f_jendela(extracted),
        _f_intensitas(extracted),
        _f_kualifikasi(checklist_result),
        _f_dana(extracted),
    ]
    skor = min(100, sum(f["poin"] for f in faktor))
    if skor > 55:
        level = "Tinggi"
    elif skor >= 25:
        level = "Sedang"
    else:
        level = "Rendah"
    return {"skor_risiko": skor, "level": level, "faktor": faktor}
