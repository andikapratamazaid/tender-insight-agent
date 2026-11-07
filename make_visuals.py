"""Buat visual README di docs/img/ dari hasil analisis yang sebenarnya.

Semua angka diambil dengan menjalankan pipeline agent atas data contoh,
bukan angka yang ditulis tangan. Membutuhkan matplotlib.

Pakai: python make_visuals.py
"""

import json
import os
from datetime import date

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from cli import analyze_file

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "docs", "img")
AD = date(2026, 11, 7)
SAMPLES = ["tender_gedung.txt", "tender_jalan.txt", "tender_irigasi.txt"]

NAVY = "#12355b"
NAVY_DARK = "#0c2743"
ORANGE = "#f59e0b"
GREEN = "#1d9e75"
RED = "#d64545"
GREY = "#8aa0b5"

plt.rcParams.update({"font.family": "DejaVu Sans", "axes.edgecolor": "#c8d4e2"})


def load_results():
    with open(os.path.join(BASE, "samples", "company_profile.json"), encoding="utf-8") as f:
        profile = json.load(f)
    results = []
    for name in SAMPLES:
        e, r, risk, ins = analyze_file(os.path.join(BASE, "samples", name), profile, AD)
        results.append((name, e, r, risk, ins))
    return results


def short_name(nama):
    return nama if len(nama) <= 42 else nama[:39] + "..."


def chart_scores(results):
    labels = [short_name(e["nama_paket"]) for _, e, _, _, _ in results][::-1]
    scores = [r["skor"] for _, _, r, _, _ in results][::-1]
    colors = [GREEN if s >= 85 else (ORANGE if s >= 60 else RED) for s in scores]
    fig, ax = plt.subplots(figsize=(9.2, 3.4))
    ax.barh(labels, scores, color=colors, height=0.55, zorder=3)
    ax.axvline(85, color=NAVY, linestyle="--", linewidth=1.4, zorder=4)
    ax.axvline(60, color=NAVY, linestyle=":", linewidth=1.4, zorder=4)
    ax.set_ylim(-0.6, 3.15)
    ax.text(85, 2.82, "Ambang BID 85", fontsize=8.5, color=NAVY, fontweight="bold", ha="center")
    ax.text(60, 2.82, "Ambang catatan 60", fontsize=8.5, color=NAVY, ha="center")
    for i, s in enumerate(scores):
        ax.text(s + 1.5, i, str(s), va="center", fontsize=11, fontweight="bold", color=NAVY_DARK)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Skor kesiapan (0-100)")
    ax.set_title("Skor Kesiapan dan Rekomendasi Tiga Tender Contoh", color=NAVY_DARK, fontsize=12.5, fontweight="bold", loc="left")
    ax.grid(axis="x", color="#e3ebf4", zorder=0)
    ax.set_axisbelow(True)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "skor-rekomendasi.png"), dpi=160)
    plt.close(fig)


def chart_checklist(results):
    items = ["sbu", "pengalaman", "modal", "tenaga_ahli", "peralatan", "dokumen", "waktu"]
    labels = ["SBU", "Pengalaman", "Modal", "Tenaga ahli", "Peralatan", "Dokumen", "Waktu"]
    bobot = [20, 20, 15, 10, 10, 15, 10]
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.6), sharey=True)
    for ax, (name, e, r, risk, ins) in zip(axes, results):
        skor = {i["item"]: i["skor"] for i in r["items"]}
        vals = [skor[k] for k in items]
        sisa = [b - v for b, v in zip(bobot, vals)]
        ax.barh(labels[::-1], vals[::-1], color=NAVY, height=0.58, zorder=3)
        ax.barh(labels[::-1], sisa[::-1], left=vals[::-1], color="#dbe4ee", height=0.58, zorder=2)
        ax.set_xlim(0, 20)
        ax.set_title(f"{short_name(e['nama_paket'])}\n{r['skor']}/100 - {r['rekomendasi']}", fontsize=9.5, color=NAVY_DARK, fontweight="bold")
        ax.grid(axis="x", color="#e3ebf4", zorder=0)
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)
    fig.suptitle("Skor per Item Checklist (batang penuh = bobot maksimum)", fontsize=12, color=NAVY_DARK, fontweight="bold", x=0.02, ha="left")
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    fig.savefig(os.path.join(OUT, "checklist-detail.png"), dpi=160)
    plt.close(fig)


def chart_timeline(results):
    stages = ["penjelasan", "batas_pemasukan", "pembukaan", "pengumuman_pemenang"]
    stage_labels = {"penjelasan": "Aanwijzing", "batas_pemasukan": "Batas pemasukan", "pembukaan": "Pembukaan", "pengumuman_pemenang": "Pengumuman"}
    colors = [NAVY, ORANGE, GREY, GREEN]
    fig, ax = plt.subplots(figsize=(9.6, 3.6))
    for row, (name, e, r, risk, ins) in enumerate(results):
        y = len(results) - 1 - row
        for stage, color in zip(stages, colors):
            if stage in e["jadwal"]:
                d = date.fromisoformat(e["jadwal"][stage])
                ax.scatter([d], [y], s=110, color=color, zorder=4, edgecolor="white", linewidth=1.2)
                ax.annotate(stage_labels[stage], (d, y), textcoords="offset points", xytext=(0, 10), ha="center", fontsize=8, color=NAVY_DARK)
        xs = [date.fromisoformat(e["jadwal"][s]) for s in stages if s in e["jadwal"]]
        if xs:
            ax.plot([min(xs), max(xs)], [y, y], color="#c8d4e2", linewidth=2, zorder=1)
    ax.set_yticks(range(len(results)))
    ax.set_yticklabels([short_name(e["nama_paket"]) for _, e, _, _, _ in results][::-1], fontsize=9.5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.set_title("Linimasa Jadwal Tiga Tender Contoh (2026)", color=NAVY_DARK, fontsize=12.5, fontweight="bold", loc="left")
    ax.grid(axis="x", color="#e3ebf4")
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "jadwal-timeline.png"), dpi=160)
    plt.close(fig)


def diagram_architecture():
    fig, ax = plt.subplots(figsize=(10.5, 3.4))
    ax.set_xlim(0, 105)
    ax.set_ylim(0, 34)
    ax.axis("off")
    boxes = [
        (1, 12, 15, 10, NAVY_DARK, "Dokumen\nTender", "white"),
        (19, 12, 19, 10, NAVY, "Ekstraksi\nDeterministik", "white"),
        (41, 20, 19, 10, NAVY, "Checklist\nBerbobot", "white"),
        (41, 3, 19, 10, "#31597f", "Risk\nEngine", "white"),
        (63, 12, 19, 10, ORANGE, "AI Insight", NAVY_DARK),
        (85, 12, 19, 10, GREEN, "Laporan +\nDashboard", "white"),
    ]
    for x, y, w, h, color, text, tcol in boxes:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=1.6", facecolor=color, edgecolor="none"))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=10.5, fontweight="bold", color=tcol)
    arrows = [((16, 17), (19, 17)), ((38, 17), (41, 22)), ((38, 15), (41, 9)), ((60, 25), (63, 19)), ((60, 8), (63, 14)), ((82, 17), (85, 17))]
    for (x1, y1), (x2, y2) in arrows:
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", color=NAVY, lw=1.6))
    ax.text(28.5, 24.5, "confidence scoring", fontsize=8, color=NAVY, ha="center", style="italic")
    ax.text(71.5, 32.8, "fuzzy matching - pertanyaan aanwijzing - opini kedua LLM", fontsize=8, color=NAVY_DARK, ha="center", style="italic")
    ax.set_title("Arsitektur Kombinasi AI Tender Insight Agent", fontsize=12.5, color=NAVY_DARK, fontweight="bold", loc="left")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "arsitektur.png"), dpi=160)
    plt.close(fig)


def main():
    os.makedirs(OUT, exist_ok=True)
    results = load_results()
    chart_scores(results)
    chart_checklist(results)
    chart_timeline(results)
    diagram_architecture()
    print("Visual ditulis ke", OUT)


if __name__ == "__main__":
    main()
