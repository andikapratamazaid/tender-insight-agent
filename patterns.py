"""Pola kata kunci dan regex untuk dokumen tender konstruksi Indonesia.

Semua pola ditulis untuk format pengumuman pascakualifikasi yang lazim
dipakai di LPSE/SPSE: baris berlabel (Nama Paket, Nilai HPS), daftar
jadwal, dan persyaratan kualifikasi bernomor dengan sub-butir.
"""

MONTHS_ID = {
    "januari": 1,
    "februari": 2,
    "maret": 3,
    "april": 4,
    "mei": 5,
    "juni": 6,
    "juli": 7,
    "agustus": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "desember": 12,
}

# Pemetaan kata kunci pada baris jadwal -> nama field.
SCHEDULE_KEYWORDS = [
    ("penjelasan", "penjelasan"),
    ("aanwijzing", "penjelasan"),
    ("batas akhir pemasukan", "batas_pemasukan"),
    ("batas pemasukan", "batas_pemasukan"),
    ("pembukaan penawaran", "pembukaan"),
    ("masa sanggah", "masa_sanggah"),
    ("pengumuman pemenang", "pengumuman_pemenang"),
]

# Header daftar butir -> nama field.
LIST_HEADERS = [
    ("tenaga ahli yang dibutuhkan", "tenaga_ahli"),
    ("peralatan utama", "peralatan"),
    ("dokumen yang wajib dilampirkan", "dokumen_wajib"),
]
