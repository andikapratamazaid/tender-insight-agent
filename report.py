"""Pembuat laporan Markdown dari hasil ekstraksi dan checklist."""

from datetime import date

from llm_summary import narrate

JADWAL_LABEL = {
    "penjelasan": "Penjelasan (Aanwijzing)",
    "batas_pemasukan": "Batas Akhir Pemasukan Penawaran",
    "pembukaan": "Pembukaan Penawaran",
    "masa_sanggah": "Masa Sanggah (mulai)",
    "pengumuman_pemenang": "Pengumuman Pemenang",
}

ITEM_LABEL = {
    "sbu": "SBU sesuai bidang",
    "pengalaman": "Pengalaman sejenis",
    "modal": "Modal disetor",
    "tenaga_ahli": "Tenaga ahli",
    "peralatan": "Peralatan utama",
    "dokumen": "Dokumen wajib",
    "waktu": "Waktu persiapan",
}


def _rp(value):
    return f"Rp {value:,}".replace(",", ".") if value else "-"


def build_report(extracted, result, analysis_date, risk=None, insight=None):
    """Susun laporan Markdown lengkap untuk satu dokumen tender."""
    lines = []
    lines.append(f"# Tender Insight: {extracted.get('nama_paket') or 'Paket Tanpa Nama'}")
    lines.append("")
    lines.append(f"Tanggal analisis: {analysis_date.isoformat()}")
    lines.append("")
    lines.append("## Ringkasan Eksekutif")
    lines.append("")
    lines.append(narrate(extracted, result))
    lines.append("")
    lines.append("## Identitas Paket")
    lines.append("")
    lines.append(f"- Instansi: {extracted.get('instansi') or '-'}")
    lines.append(f"- Lokasi: {extracted.get('lokasi') or '-'}")
    lines.append(f"- Nilai HPS: {_rp(extracted.get('nilai_hps_rp'))}")
    lines.append(f"- Tahun Anggaran: {extracted.get('tahun_anggaran') or '-'}")
    lines.append(f"- Sumber Dana: {extracted.get('sumber_dana') or '-'}")
    lines.append(f"- Jangka Waktu Pelaksanaan: {extracted.get('jangka_waktu_hari') or '-'} hari kalender")
    lines.append(f"- Metode Evaluasi: {extracted.get('metode_evaluasi') or '-'}")
    lines.append(f"- Jenis Kontrak: {extracted.get('jenis_kontrak') or '-'}")
    conf = extracted.get("confidence", {})
    if conf:
        lines.append(
            "- Keyakinan ekstraksi: "
            + ", ".join(f"{k} {v}" for k, v in conf.items())
        )
    lines.append("")
    lines.append("## Jadwal Kritis")
    lines.append("")
    jadwal = extracted.get("jadwal", {})
    if jadwal:
        lines.append("| Tahap | Tanggal | Sisa Hari |")
        lines.append("|---|---|---|")
        for key in ["penjelasan", "batas_pemasukan", "pembukaan", "masa_sanggah", "pengumuman_pemenang"]:
            if key in jadwal:
                d = date.fromisoformat(jadwal[key])
                sisa = (d - analysis_date).days
                lines.append(f"| {JADWAL_LABEL[key]} | {jadwal[key]} | {sisa} |")
    else:
        lines.append("Jadwal tidak terbaca dari dokumen.")
    lines.append("")
    lines.append("## Syarat Kualifikasi Terdeteksi")
    lines.append("")
    kual = extracted.get("kualifikasi", {})
    lines.append(f"- SBU: {', '.join(kual.get('sbu', [])) or '-'}")
    lines.append(
        f"- Pengalaman minimum: {_rp(kual.get('pengalaman_min_rp'))}"
        + (f" dalam {kual['pengalaman_dalam_tahun']} tahun terakhir" if kual.get("pengalaman_dalam_tahun") else "")
    )
    lines.append(f"- Modal disetor minimum: {_rp(kual.get('modal_min_rp'))}")
    lines.append(f"- Tenaga ahli: {', '.join(kual.get('tenaga_ahli', [])) or '-'}")
    lines.append(f"- Peralatan: {', '.join(kual.get('peralatan', [])) or '-'}")
    lines.append(f"- Dokumen wajib: {', '.join(extracted.get('dokumen_wajib', [])) or '-'}")
    lines.append("")
    lines.append("## Checklist Kesiapan")
    lines.append("")
    lines.append("| Item | Status | Bobot | Skor | Keterangan |")
    lines.append("|---|---|---|---|---|")
    for item in result["items"]:
        lines.append(
            f"| {ITEM_LABEL.get(item['item'], item['item'])} | {item['status']} | {item['bobot']} | {item['skor']} | {item['detail']} |"
        )
    lines.append("")
    lines.append(f"**Skor total: {result['skor']}/100**")
    lines.append("")
    lines.append(f"## Rekomendasi: {result['rekomendasi']}")
    lines.append("")
    if result["alasan"]:
        lines.append("Catatan yang mendasari rekomendasi:")
        for alasan in result["alasan"]:
            lines.append(f"- {alasan}")
    else:
        lines.append("Tidak ada catatan: seluruh syarat terpenuhi.")
    lines.append("")
    if risk:
        lines.append("## Analisis Risiko")
        lines.append("")
        lines.append(f"**Level risiko: {risk['level']} (skor risiko {risk['skor_risiko']}/100)**")
        lines.append("")
        lines.append("| Faktor | Level | Poin | Keterangan |")
        lines.append("|---|---|---|---|")
        for f in risk["faktor"]:
            lines.append(f"| {f['faktor']} | {f['level']} | {f['poin']} | {f['detail']} |")
        lines.append("")
    if insight:
        lines.append("## AI Insight")
        lines.append("")
        lines.append("### Draf Pertanyaan Aanwijzing")
        lines.append("")
        for n, q in enumerate(insight["pertanyaan_aanwijzing"], 1):
            lines.append(f"{n}. {q}")
        lines.append("")
        lines.append("### Opini Kedua")
        lines.append("")
        opini = insight["opini_kedua"]
        lines.append("Risiko utama:")
        for r in opini["risiko_utama"]:
            lines.append(f"- {r}")
        lines.append("")
        lines.append("Peluang:")
        for p in opini["peluang"]:
            lines.append(f"- {p}")
        lines.append("")
        lines.append("Strategi:")
        for s in opini["strategi"]:
            lines.append(f"- {s}")
        lines.append("")
    return "\n".join(lines)
