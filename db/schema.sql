-- Skema basis data riwayat analisis Tender Insight Agent (SQLite).
-- Satu baris = satu dokumen tender yang pernah dianalisis terhadap
-- satu profil perusahaan, agar hasil antar tender dapat dibandingkan.

CREATE TABLE IF NOT EXISTS analisis_tender (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    tanggal_analisis  TEXT    NOT NULL,
    berkas            TEXT    NOT NULL,
    nama_paket        TEXT,
    instansi          TEXT,
    nilai_hps_rp      INTEGER,
    jangka_waktu_hari INTEGER,
    skor_kesiapan     INTEGER NOT NULL,
    rekomendasi       TEXT    NOT NULL,
    level_risiko      TEXT    NOT NULL,
    skor_risiko       INTEGER NOT NULL,
    jumlah_pertanyaan INTEGER NOT NULL DEFAULT 0,
    dibuat_pada       TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_analisis_rekomendasi
    ON analisis_tender (rekomendasi);

CREATE INDEX IF NOT EXISTS idx_analisis_tanggal
    ON analisis_tender (tanggal_analisis);
