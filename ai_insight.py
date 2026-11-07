"""AI Insight: pertanyaan aanwijzing dan opini kedua.

Dua keluaran yang paling dipakai tim tender dari hasil analisis:

1. Draf pertanyaan penjelasan (aanwijzing) yang disusun dari celah
   checklist, item yang kurang, dan field berconfidence rendah. Tanpa
   LLM pun daftar ini lengkap karena diturunkan dari aturan.
2. Opini kedua terstruktur (risiko utama, peluang, strategi). Bila
   TENDER_INSIGHT_LLM_API_KEY terisi, opini ditulis LLM dalam JSON;
   bila tidak, disusun dari faktor Risk Engine dan checklist.
"""

import json
import os
import urllib.request

_PERTANYAAN_ITEM = {
    "tenaga_ahli": "Apakah tenaga ahli yang belum kami miliki dapat dipenuhi melalui perjanjian dukungan atau komitmen penugasan dari pihak lain, dan dokumen apa yang harus dilampirkan sebagai buktinya?",
    "peralatan": "Apakah peralatan utama yang belum kami miliki dapat dipenuhi melalui sewa atau perjanjian dukungan peralatan, dan apakah bukti kepemilikan atau sewa harus dilampirkan pada dokumen penawaran?",
    "waktu": "Mengingat sisa waktu persiapan yang singkat, apakah ada kemungkinan perubahan jadwal pemasukan dokumen penawaran, dan melalui media apa perubahan itu diumumkan?",
}


def _missing_from_detail(detail):
    """Ambil daftar nama setelah tanda titik dua terakhir pada detail item."""
    if ":" in detail:
        tail = detail.rsplit(":", 1)[1].strip().rstrip(".")
        return [t.strip() for t in tail.split(",") if t.strip()]
    return []


def generate_questions(extracted, checklist_result):
    """Susun draf pertanyaan aanwijzing dari hasil analisis."""
    questions = []
    items = {i["item"]: i for i in checklist_result["items"]}

    dok = items.get("dokumen")
    if dok and dok["status"] != "OK":
        for nama in _missing_from_detail(dok["detail"]):
            questions.append(
                f"Terkait dokumen {nama} yang belum kami lengkapi: apakah dokumen tersebut wajib dilampirkan pada tahap penawaran, dan apakah tersedia format atau contoh resmi dari panitia?"
            )
    for key in ["tenaga_ahli", "peralatan", "waktu"]:
        item = items.get(key)
        if item and item["status"] != "OK" and key in _PERTANYAAN_ITEM:
            questions.append(_PERTANYAAN_ITEM[key])

    conf = extracted.get("confidence", {})
    if conf.get("pelaksanaan") == "rendah":
        questions.append(
            "Dokumen pengumuman tidak menyebutkan jangka waktu pelaksanaan dan jenis kontrak secara eksplisit. Mohon dikonfirmasi agar perhitungan harga dan jadwal kerja kami tepat."
        )
    if conf.get("jadwal") in ("rendah", "sedang"):
        questions.append(
            "Sebagian tanggal tahapan pemilihan belum terbaca jelas di pengumuman. Mohon dikonfirmasi jadwal lengkapnya, termasuk masa sanggah dan pengumuman pemenang."
        )
    if extracted.get("metode_evaluasi"):
        questions.append(
            f"Metode evaluasi yang tertulis adalah {extracted['metode_evaluasi']}. Mohon dikonfirmasi ambang batas dan urutan evaluasinya (administrasi, teknis, harga) agar strategi penawaran kami sesuai."
        )
    questions.append(
        "Bagaimana pola pembayaran dan termin pekerjaan ini, termasuk uang muka dan retensinya, agar dapat kami masukkan ke perencanaan arus kas penawaran?"
    )
    # Hilangkan duplikat sambil menjaga urutan.
    seen, unique = set(), []
    for q in questions:
        if q not in seen:
            seen.add(q)
            unique.append(q)
    return unique


def _rule_opinion(extracted, checklist_result, risk):
    faktor_tinggi = [f["detail"] for f in risk["faktor"] if f["level"] == "Tinggi"]
    faktor_sedang = [f["detail"] for f in risk["faktor"] if f["level"] == "Sedang"]
    risiko_utama = (faktor_tinggi + faktor_sedang)[:3] or ["Tidak ada faktor risiko menonjol pada analisis ini."]
    ok_items = [i["item"] for i in checklist_result["items"] if i["status"] == "OK"]
    peluang = []
    if "sbu" in ok_items and "pengalaman" in ok_items:
        peluang.append("Kualifikasi inti (SBU dan pengalaman) terpenuhi, posisi awal kuat untuk bersaing.")
    if risk["level"] == "Rendah":
        peluang.append("Profil risiko rendah, margin penawaran dapat dijaga tanpa cadangan risiko besar.")
    if extracted.get("metode_evaluasi") and "gugur" in extracted["metode_evaluasi"].lower():
        peluang.append("Evaluasi sistem gugur: kelengkapan dan kepatuhan dokumen lebih menentukan daripada harga terendah semata.")
    if not peluang:
        peluang.append("Peluang tetap ada bila celah kualifikasi dapat ditutup sebelum batas pemasukan.")
    strategi = []
    if checklist_result["rekomendasi"] == "NO-BID":
        strategi.append("Jangan memaksakan ikut: risiko gugur kualifikasi tinggi. Catat syaratnya dan siapkan kualifikasi untuk paket serupa berikutnya.")
    elif checklist_result["rekomendasi"] == "BID DENGAN CATATAN":
        strategi.append("Ikut dengan rencana penutupan celah yang eksplisit: tetapkan penanggung jawab dan tenggat internal untuk setiap item KURANG.")
    else:
        strategi.append("Fokus pada kualitas dokumen dan pertanyaan aanwijzing yang tajam untuk mengunci interpretasi syarat sejak awal.")
    if any(i["item"] == "waktu" and i["status"] != "OK" for i in checklist_result["items"]):
        strategi.append("Siapkan dokumen yang sudah pasti lengkap lebih dulu, kerjakan item yang kurang secara paralel.")
    return {"risiko_utama": risiko_utama, "peluang": peluang, "strategi": strategi}


def second_opinion(extracted, checklist_result, risk):
    """Opini kedua terstruktur; LLM bila dikonfigurasi, aturan bila tidak."""
    api_key = os.environ.get("TENDER_INSIGHT_LLM_API_KEY")
    if not api_key:
        return _rule_opinion(extracted, checklist_result, risk)
    base_url = os.environ.get("TENDER_INSIGHT_LLM_BASE_URL", "https://api.openai.com/v1")
    model = os.environ.get("TENDER_INSIGHT_LLM_MODEL", "gpt-4o-mini")
    facts = {
        "paket": extracted.get("nama_paket"),
        "nilai_hps_rp": extracted.get("nilai_hps_rp"),
        "skor_kesiapan": checklist_result["skor"],
        "rekomendasi": checklist_result["rekomendasi"],
        "catatan_checklist": checklist_result["alasan"],
        "level_risiko": risk["level"],
        "faktor_risiko": [f["detail"] for f in risk["faktor"]],
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "Kamu konsultan tender konstruksi. Jawab HANYA dengan JSON valid berbentuk {\"risiko_utama\": [string], \"peluang\": [string], \"strategi\": [string]}, masing-masing maksimal 3 butir Bahasa Indonesia, hanya dari fakta yang diberikan.",
            },
            {"role": "user", "content": json.dumps(facts, ensure_ascii=False)},
        ],
        "temperature": 0.2,
    }
    try:
        req = urllib.request.Request(
            base_url.rstrip("/") + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        parsed = json.loads(data["choices"][0]["message"]["content"])
        return {
            "risiko_utama": list(parsed.get("risiko_utama", []))[:3],
            "peluang": list(parsed.get("peluang", []))[:3],
            "strategi": list(parsed.get("strategi", []))[:3],
        }
    except Exception:
        return _rule_opinion(extracted, checklist_result, risk)


def build_insight(extracted, checklist_result, risk):
    return {
        "pertanyaan_aanwijzing": generate_questions(extracted, checklist_result),
        "opini_kedua": second_opinion(extracted, checklist_result, risk),
    }
