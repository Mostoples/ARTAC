"""PANDUAN_CETAK.md & PANDUAN_RAKIT.md -> PDF (HTML + Chrome headless), lalu bundel ZIP berisi STL + panduan.

  python make_pdf.py
"""
import os
import re
import pathlib
import subprocess
import zipfile

import markdown

HERE = pathlib.Path(__file__).resolve().parent
CHROME = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
          r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"]

CSS = """
@page { size: A4; margin: 16mm 15mm 18mm 15mm; }
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 10pt; color: #1e293b; line-height: 1.45; }
h1 { font-size: 20pt; color: #1d4ed8; margin: 0 0 4mm; }
h2 { font-size: 13.5pt; color: #1d4ed8; border-bottom: 2px solid #bfdbfe; padding-bottom: 1.5mm; margin-top: 7mm;
     break-after: avoid; }
table { border-collapse: collapse; width: 100%; margin: 2.5mm 0 4mm; font-size: 8.8pt; break-inside: auto; }
tr { break-inside: avoid; }
th { background: #1d4ed8; color: white; text-align: left; padding: 1.6mm 2mm; }
td { border-bottom: 1px solid #e2e8f0; padding: 1.4mm 2mm; vertical-align: top; }
tr:nth-child(even) td { background: #f8fafc; }
code { background: #eef2ff; padding: 0 1mm; border-radius: 2px; font-size: 8.8pt; }
blockquote { background: #fff7ed; border-left: 4px solid #f59e0b; margin: 3mm 0; padding: 2mm 4mm; }
a { color: #1d4ed8; text-decoration: none; }
.cover { height: 255mm; display: flex; flex-direction: column; justify-content: center; text-align: center;
         break-after: page; }
.cover h1 { font-size: 30pt; margin-bottom: 2mm; }
.cover .sub { font-size: 14pt; color: #475569; margin-bottom: 8mm; }
.cover img { width: 100%; border-radius: 4mm; box-shadow: 0 2mm 6mm rgba(0,0,0,.15); }
.cover .meta { margin-top: 8mm; color: #64748b; font-size: 10pt; }
h3 { font-size: 11.5pt; color: #1e3a8a; margin: 5mm 0 1.5mm; break-after: avoid; }
p > img { display: block; max-width: 100%; max-height: 105mm; margin: 1mm auto 2mm; border-radius: 2mm; }
.gallery { break-before: page; }
.gallery img { width: 49%; margin-bottom: 2mm; border-radius: 2mm; }
.gallery p { font-size: 8.5pt; color: #64748b; }
"""


def build_html(src="PANDUAN_CETAK.md"):
    md = (HERE / src).read_text(encoding="utf-8")
    md = md.split("\n", 1)[1]                                 # judul dipindah ke sampul
    md = "\n".join(("    " + l[3:]) if l.startswith("   - ") else l for l in md.split("\n"))   # sub-daftar
    body = markdown.markdown(md, extensions=["tables", "fenced_code", "sane_lists"])
    body = re.sub(r"<thead>\s*<tr>\s*(<th></th>\s*)+</tr>\s*</thead>", "", body)       # tabel tanpa judul
    r = (HERE / "render").as_uri()
    cover = f"""<div class="cover">
      <h1>Panduan Cetak 3D</h1>
      <div class="sub">ARTA-C Portable v2: dispenser obat TB konsep "pemanggang roti"</div>
      <img src="{r}/03_wadah_dimasukkan_seperti_roti.png">
      <div class="meta">34 file STL &middot; &plusmn;595 g filamen &middot; untuk Bambu Lab A1 mini (180 &times; 180 mm)<br>
      File STL ada di folder <b>stl/</b> dalam ZIP ini</div></div>"""
    gallery = f"""<div class="gallery"><h2>Gambaran hasil akhir</h2>
      <img src="{r}/00_muka_depan_kamera_sensor.png"> <img src="{r}/02_blister_masuk_wadah.png">
      <img src="{r}/04_pelatuk_mematuk.png"> <img src="{r}/05_kaplet_keluar_ke_belakang.png">
      <p>Kiri atas: muka depan (kamera, buzzer, layar, sensor jari, ventilasi DHT11). Kanan atas: blister dijepit di wadah. Kiri bawah: kereta pelatuk mematuk kubah.
      Kanan bawah: kaplet keluar lewat foil ke belakang lalu meluncur ke baki.</p></div>"""
    html = f"<!doctype html><html lang='id'><head><meta charset='utf-8'><title>Panduan Cetak ARTA-C</title>" \
           f"<style>{CSS}</style></head><body>{cover}{body}{gallery}</body></html>"
    if src == "PANDUAN_RAKIT.md":
        rk = (HERE / "rakit").as_uri()
        body = body.replace('src="rakit/', f'src="{rk}/')
        cover = f"""<div class="cover">
      <h1>Panduan Merakit</h1>
      <div class="sub">ARTA-C Portable v2: dispenser obat TB konsep "pemanggang roti"</div>
      <img src="{rk}/langkah_09.png">
      <div class="meta">9 langkah bergambar &middot; elektronik &amp; kabel &middot; kalibrasi servo &middot; uji akhir<br>
      Versi blister 104 &times; 180 mm, kaplet miring 45&deg; &middot; 2026-11-24</div></div>"""
        html = (f"<!doctype html><html lang='id'><head><meta charset='utf-8'><title>Panduan Rakit ARTA-C</title>"
                f"<style>{CSS}</style></head><body>{cover}{body}</body></html>")
    out = HERE / "_anim_tmp" / src.replace(".md", ".html")
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


def to_pdf(html, pdf):
    exe = next(p for p in CHROME if os.path.exists(p))
    subprocess.run([exe, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", html.as_uri()], check=True, capture_output=True, timeout=120)


def bundle(pdf, pdf_rakit=None):
    zp = HERE / "ARTA-C_Portable_v2_STL.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(pdf, "PANDUAN_CETAK.pdf")
        z.write(HERE / "PANDUAN_CETAK.md", "PANDUAN_CETAK.md")
        z.write(HERE / "README.md", "README.md")
        if pdf_rakit:
            z.write(pdf_rakit, "PANDUAN_RAKIT.pdf")
            z.write(HERE / "PANDUAN_RAKIT.md", "PANDUAN_RAKIT.md")
            for f in sorted((HERE / "rakit").glob("*.png")):
                z.write(f, f"rakit/{f.name}")
        gt = HERE / "gambar_teknik" / "GT_ARTA-C_Portable_v2.pdf"
        if gt.exists():
            z.write(gt, "GAMBAR_TEKNIK_ARTA-C_Portable_v2.pdf")
        for f in sorted((HERE / "stl").glob("*.stl")):
            z.write(f, f"stl/{f.name}")
    return zp


if __name__ == "__main__":
    pdf = HERE / "PANDUAN_CETAK.pdf"
    to_pdf(build_html(), pdf)
    pr = HERE / "PANDUAN_RAKIT.pdf"
    to_pdf(build_html("PANDUAN_RAKIT.md"), pr)
    zp = bundle(pdf, pr)
    print(pr, pr.stat().st_size // 1024, "KB")
    print(pdf, pdf.stat().st_size // 1024, "KB")
    print(zp, zp.stat().st_size // 1024, "KB")
