#!/usr/bin/env bash
# Demo satu perintah Tender Insight Agent:
# evaluasi ekstraksi, seluruh tes, laporan contoh, visual, dan data dashboard.
set -e
cd "$(dirname "$0")/.."

echo "== 1/5 Evaluasi akurasi ekstraksi =="
python3 run_eval.py

echo
echo "== 2/5 Tes otomatis =="
python3 -m pytest -q

echo
echo "== 3/5 Laporan contoh (Markdown) =="
python3 cli.py samples/tender_gedung.txt samples/tender_jalan.txt samples/tender_irigasi.txt \
  --profile samples/company_profile.json --date 2026-11-07 --out laporan-contoh/

echo
echo "== 4/5 Visual untuk README =="
python3 make_visuals.py

echo
echo "== 5/5 Data dashboard =="
python3 build_dashboard_data.py

echo
echo "Selesai. Buka dashboard/index.html di browser untuk melihat dashboardnya."
