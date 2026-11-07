"""CLI Tender Insight Agent.

Contoh:
    python cli.py samples/tender_gedung.txt --profile samples/company_profile.json
    python cli.py samples/*.txt --profile samples/company_profile.json --date 2026-11-07 --out laporan/
    python cli.py samples/tender_gedung.txt --profile samples/company_profile.json --json
"""

import argparse
import json
import os
import sys
from datetime import date

from ai_insight import build_insight
from checklist import build_checklist
from extractor import extract
from report import build_report
from risk import analyze_risk


def analyze_file(path, profile, analysis_date):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    extracted = extract(text)
    result = build_checklist(extracted, profile, analysis_date)
    risk = analyze_risk(extracted, result, analysis_date)
    insight = build_insight(extracted, result, risk)
    return extracted, result, risk, insight


def main(argv=None):
    parser = argparse.ArgumentParser(description="Tender Insight Agent: analisis bid/no-bid tender konstruksi Indonesia.")
    parser.add_argument("files", nargs="+", help="Berkas teks pengumuman tender (.txt)")
    parser.add_argument("--profile", required=True, help="Berkas JSON profil perusahaan")
    parser.add_argument("--date", default=None, help="Tanggal analisis YYYY-MM-DD (bawaan: hari ini)")
    parser.add_argument("--out", default=None, help="Folder keluaran laporan Markdown")
    parser.add_argument("--json", action="store_true", help="Cetak hasil ekstraksi + checklist sebagai JSON")
    args = parser.parse_args(argv)

    with open(args.profile, encoding="utf-8") as f:
        profile = json.load(f)
    analysis_date = date.fromisoformat(args.date) if args.date else date.today()

    if args.out:
        os.makedirs(args.out, exist_ok=True)

    payload = []
    for path in args.files:
        extracted, result, risk, insight = analyze_file(path, profile, analysis_date)
        if args.json:
            payload.append(
                {
                    "file": path,
                    "ekstraksi": extracted,
                    "checklist": result,
                    "risiko": risk,
                    "insight": insight,
                }
            )
            continue
        report = build_report(extracted, result, analysis_date, risk, insight)
        if args.out:
            name = os.path.splitext(os.path.basename(path))[0] + ".md"
            with open(os.path.join(args.out, name), "w", encoding="utf-8") as f:
                f.write(report)
        print(
            f"{os.path.basename(path)}: skor {result['skor']}/100 -> {result['rekomendasi']} "
            f"(risiko {risk['level']}, {risk['skor_risiko']}/100)"
        )
        if not args.out:
            print()
            print(report)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
