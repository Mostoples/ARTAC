"""Membuat diagram dokumen teknis ARTA-C + PDF dari DOKUMEN_TEKNIS_ARTA-C.md.

  python buat_dokumen.py
"""
import os
import pathlib
import re
import shutil
import subprocess

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HERE = pathlib.Path(__file__).resolve().parent
G = HERE / "gambar"
HW = HERE.parent / "hardware" / "dispenser-portable"
BLUE, ORANGE, GREEN, PURPLE, GREY, RED = "#1d4ed8", "#ea580c", "#15803d", "#7c3aed", "#475569", "#b91c1c"


def box(ax, x, y, w, h, title, sub="", color=BLUE, fs=9):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", fc="white", ec=color, lw=1.6))
    ax.add_patch(FancyBboxPatch((x, y + h - 0.32), w, 0.32, boxstyle="round,pad=0.02,rounding_size=0.12", fc=color, ec=color))
    ax.text(x + w / 2, y + h - 0.16, title, ha="center", va="center", color="white", fontsize=fs, weight="bold")
    if sub:
        ax.text(x + w / 2, y + (h - 0.32) / 2, sub, ha="center", va="center", fontsize=fs - 1.6, color="#0f172a",
                linespacing=1.35)


def arrow(ax, p, q, text="", color=GREY, both=False, style="-|>", ls="-"):
    ax.annotate("", q, p, arrowprops=dict(arrowstyle=("<|-|>" if both else style), lw=1.3, color=color, ls=ls,
                                          shrinkA=2, shrinkB=2, mutation_scale=11))
    if text:
        ax.text((p[0] + q[0]) / 2, (p[1] + q[1]) / 2 + 0.1, text, ha="center", va="bottom", fontsize=7, color=color,
                bbox=dict(fc="white", ec="none", pad=0.6))


def canvas(w, h):
    fig = plt.figure(figsize=(w, h), dpi=170)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, w); ax.set_ylim(0, h); ax.set_axis_off()
    return fig, ax


def arsitektur():
    fig, ax = canvas(12, 7.2)
    ax.text(0.3, 6.9, "Arsitektur sistem ARTA-C Portable v2", fontsize=13, weight="bold", color="#0f172a")
    box(ax, 0.3, 4.6, 2.2, 1.5, "Daya", "USB-C 5 V\nIP5306 charger+boost\nLiPo 1S 2000 mAh", ORANGE)
    box(ax, 3.4, 3.4, 3.0, 2.7, "ESP32 CYD 2,8\"", "Pengendali utama\nUI LVGL + layar sentuh\nJadwal & penghitung kantong\nWiFi -> Firebase\nI2C master (GPIO 27/22)", BLUE)
    box(ax, 7.5, 4.7, 2.0, 1.4, "PCA9685", "PWM 16 kanal\nI2C 0x40", BLUE)
    box(ax, 10.0, 5.25, 1.75, 0.85, "Servo 1", "turun wadah", GREY, 8)
    box(ax, 10.0, 4.3, 1.75, 0.85, "Servo 2", "kereta kiri-kanan", GREY, 8)
    box(ax, 10.0, 3.35, 1.75, 0.85, "Servo 3", "pelatuk", GREY, 8)
    box(ax, 7.5, 2.9, 2.0, 1.4, "MAX30102", "PPG jari, I2C 0x57\nHR, SpO2\n(TD & GD: estimasi)", PURPLE)
    box(ax, 3.4, 0.5, 3.0, 2.2, "ESP32-CAM", "Verifikasi wajah (esp-who)\nFoto bukti minum (VOT)\nDHT11 @GPIO13\nBuzzer @GPIO14", GREEN)
    box(ax, 0.3, 0.6, 2.2, 1.0, "DHT11", "suhu & kelembapan", GREEN, 8)
    box(ax, 0.3, 1.8, 2.2, 0.9, "Buzzer 5 V", "alarm jadwal", GREEN, 8)
    box(ax, 7.5, 0.5, 4.25, 1.9, "Cloud ARTA-C (Firebase)", "devices: baterai, suhu, sisa obat\ndoseLogs: status, takenAt, votStatus\nalerts: dosis terlewat, baterai, isi ulang\nWeb app: dokter / PMO / pasien", RED)
    arrow(ax, (2.5, 5.35), (3.4, 5.35), "5 V", ORANGE)
    arrow(ax, (1.4, 4.6), (4.2, 2.7), "5 V", ORANGE)
    arrow(ax, (6.4, 5.4), (7.5, 5.4), "I2C", BLUE, both=True)
    arrow(ax, (6.4, 3.7), (7.5, 3.6), "I2C", PURPLE, both=True)
    arrow(ax, (9.5, 5.6), (10.0, 5.67), "", GREY); arrow(ax, (9.5, 5.3), (10.0, 4.72), "", GREY)
    arrow(ax, (9.5, 5.0), (10.0, 3.77), "", GREY)
    arrow(ax, (4.9, 2.7), (4.9, 3.4), "ESP-NOW (nirkabel)", GREEN, both=True, ls="--")
    arrow(ax, (2.5, 1.1), (3.4, 1.1), "data", GREEN); arrow(ax, (3.4, 2.25), (2.5, 2.25), "", GREEN)
    arrow(ax, (6.4, 3.55), (7.6, 2.4), "WiFi / HTTPS", RED, both=True, ls="--")
    fig.savefig(G / "diagram_arsitektur.png", facecolor="white"); plt.close(fig)


def kabel():
    fig, ax = canvas(12, 7)
    ax.text(0.3, 6.7, "Diagram pengkabelan (wiring)", fontsize=13, weight="bold", color="#0f172a")
    rows = [("IP5306 OUT 5V", "Rel 5 V: CYD (JST 5V), PCA9685 V+, ESP32-CAM 5V, servo V+ (lewat PCA9685), buzzer", ORANGE),
            ("IP5306 BAT+/-", "LiPo 103450 3,7 V (perhatikan polaritas)", ORANGE),
            ("IP5306 USB-C IN", "Port cas di dinding kiri (5 V, ±1 A)", ORANGE),
            ("Saklar toggle", "Memutus OUT 5V IP5306 ke rel 5 V", ORANGE),
            ("Kapasitor 1000 uF", "Paralel di V+ / GND PCA9685 (peredam lonjakan servo)", ORANGE),
            ("CYD CN1 GPIO 27", "SDA -> PCA9685 SDA, MAX30102 SDA", BLUE),
            ("CYD CN1 GPIO 22", "SCL -> PCA9685 SCL, MAX30102 SCL", BLUE),
            ("CYD CN1 3V3 / GND", "VCC 3V3 PCA9685 (logika) & MAX30102; GND bersama", BLUE),
            ("PCA9685 kanal 0 / 1 / 2", "Servo 1 (wadah) / servo 2 (tuas kereta) / servo 3 (pelatuk)", GREY),
            ("ESP32-CAM GPIO 13", "DHT11 DATA (+ pull-up 10 kOhm ke 3V3 bila modul tanpa resistor)", GREEN),
            ("ESP32-CAM GPIO 14", "Resistor 1 kOhm -> basis S8050; kolektor -> buzzer (-), buzzer (+) -> 5 V", GREEN),
            ("ESP32-CAM 5V / GND", "Dari rel 5 V; GND bersama dengan CYD", GREEN),
            ("CYD <-> ESP32-CAM", "ESP-NOW (tanpa kabel data), alamat MAC dipasangkan saat setup", GREEN)]
    y = 6.2
    ax.text(0.4, y, "Dari", weight="bold", fontsize=9); ax.text(3.6, y, "Ke / keterangan", weight="bold", fontsize=9)
    for a, b, c in rows:
        y -= 0.44
        ax.add_patch(plt.Rectangle((0.3, y - 0.17), 11.4, 0.4, fc=c, alpha=0.08, ec="none"))
        ax.text(0.4, y, a, fontsize=8.6, color=c, weight="bold", va="center")
        ax.text(3.6, y, b, fontsize=8.4, va="center")
    ax.text(0.3, 0.25, "Catatan: semua GND disatukan. Servo hanya bergerak satu per satu (dibatasi firmware) agar arus puncak < 1,5 A.",
            fontsize=8, color=GREY, style="italic")
    fig.savefig(G / "diagram_kabel.png", facecolor="white"); plt.close(fig)


def alur():
    fig, ax = canvas(12, 6.2)
    ax.text(0.3, 5.9, "Alur kerja satu jadwal minum obat (state machine firmware)", fontsize=13, weight="bold", color="#0f172a")
    NL = chr(10)
    S = [("SIAGA", NL.join(["layar jam + status", "sensor tiap 5 menit"]), 0.4, 4.1, GREY),
         ("JADWAL TIBA", NL.join(["buzzer + notifikasi layar", "mulai hitung 60 menit"]), 3.3, 4.1, ORANGE),
         ("VERIFIKASI WAJAH", NL.join(["ESP32-CAM cocokkan wajah", "maks 3x percobaan"]), 6.2, 4.1, GREEN),
         ("CEK PPG JARI", NL.join(["MAX30102 +/-15 detik", "HR, SpO2 (+ estimasi)"]), 9.1, 4.1, PURPLE),
         ("DOSIS TERLEWAT", NL.join(["status missed + alert PMO", "(eskalasi 15/30/60 mnt)", "-> kembali SIAGA"]), 0.4, 1.5, RED),
         ("BLISTER HABIS?", NL.join(["pillsLeft = 0 -> alert", "'isi ulang' ke PMO", "-> kembali SIAGA"]), 3.3, 1.5, ORANGE),
         ("CATAT", NL.join(["doseLogs: status taken,", "method dispenser, votStatus", "kurangi pillsLeft"]), 6.2, 1.5, RED),
         ("KELUARKAN OBAT", NL.join(["tiap kaplet: servo 2 ke kolom,", "servo 3 patuk; kolom habis ->", "servo 1 turun 1 baris"]), 9.1, 1.5, BLUE)]
    pos = {}
    for t, sub, x, y, c in S:
        box(ax, x, y, 2.6, 1.45, t, sub, c, 8.5)
        pos[t] = (x, y)

    def c(t, side):
        x, y = pos[t]
        return {"r": (x + 2.6, y + 0.72), "l": (x, y + 0.72), "t": (x + 1.3, y + 1.45), "b": (x + 1.3, y)}[side]
    arrow(ax, c("SIAGA", "r"), c("JADWAL TIBA", "l"), "jadwal")
    arrow(ax, c("JADWAL TIBA", "r"), c("VERIFIKASI WAJAH", "l"), "pasien datang")
    arrow(ax, c("VERIFIKASI WAJAH", "r"), c("CEK PPG JARI", "l"), "cocok")
    arrow(ax, c("CEK PPG JARI", "b"), c("KELUARKAN OBAT", "t"), "selesai / dilewati")
    arrow(ax, c("KELUARKAN OBAT", "l"), c("CATAT", "r"), "sukses")
    arrow(ax, c("CATAT", "l"), c("BLISTER HABIS?", "r"))
    arrow(ax, (3.6, 4.1), c("DOSIS TERLEWAT", "t"), NL.join(["timeout 60 mnt atau", "3x gagal verifikasi"]), RED, ls="--")
    ax.text(10.4, 1.05, NL.join(["macet / kaplet tidak turun -> servo berhenti,", "alert 'periksa alat' ke PMO"]), fontsize=7.2,
            color=RED, ha="center", va="top")
    fig.savefig(G / "diagram_alur_dosis.png", facecolor="white"); plt.close(fig)


def daya():
    loads = [("CYD (layar menyala)", 180), ("ESP32-CAM (aktif)", 200), ("PCA9685 + logika", 15), ("MAX30102 (LED)", 20),
             ("DHT11", 2), ("Buzzer", 30), ("1 servo MG90S bergerak", 450)]
    fig, ax = plt.subplots(figsize=(8, 3.6), dpi=170)
    names = [a for a, _ in loads][::-1]; vals = [b for _, b in loads][::-1]
    ax.barh(names, vals, color=[ORANGE if "servo" in n else BLUE for n in names])
    for i, v in enumerate(vals):
        ax.text(v + 8, i, f"{v} mA", va="center", fontsize=8)
    ax.set_xlabel("Arus tipikal di 5 V (mA)"); ax.set_xlim(0, 560)
    ax.set_title("Anggaran arus per komponen (perkiraan)", fontsize=11, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(G / "diagram_daya.png", facecolor="white"); plt.close(fig)


def salin_gambar():
    r = HW / "render"
    for f in ("00_muka_depan_kamera_sensor.png", "03_wadah_dimasukkan_seperti_roti.png", "04_pelatuk_mematuk.png",
              "05_kaplet_keluar_ke_belakang.png", "06_obat_di_baki.png", "07_gambar_urai_berlabel.png", "08_cek_jari_ppg.png",
              "02_blister_masuk_wadah.png"):
        if (r / f).exists():
            shutil.copy(r / f, G / f)
    for f in ("GT-01_rakitan.png", "GT-02_gambar_urai.png"):
        p = HW / "gambar_teknik" / f
        if p.exists():
            shutil.copy(p, G / f)


CSS = """
@page { size: A4; margin: 18mm 16mm 18mm 16mm; }
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 10pt; color: #1e293b; line-height: 1.5; }
h1 { font-size: 19pt; color: #1d4ed8; margin: 0 0 2mm; break-before: page; }
h1:first-of-type { break-before: auto; }
h2 { font-size: 13pt; color: #1d4ed8; border-bottom: 2px solid #bfdbfe; padding-bottom: 1mm; margin-top: 6mm; break-after: avoid; }
h3 { font-size: 11pt; color: #0f172a; margin-top: 4mm; break-after: avoid; }
table { border-collapse: collapse; width: 100%; margin: 2mm 0 4mm; font-size: 8.6pt; }
tr { break-inside: avoid; }
th { background: #1d4ed8; color: #fff; text-align: left; padding: 1.4mm 2mm; }
td { border-bottom: 1px solid #e2e8f0; padding: 1.2mm 2mm; vertical-align: top; }
tr:nth-child(even) td { background: #f8fafc; }
img { max-width: 100%; display: block; margin: 2mm auto 1mm; break-inside: avoid; }
code { background: #eef2ff; padding: 0 1mm; border-radius: 2px; font-size: 8.6pt; }
pre { background: #f1f5f9; padding: 3mm; border-radius: 2mm; font-size: 8.2pt; white-space: pre-wrap; break-inside: avoid; }
blockquote { background: #fff7ed; border-left: 4px solid #f59e0b; margin: 3mm 0; padding: 2mm 4mm; }
em { color: #475569; }
.cover { height: 250mm; display: flex; flex-direction: column; justify-content: center; text-align: center; break-after: page; }
.cover h1 { font-size: 30pt; break-before: auto; }
.cover .sub { font-size: 14pt; color: #475569; }
.cover img { width: 92%; border-radius: 4mm; margin-top: 8mm; }
.cover table { width: 70%; margin: 8mm auto 0; font-size: 9pt; }
"""


def pdf():
    import markdown
    md = (HERE / "DOKUMEN_TEKNIS_ARTA-C.md").read_text(encoding="utf-8")
    md = "\n".join(("    " + l[3:]) if l.startswith("   - ") else l for l in md.split("\n"))
    head, body = md.split("<!-- ISI -->", 1)
    html_head = markdown.markdown(head, extensions=["tables"])
    html_body = markdown.markdown(body, extensions=["tables", "fenced_code", "sane_lists", "toc"])
    html = (f"<!doctype html><html lang='id'><head><meta charset='utf-8'><title>Dokumen Teknis ARTA-C</title>"
            f"<style>{CSS}</style></head><body><div class='cover'>{html_head}</div>{html_body}</body></html>")
    base = HERE.as_uri() + "/"
    html = re.sub(r'src="(?!http|file)([^"]+)"', lambda m: f'src="{base}{m.group(1)}"', html)
    p = HERE / "_dokumen.html"
    p.write_text(html, encoding="utf-8")
    exe = next(e for e in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                           r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe") if os.path.exists(e))
    out = HERE / "DOKUMEN_TEKNIS_ARTA-C.pdf"
    subprocess.run([exe, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={out}", p.as_uri()],
                   check=True, capture_output=True, timeout=180)
    p.unlink()
    print("PDF:", out, out.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    G.mkdir(exist_ok=True)
    arsitektur(); kabel(); alur(); daya(); salin_gambar()
    print("diagram selesai")
    if (HERE / "DOKUMEN_TEKNIS_ARTA-C.md").exists():
        pdf()
