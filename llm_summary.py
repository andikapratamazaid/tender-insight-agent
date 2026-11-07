"""Lapisan narasi ringkasan eksekutif.

Bila variabel lingkungan TENDER_INSIGHT_LLM_API_KEY terisi, narasi ditulis
oleh LLM lewat endpoint kompatibel OpenAI (URL dan model dapat diatur via
TENDER_INSIGHT_LLM_BASE_URL dan TENDER_INSIGHT_LLM_MODEL). Tanpa kunci,
atau bila panggilan gagal, narasi dibuat dari templat deterministik.
Angka tidak pernah dibuat oleh lapisan ini: narasi hanya merangkai fakta
yang sudah diekstrak dan dinilai oleh aturan.
"""

import json
import os
import urllib.request


def _template_narrative(extracted, result):
    hps = extracted.get("nilai_hps_rp")
    hps_txt = f"Rp {hps:,}".replace(",", ".") if hps else "tidak terbaca"
    kurang = [i for i in result["items"] if i["status"] != "OK"]
    if kurang:
        daftar = "; ".join(f"{i['item']}: {i['detail']}" for i in kurang)
        catatan = f"Hal yang perlu diperhatikan: {daftar}"
    else:
        catatan = "Seluruh item checklist terpenuhi."
    return (
        f"Paket {extracted.get('nama_paket') or 'tanpa nama'} dari "
        f"{extracted.get('instansi') or 'instansi tidak terbaca'} dengan nilai HPS {hps_txt} "
        f"mendapat skor kesiapan {result['skor']}/100 dan rekomendasi {result['rekomendasi']}. "
        f"{catatan}"
    )


def narrate(extracted, result):
    """Hasilkan narasi eksekutif; LLM bila dikonfigurasi, templat bila tidak."""
    api_key = os.environ.get("TENDER_INSIGHT_LLM_API_KEY")
    if not api_key:
        return _template_narrative(extracted, result)
    base_url = os.environ.get("TENDER_INSIGHT_LLM_BASE_URL", "https://api.openai.com/v1")
    model = os.environ.get("TENDER_INSIGHT_LLM_MODEL", "gpt-4o-mini")
    facts = {
        "paket": extracted.get("nama_paket"),
        "instansi": extracted.get("instansi"),
        "nilai_hps_rp": extracted.get("nilai_hps_rp"),
        "skor": result["skor"],
        "rekomendasi": result["rekomendasi"],
        "catatan": result["alasan"],
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "Kamu menulis ringkasan eksekutif Bahasa Indonesia untuk keputusan bid/no-bid tender konstruksi. Gunakan hanya fakta yang diberikan, jangan menambah angka baru. Maksimal 4 kalimat.",
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
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return _template_narrative(extracted, result)
