FROM python:3.12-slim

WORKDIR /app
COPY . /app

# Hanya untuk menjalankan tes dan membuat visual; inti agent murni pustaka standar.
RUN pip install --no-cache-dir pytest matplotlib

# Bawaan: analisis dokumen contoh gedung dan cetak laporannya.
CMD ["python", "cli.py", "samples/tender_gedung.txt", "--profile", "samples/company_profile.json", "--date", "2026-11-07"]
