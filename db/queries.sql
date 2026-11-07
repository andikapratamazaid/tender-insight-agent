-- Contoh query rekap untuk basis data riwayat analisis tender.
-- Jalankan dengan: sqlite3 tender_insight.db < db/queries.sql

-- 1. Rekap jumlah paket per rekomendasi
SELECT rekomendasi,
       COUNT(*)        AS jumlah_paket,
       AVG(skor_kesiapan) AS rata_rata_skor
FROM analisis_tender
GROUP BY rekomendasi
ORDER BY jumlah_paket DESC;

-- 2. Sepuluh analisis terakhir
SELECT tanggal_analisis, nama_paket, skor_kesiapan, rekomendasi, level_risiko
FROM analisis_tender
ORDER BY id DESC
LIMIT 10;

-- 3. Paket berisiko tinggi yang tetap direkomendasikan ikut
SELECT nama_paket, instansi, skor_kesiapan, skor_risiko
FROM analisis_tender
WHERE level_risiko = 'Tinggi'
  AND rekomendasi LIKE 'BID%'
ORDER BY skor_risiko DESC;

-- 4. Total nilai HPS per instansi dari paket yang direkomendasikan BID
SELECT instansi,
       COUNT(*)           AS jumlah_paket,
       SUM(nilai_hps_rp)  AS total_hps
FROM analisis_tender
WHERE rekomendasi = 'BID'
GROUP BY instansi
ORDER BY total_hps DESC;
