"""Ekstraksi deterministik dari teks pengumuman tender konstruksi.

Inti agent ini sengaja deterministik (regex + aturan) agar hasilnya
dapat dites dan tidak mengarang: setiap field yang keluar dapat dilacak
ke baris teks sumbernya. Setiap field juga diberi skor keyakinan
(confidence) agar lapisan di atasnya tahu mana hasil bacaan pasti dan
mana yang perlu dikonfirmasi ke panitia. Lapisan bahasa (LLM) hanya
dipakai untuk narasi dan opini kedua, bukan untuk angka.
"""

import re
from datetime import date

from patterns import LIST_HEADERS, MONTHS_ID, SCHEDULE_KEYWORDS

_MONEY_RE = re.compile(r"Rp\.?\s*([\d][\d\.,]*)\s*(miliar|juta)?", re.IGNORECASE)
_DATE_RE = re.compile(
    r"(\d{1,2})\s+(" + "|".join(MONTHS_ID.keys()) + r")\s+(\d{4})", re.IGNORECASE
)
_SBU_RE = re.compile(r"\b([A-Z]{2}\d{3})\b")


def parse_money(text):
    """Ambil nilai uang pertama dari teks bebas, kembalikan int rupiah.

    Mendukung format baku "Rp 12.450.000.000,00" dan format ringkas
    "Rp 2,5 miliar" / "Rp 750 juta". Mengembalikan None bila tidak ada.
    """
    if not text:
        return None
    m = _MONEY_RE.search(text)
    if not m:
        return None
    raw, unit = m.group(1), (m.group(2) or "").lower()
    raw = raw.rstrip(".,")
    if unit:
        value = float(raw.replace(",", ".")) if "," in raw else float(raw.replace(".", ""))
        multiplier = 1_000_000_000 if unit == "miliar" else 1_000_000
        return int(round(value * multiplier))
    int_part = raw.split(",")[0].replace(".", "")
    return int(int_part) if int_part.isdigit() else None


def parse_date_id(text):
    """Ambil tanggal pertama berformat Indonesia dari teks, kembalikan date."""
    if not text:
        return None
    m = _DATE_RE.search(text)
    if not m:
        return None
    day, month_name, year = int(m.group(1)), m.group(2).lower(), int(m.group(3))
    return date(year, MONTHS_ID[month_name], day)


def _label_value(lines, label):
    for line in lines:
        if line.strip().lower().startswith(label.lower()):
            return line.split(":", 1)[1].strip() if ":" in line else line.strip()
    return None


def _extract_schedule(lines):
    jadwal = {}
    for line in lines:
        low = line.lower()
        for keyword, field in SCHEDULE_KEYWORDS:
            if keyword in low and field not in jadwal:
                found = parse_date_id(line)
                if found:
                    jadwal[field] = found.isoformat()
    return jadwal


def _extract_lists(lines):
    result = {}
    active = None
    for line in lines:
        low = line.lower()
        header_found = None
        for keyword, field in LIST_HEADERS:
            if keyword in low:
                header_found = field
                break
        if header_found:
            active = header_found
            result.setdefault(active, [])
            continue
        stripped = line.strip()
        if active and stripped.startswith("-"):
            result[active].append(stripped.lstrip("-").strip())
        elif active and stripped and not stripped.startswith("-"):
            if re.match(r"^\d+\.", stripped) or ":" in stripped:
                active = None
    return result


def extract(text):
    """Ekstrak field terstruktur + confidence dari teks pengumuman tender."""
    lines = text.splitlines()
    joined = "\n".join(lines)

    hps_line = _label_value(lines, "Nilai HPS") or ""
    instansi = _label_value(lines, "Instansi")
    nama_paket = _label_value(lines, "Nama Paket")
    lokasi = _label_value(lines, "Lokasi Pekerjaan")
    sumber_dana = _label_value(lines, "Sumber Dana")
    metode_evaluasi = _label_value(lines, "Metode Evaluasi")
    jenis_kontrak = _label_value(lines, "Jenis Kontrak")

    jangka_hari = None
    m = re.search(r"Jangka Waktu Pelaksanaan\s*:\s*(\d+)", joined)
    if m:
        jangka_hari = int(m.group(1))

    tahun = None
    m = re.search(r"Tahun Anggaran\s*:\s*(\d{4})", joined)
    if m:
        tahun = int(m.group(1))

    sbu_codes = []
    for code in _SBU_RE.findall(joined):
        if code not in sbu_codes:
            sbu_codes.append(code)

    pengalaman_rp, pengalaman_tahun = None, None
    m = re.search(r"[Pp]engalaman[^\n]*", joined)
    if m:
        pengalaman_rp = parse_money(m.group(0))
        mt = re.search(r"dalam\s*(\d+)", m.group(0))
        if mt:
            pengalaman_tahun = int(mt.group(1))

    modal_rp = None
    m = re.search(r"[Mm]odal disetor[^\n]*", joined)
    if m:
        modal_rp = parse_money(m.group(0))

    lists = _extract_lists(lines)
    jadwal = _extract_schedule(lines)

    extracted = {
        "nama_paket": nama_paket,
        "instansi": instansi,
        "lokasi": lokasi,
        "nilai_hps_rp": parse_money(hps_line),
        "tahun_anggaran": tahun,
        "sumber_dana": sumber_dana,
        "jangka_waktu_hari": jangka_hari,
        "metode_evaluasi": metode_evaluasi,
        "jenis_kontrak": jenis_kontrak,
        "jadwal": jadwal,
        "kualifikasi": {
            "sbu": sbu_codes,
            "pengalaman_min_rp": pengalaman_rp,
            "pengalaman_dalam_tahun": pengalaman_tahun,
            "modal_min_rp": modal_rp,
            "tenaga_ahli": lists.get("tenaga_ahli", []),
            "peralatan": lists.get("peralatan", []),
        },
        "dokumen_wajib": lists.get("dokumen_wajib", []),
    }
    extracted["confidence"] = _confidence(extracted)
    return extracted


def _confidence(e):
    """Skor keyakinan per kelompok field: tinggi / sedang / rendah.

    tinggi = terbaca dari label baku; sedang = terbaca sebagian;
    rendah = tidak ditemukan. Dipakai AI Insight untuk memutuskan
    pertanyaan klarifikasi aanwijzing.
    """
    def level(ok_count, total):
        if total and ok_count == total:
            return "tinggi"
        if ok_count > 0:
            return "sedang"
        return "rendah"

    identitas = [
        bool(e["nama_paket"]),
        bool(e["instansi"]),
        bool(e["nilai_hps_rp"]),
        bool(e["lokasi"]),
    ]
    jadwal_keys = ["penjelasan", "batas_pemasukan", "pembukaan", "pengumuman_pemenang"]
    jadwal_ok = sum(1 for k in jadwal_keys if k in e["jadwal"])
    kual = e["kualifikasi"]
    kual_ok = sum(
        [
            bool(kual["sbu"]),
            bool(kual["pengalaman_min_rp"]),
            bool(kual["modal_min_rp"]),
            bool(kual["tenaga_ahli"]),
            bool(kual["peralatan"]),
        ]
    )
    return {
        "identitas": level(sum(identitas), len(identitas)),
        "jadwal": level(jadwal_ok, len(jadwal_keys)),
        "kualifikasi": level(kual_ok, 5),
        "dokumen": "tinggi" if e["dokumen_wajib"] else "rendah",
        "pelaksanaan": level(sum([bool(e["jangka_waktu_hari"]), bool(e["jenis_kontrak"])]), 2),
    }
