"""Checklist kesiapan bid dan rekomendasi BID / BID DENGAN CATATAN / NO-BID.

Setiap item punya bobot. Status OK mengambil bobot penuh, KURANG setengah,
GAGAL nol. Item keras (SBU, pengalaman, modal) yang GAGAL langsung
menghasilkan NO-BID berapa pun skornya, meniru gugur kualifikasi di
pascakualifikasi.
"""

from datetime import date
import re

WEIGHTS = {
    "sbu": 20,
    "pengalaman": 20,
    "modal": 15,
    "tenaga_ahli": 10,
    "peralatan": 10,
    "dokumen": 15,
    "waktu": 10,
}

HARD_ITEMS = {"sbu", "pengalaman", "modal"}


def _norm(text):
    return " ".join(str(text).lower().split())


def _tokens(text):
    return set(_norm(_strip_parens(text)).split())


def fuzzy_contains(required, owned_list):
    """Pencocokan semantik ringan antara satu syarat dan daftar milik perusahaan.

    Cocok bila: sama persis setelah normalisasi, salah satu menjadi bagian
    teks yang lain, atau kemiripan himpunan kata (Jaccard) >= 0.85. Ambang
    sengaja tinggi agar kualifikasi penting seperti kata "teraudit" tidak
    dianggap sama dengan versi tanpa kata itu (Jaccard-nya 0.80).
    """
    req_norm = _norm(_strip_parens(required))
    req_tokens = _tokens(required)
    for owned in owned_list:
        own_norm = _norm(_strip_parens(owned))
        if req_norm == own_norm or req_norm in own_norm or own_norm in req_norm:
            return True
        own_tokens = _tokens(owned)
        union = req_tokens | own_tokens
        if union and len(req_tokens & own_tokens) / len(union) >= 0.85:
            return True
    return False


def _item(name, status, hard, detail):
    weight = WEIGHTS[name]
    score = weight if status == "OK" else (weight // 2 if status == "KURANG" else 0)
    return {
        "item": name,
        "status": status,
        "hard": hard,
        "bobot": weight,
        "skor": score,
        "detail": detail,
    }


def _check_sbu(required, profile):
    owned = set(profile.get("sbu", []))
    if not required:
        return _item("sbu", "KURANG", True, "Kode SBU tidak terbaca dari dokumen tender.")
    missing = [c for c in required if c not in owned]
    if missing:
        return _item("sbu", "GAGAL", True, "SBU tidak dimiliki: " + ", ".join(missing))
    return _item("sbu", "OK", True, "SBU sesuai: " + ", ".join(required))


def _check_pengalaman(required_rp, bidang, profile):
    if not required_rp:
        return _item("pengalaman", "KURANG", True, "Syarat pengalaman tidak terbaca.")
    best = 0
    for exp in profile.get("pengalaman", []):
        if exp.get("bidang") == bidang:
            best = max(best, int(exp.get("nilai_rp", 0)))
    if best >= required_rp:
        return _item(
            "pengalaman", "OK", True,
            f"Pengalaman terbesar bidang {bidang} Rp {best:,} memenuhi syarat Rp {required_rp:,}.".replace(",", "."),
        )
    return _item(
        "pengalaman", "GAGAL", True,
        f"Pengalaman terbesar bidang {bidang} Rp {best:,} di bawah syarat Rp {required_rp:,}.".replace(",", "."),
    )


def _check_modal(required_rp, profile):
    if not required_rp:
        return _item("modal", "KURANG", True, "Syarat modal tidak terbaca.")
    owned = int(profile.get("modal_disetor_rp", 0))
    if owned >= required_rp:
        return _item("modal", "OK", True, f"Modal disetor Rp {owned:,} memenuhi syarat.".replace(",", "."))
    return _item("modal", "GAGAL", True, f"Modal disetor Rp {owned:,} di bawah syarat Rp {required_rp:,}.".replace(",", "."))


def _strip_parens(text):
    return re.sub(r"\(.*?\)", "", str(text))


def _check_partial(name, required, owned, label):
    if not required:
        return _item(name, "KURANG", False, f"Daftar {label} tidak terbaca dari dokumen.")

    def clean(text):
        return _norm(_strip_parens(text))

    missing = [r for r in required if not fuzzy_contains(r, owned)]
    if not missing:
        return _item(name, "OK", False, f"Seluruh {label} yang disyaratkan tersedia ({len(required)} item).")
    if len(missing) == len(required):
        return _item(name, "GAGAL", False, f"Belum ada {label} yang disyaratkan: " + ", ".join(missing))
    return _item(name, "KURANG", False, f"{label.capitalize()} belum lengkap, kurang: " + ", ".join(missing))


def _check_dokumen(required_docs, profile):
    if not required_docs:
        return _item("dokumen", "KURANG", False, "Daftar dokumen wajib tidak terbaca.")
    import re

    owned_docs = list(profile.get("dokumen", []))
    owned_sbu = set(profile.get("sbu", []))
    missing = []
    for doc in required_docs:
        code = re.search(r"\b([A-Z]{2}\d{3})\b", doc)
        if code:
            if code.group(1) not in owned_sbu:
                missing.append(doc)
            continue
        if not fuzzy_contains(doc, owned_docs):
            missing.append(doc)
    if not missing:
        return _item("dokumen", "OK", False, f"Seluruh dokumen wajib tersedia ({len(required_docs)} dokumen).")
    return _item("dokumen", "KURANG", False, "Dokumen belum lengkap: " + ", ".join(missing))


def _check_waktu(jadwal, analysis_date):
    raw = jadwal.get("batas_pemasukan")
    if not raw:
        return _item("waktu", "KURANG", False, "Batas pemasukan tidak terbaca.")
    deadline = date.fromisoformat(raw)
    sisa = (deadline - analysis_date).days
    if sisa < 0:
        return _item("waktu", "GAGAL", False, f"Batas pemasukan sudah lewat {-sisa} hari.")
    if sisa >= 5:
        return _item("waktu", "OK", False, f"Sisa waktu persiapan {sisa} hari sampai batas pemasukan.")
    return _item("waktu", "KURANG", False, f"Sisa waktu persiapan hanya {sisa} hari, di bawah ambang aman 5 hari.")


def build_checklist(extracted, profile, analysis_date):
    """Bangun checklist + rekomendasi dari hasil ekstraksi dan profil perusahaan."""
    kual = extracted.get("kualifikasi", {})
    bidang = kual.get("sbu", [None])[0]
    items = [
        _check_sbu(kual.get("sbu", []), profile),
        _check_pengalaman(kual.get("pengalaman_min_rp"), bidang, profile),
        _check_modal(kual.get("modal_min_rp"), profile),
        _check_partial("tenaga_ahli", kual.get("tenaga_ahli", []), profile.get("tenaga_ahli", []), "tenaga ahli"),
        _check_partial("peralatan", kual.get("peralatan", []), profile.get("peralatan", []), "peralatan"),
        _check_dokumen(extracted.get("dokumen_wajib", []), profile),
        _check_waktu(extracted.get("jadwal", {}), analysis_date),
    ]
    score = sum(i["skor"] for i in items)
    hard_fail = [i for i in items if i["hard"] and i["status"] == "GAGAL"]
    waktu_fail = [i for i in items if i["item"] == "waktu" and i["status"] == "GAGAL"]
    if hard_fail or waktu_fail or score < 60:
        label = "NO-BID"
    elif score >= 85:
        label = "BID"
    else:
        label = "BID DENGAN CATATAN"
    reasons = [i["detail"] for i in items if i["status"] != "OK"]
    return {"items": items, "skor": score, "rekomendasi": label, "alasan": reasons}
