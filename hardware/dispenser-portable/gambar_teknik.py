"""Gambar teknik ARTA-C Portable v2 -> gambar_teknik/GT_ARTA-C_Portable_v2.pdf (A3, proyeksi Eropa / ISO-E).

Garis pandangan dirender Blender Freestyle dari mesh asli (garis tampak tebal, garis tersembunyi putus-putus),
lalu disusun dengan matplotlib: skala sejati, dimensi, kop gambar, gambar urai + daftar part.

  python gambar_teknik.py
"""
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, "_gt_tmp")
OUTD = os.path.join(HERE, "gambar_teknik")
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
PPM = 8.0                                   # piksel per mm pada render pandangan
DATE = "2026-11-24"

# nama, fungsi, jumlah, bahan
INFO = {
    "dinding_depan": ("Dinding depan", "Muka alat: jendela layar, kamera, buzzer, ventilasi, baki", 1, "PLA"),
    "dinding_belakang": ("Dinding belakang", "Alas rakit semua modul", 1, "PLA"),
    "dinding_atas": ("Dinding atas", "Celah masuk wadah", 1, "PLA"),
    "dinding_bawah": ("Dinding bawah", "", 1, "PLA"),
    "dinding_kiri": ("Dinding kiri", "Port USB-C cas + saklar", 1, "PLA"),
    "dinding_kanan": ("Dinding kanan", "", 1, "PLA"),
    "blok_sudut": ("Blok sudut", "Pengikat dinding M3", 4, "PLA"),
    "rel_kereta": ("Rel kereta", "Jalur kereta pelatuk", 1, "PLA"),
    "kereta": ("Kereta pelatuk", "Membawa servo 3 + pelatuk", 1, "PETG"),
    "pelatuk": ("Pelatuk", "Menekan kubah blister (scotch-yoke)", 1, "PETG"),
    "engkol_servo3": ("Engkol servo 3", "r = 6,3 mm, langkah 12,6 mm", 1, "PETG"),
    "tuas_servo2": ("Tuas servo 2", "Menggeser kereta, L = 113 mm", 1, "PETG"),
    "braket_servo2": ("Braket servo 2", "", 1, "PLA"),
    "braket_servo1": ("Braket servo 1", "", 1, "PLA"),
    "gear_G1": ("Roda gigi G1", "m1, z40, sudut tekan 20 deg", 1, "PETG"),
    "gear_G2": ("Roda gigi G2", "m1, z36 / z12 (majemuk)", 1, "PETG"),
    "spacer_G2": ("Spacer G2", "Poros baut M3", 1, "PETG"),
    "pemandu_kiri": ("Pemandu kiri", "Jalur wadah (sisi rack)", 1, "PLA"),
    "pemandu_kanan": ("Pemandu kanan", "Jalur wadah", 1, "PLA"),
    "landasan": ("Landasan", "Penahan dorongan + celah keluar kaplet", 1, "PLA"),
    "corong_baki": ("Corong & baki", "Lantai luncur + baki ambil", 1, "PLA"),
    "klem_layar": ("Klem layar", "Penjepit CYD 2,8 in", 2, "PLA"),
    "wadah_belakang": ("Wadah belakang", "Pemegang blister + rack m1", 1, "PLA"),
    "wadah_depan": ("Wadah depan", "Bingkai penjepit blister", 1, "PLA"),
    "kantong_jari_ppg": ("Kantong jari PPG", "Terowongan jari, MAX30102 di lantai", 1, "PLA hitam"),
}


DETAIL = {   # data rinci yang dicantumkan di catatan gambar
    "gear_G1": ["Data roda gigi: modul m = 1, z = 40, sudut tekan 20 deg", "d pitch = 40,0; d luar = 42,0; lebar gigi = 5,0",
                "Lubang spline servo MG90S Ø4,7 (tekan)"],
    "gear_G2": ["Roda gigi majemuk: z36 (d pitch 36,0, d luar 38,0, lebar 5,0)", "+ z12 (d pitch 12,0, d luar 14,0)",
                "Lubang poros Ø3,4 untuk baut M3", "Rasio total servo 1 ke rack: 60 mm/rad"],
    "wadah_belakang": ["Blister 104 x 180; kantong 4 x 7, jarak pusat 22,35 (h) x 21,85 (v)", "Lubang kaplet 23,0 x 13,0 miring 45 deg",
                       "Rack vertikal m = 1 di sisi kiri, panjang 180", "Pegangan 40 x 9 R4,4"],
    "wadah_depan": ["Jendela kubah 23,5 x 13,5 miring 45 deg, jarak pusat 22,35 x 21,85", "6 lubang M2 ke wadah belakang"],
    "kantong_jari_ppg": ["Lubang jari Ø19 x 35 dalam, bibir masuk Ø24", "Jendela sensor 6 x 8 di lantai, 2-10 mm dari ujung lubang (bantalan ujung jari)",
                         "Kantong papan MAX30102 16 x 16, terbuka ke bawah", "4 baut M3 + mur ke dinding depan; cetak PLA hitam"],
    "pelatuk": ["Bantalan dorong 16,5 x 7 miring 45 deg (sejajar kaplet)", "Slot yoke 16,2 x 3,5 untuk pin engkol Ø3"],
    "engkol_servo3": ["Radius engkol 6,3 (langkah pelatuk 12,6)", "Pin Ø3,0; lubang spline MG90S Ø4,7"],
    "tuas_servo2": ["Panjang lengan 133 (sumbu servo ke pin)", "Pin Ø3,0 masuk slot kereta"],
    "dinding_kiri": ["Lubang port USB-C 10,0 x 4,6", "Lubang saklar Ø6,2"],
    "dinding_depan": ["Jendela layar 60 x 46; lensa kamera Ø9; 5 lubang buzzer Ø2",
                      "Ventilasi DHT11 5 x (1,6 x 10); bukaan baki 30 x 22"],
    "dinding_atas": ["Celah wadah 118,2 x 6,6"],
}


# ------------------------------------------------------------------ data (python biasa)
def parts_device():
    sys.path.insert(0, HERE)
    import build as b
    cb = b.cb_at(1)
    w = b.walls_placed()
    p = {k: w[k] for k in w}
    p.update({"blok_sudut": b.union([b.part_blok(n) for n in b.CORNERS]), "rel_kereta": b.part_rel(),
              "kereta": b.kereta(b.XC), "pelatuk": b.pelatuk(b.XC), "engkol_servo3": b.engkol3(b.XC),
              "tuas_servo2": b.part_tuas(), "braket_servo2": b.part_braket_s2(), "braket_servo1": b.part_braket_s1(),
              "gear_G1": b.part_g1(), "gear_G2": b.part_g2(), "spacer_G2": b.part_spacer_g2(),
              "pemandu_kiri": b.part_pemandu_kiri(), "pemandu_kanan": b.part_pemandu_kanan(),
              "landasan": b.part_landasan(), "corong_baki": b.part_corong(),
              "klem_layar": b.part_klem_layar(True) + b.part_klem_layar(False),
              "wadah_belakang": b.wadah_belakang(cb), "wadah_depan": b.wadah_depan(cb),
              "kantong_jari_ppg": b.part_kantong_jari()})
    return b, p


EXPLODE = {   # arah urai (mm) gambar urai / video
    "dinding_depan": (0, -170, 0), "dinding_belakang": (0, 170, 0), "dinding_atas": (0, 0, 150),
    "dinding_bawah": (0, 0, -110), "dinding_kiri": (-150, 0, 0), "dinding_kanan": (150, 0, 0),
    "kantong_jari_ppg": (0, -250, -30), "blok_sudut": (0, 60, 0), "rel_kereta": (0, -95, 40),
    "kereta": (0, -120, 15), "pelatuk": (0, -150, 25), "engkol_servo3": (0, -135, 5), "tuas_servo2": (0, -90, -40),
    "braket_servo2": (0, 60, -60), "braket_servo1": (-60, 70, 0), "gear_G1": (-75, -60, -10),
    "gear_G2": (-85, -20, 30), "spacer_G2": (-85, 50, 30), "pemandu_kiri": (-40, 40, 0),
    "pemandu_kanan": (60, 40, 0), "landasan": (0, 110, 10), "corong_baki": (40, 30, -80),
    "klem_layar": (0, -60, -20), "wadah_belakang": (0, 30, 175), "wadah_depan": (0, -40, 175),
}


def prepare():
    import trimesh
    b, parts = parts_device()
    os.makedirs(TMP, exist_ok=True)
    for f in os.listdir(TMP):
        if f.endswith(".stl"):
            os.remove(os.path.join(TMP, f))
    meta = {}
    for name, m in parts.items():
        t = b.to_tm(m)
        t.export(os.path.join(TMP, f"{name}.stl"))
        meta[name] = dict(bounds=t.bounds.tolist(), vol=t.volume / 1000)
    dm = [m for k, m in b.dummies()]
    b.to_tm(b.union(dm)).export(os.path.join(TMP, "_elektronik.stl"))
    json.dump(dict(meta=meta, explode=EXPLODE), open(os.path.join(TMP, "meta.json"), "w"))
    return b, meta


# ------------------------------------------------------------------ Blender
VIEWS = {   # arah pandang (lokasi kamera relatif pusat) & sumbu tegak
    "depan": ((0, -1, 0), (0, 0, 1)), "atas": ((0, 0, 1), (0, 1, 0)), "kiri": ((-1, 0, 0), (0, 0, 1)),
    "iso": ((0.62, -1.0, 0.55), (0, 0, 1)), "iso_back": ((-0.75, 1.0, 0.6), (0, 0, 1)),
}


def blender_main(jobs_path):
    import bpy
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector

    jobs = json.load(open(jobs_path))
    results = {}
    for job in jobs:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        sc = bpy.context.scene
        sc.render.engine = "BLENDER_EEVEE"
        sc.view_settings.view_transform = "Standard"
        sc.render.film_transparent = False
        w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
        w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
        w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
        shaded = job.get("shaded", False)
        objs = []
        for item in job["items"]:
            bpy.ops.wm.stl_import(filepath=item["stl"])
            o = bpy.context.selected_objects[0]
            o.location = item.get("offset", (0, 0, 0))
            m = bpy.data.materials.new("m"); m.use_nodes = True
            nt = m.node_tree
            if shaded:
                p = nt.nodes["Principled BSDF"]
                p.inputs["Base Color"].default_value = (*item.get("color", (0.82, 0.88, 0.96)), 1)
                p.inputs["Roughness"].default_value = 0.6
            else:
                nt.nodes.clear()
                em = nt.nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = (1, 1, 1, 1)
                out = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(em.outputs[0], out.inputs[0])
            o.data.materials.append(m)
            objs.append((item.get("name", ""), o))
        if shaded:
            bpy.ops.object.light_add(type="SUN", rotation=(math.radians(40), math.radians(10), math.radians(-35)))
            bpy.context.object.data.energy = 2.6
            w.node_tree.nodes["Background"].inputs[1].default_value = 0.8
            sc.view_settings.view_transform = "AgX"
            sc.render.film_transparent = True
        sc.render.use_freestyle = True
        sc.render.line_thickness_mode = "ABSOLUTE"
        fs = bpy.context.view_layer.freestyle_settings
        fs.crease_angle = math.radians(140)
        ls = fs.linesets[0] if len(fs.linesets) else fs.linesets.new("visible")
        if ls.linestyle is None:
            ls.linestyle = bpy.data.linestyles.new("vis")
        ls.select_by_visibility = True; ls.visibility = "VISIBLE"
        ls.select_silhouette = ls.select_border = ls.select_crease = True
        ls.linestyle.thickness = job.get("thick", 2.0)
        ls.linestyle.color = (0, 0, 0)
        if job.get("hidden"):
            l2 = fs.linesets.new("hidden")
            l2.select_by_visibility = True; l2.visibility = "HIDDEN"
            l2.select_silhouette = l2.select_border = l2.select_crease = True
            st = bpy.data.linestyles.new("hid"); l2.linestyle = st
            st.thickness = 1.0; st.color = (0.45, 0.45, 0.45)
            st.use_dashed_line = True; st.dash1 = 7; st.gap1 = 5
        # kamera ortografis
        lo, hi = Vector(job["bounds"][0]), Vector(job["bounds"][1])
        c = (lo + hi) / 2
        d, up = VIEWS[job["view"]]
        d = Vector(d).normalized()
        bpy.ops.object.camera_add(location=c + d * 2000)
        cam = bpy.context.object; sc.camera = cam
        cam.rotation_euler = (-d).to_track_quat("-Z", "Y" if job["view"] != "atas" else "Y").to_euler()
        if job["view"] == "atas":
            cam.rotation_euler = (0, 0, 0)
        cam.data.type = "ORTHO"; cam.data.clip_end = 5000
        cam.data.ortho_scale = job["ortho"]
        sc.render.resolution_x, sc.render.resolution_y = job["res"]
        sc.render.filepath = job["out"]
        bpy.ops.render.render(write_still=True)
        if job.get("anchors"):
            sc.frame_set(0)
            an = {}
            for name, o in objs:
                if not name:
                    continue
                vs = o.data.vertices
                pts = [o.matrix_world @ Vector(vs[i].co) for i in range(0, len(vs), max(1, len(vs) // 60))]
                ctr = sum(pts, Vector()) / len(pts)
                p = world_to_camera_view(sc, cam, ctr)
                an[name] = (p.x, p.y)
            results[job["out"]] = an
    json.dump(results, open(os.path.join(os.path.dirname(jobs_path), "anchors.json"), "w"))


# ------------------------------------------------------------------ penyusunan lembar (matplotlib)
def view_box(bounds, view):
    lo, hi = bounds
    if view == "depan":
        return hi[0] - lo[0], hi[2] - lo[2]
    if view == "atas":
        return hi[0] - lo[0], hi[1] - lo[1]
    if view == "kiri":
        return hi[1] - lo[1], hi[2] - lo[2]


def make_job(stl, bounds, view, out, hidden=True, margin=6.0):
    w, h = view_box(bounds, view)
    W, H = w + 2 * margin, h + 2 * margin
    res = (max(64, int(W * PPM)), max(64, int(H * PPM)))
    return dict(items=[dict(stl=stl)], bounds=bounds, view=view, out=out, ortho=max(W, H), res=res,
                hidden=hidden, thick=2.2), (W, H)


def run_blender(jobs):
    jp = os.path.join(TMP, "jobs.json")
    json.dump(jobs, open(jp, "w"))
    subprocess.run([BLENDER, "-b", "-P", os.path.abspath(__file__), "--", jp], check=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)


def dim(ax, p1, p2, off, text, horiz=True, fs=7):
    """Garis dimensi linear antara p1-p2 (koordinat lembar mm), digeser off."""
    import matplotlib.patches as mp
    (x1, y1), (x2, y2) = p1, p2
    if horiz:
        y = y1 + off
        ax.plot([x1, x1], [y1, y + math.copysign(1.5, off)], lw=0.35, color="k")
        ax.plot([x2, x2], [y2, y + math.copysign(1.5, off)], lw=0.35, color="k")
        ax.annotate("", (x1, y), (x2, y), arrowprops=dict(arrowstyle="<|-|>", lw=0.45, color="k", mutation_scale=6))
        ax.text((x1 + x2) / 2, y + 1.0, text, ha="center", va="bottom", fontsize=fs)
    else:
        x = x1 + off
        ax.plot([x1, x + math.copysign(1.5, off)], [y1, y1], lw=0.35, color="k")
        ax.plot([x2, x + math.copysign(1.5, off)], [y2, y2], lw=0.35, color="k")
        ax.annotate("", (x, y1), (x, y2), arrowprops=dict(arrowstyle="<|-|>", lw=0.45, color="k", mutation_scale=6))
        ax.text(x - 1.0, (y1 + y2) / 2, text, ha="right", va="center", fontsize=fs, rotation=90)


def sheet(title, no, total, scale, material="-", mass="-"):
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(420 / 25.4, 297 / 25.4), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 420); ax.set_ylim(0, 297); ax.set_axis_off()
    ax.add_patch(plt.Rectangle((10, 10), 400, 277, fill=False, lw=1.2))
    ax.add_patch(plt.Rectangle((5, 5), 410, 287, fill=False, lw=0.3))
    x0, y0 = 240, 10
    tb = [(0, 0, 170, 42)]
    for r in tb:
        ax.add_patch(plt.Rectangle((x0 + r[0], y0 + r[1]), r[2], r[3], fill=False, lw=0.8))
    for yy in (10, 18, 26, 34):
        ax.plot([x0, x0 + 170], [y0 + yy, y0 + yy], lw=0.4, color="k")
    for xx in (60, 115):
        ax.plot([x0 + xx, x0 + xx], [y0, y0 + 34], lw=0.4, color="k")
    t = lambda x, y, s, **k: ax.text(x0 + x, y0 + y, s, va="center", fontsize=k.pop("fs", 6.5), **k)
    t(3, 38, "ARTA-C PORTABLE v2  |  DISPENSER OBAT TB", fs=8.5, weight="bold")
    t(3, 30, title, fs=8.5, weight="bold", color="#1d4ed8")
    t(3, 22, f"Skala: {scale}"); t(63, 22, "Satuan: mm"); t(118, 22, "Proyeksi Eropa (ISO-E)")
    t(3, 14, f"Bahan: {material}"); t(63, 14, f"Massa: {mass}"); t(118, 14, "Toleransi umum ISO 2768-m")
    t(3, 5, f"Digambar: Tim ARTA-C ({DATE})"); t(63, 5, f"No. gambar: GT-{no:02d}"); t(118, 5, f"Lembar {no} / {total}")
    return fig, ax


def place(ax, png, x, y, Wmm, Hmm, s):
    import matplotlib.image as mi
    ax.imshow(mi.imread(png), extent=(x, x + Wmm * s, y, y + Hmm * s), interpolation="bilinear", zorder=1)


def part_sheet(name, meta, files, no, total):
    """3 pandangan + iso, skala otomatis, dimensi keseluruhan."""
    lo, hi = meta["bounds"]
    X, Y, Z = (hi[i] - lo[i] for i in range(3))
    m = 6.0
    avail_w, avail_h = 215, 190
    for s, lab in ((2.0, "2 : 1"), (1.0, "1 : 1"), (0.5, "1 : 2"), (0.4, "1 : 2,5"), (0.25, "1 : 4")):
        if (X + Y + 4 * m) * s + 25 <= avail_w and (Z + Y + 4 * m) * s + 25 <= avail_h:
            break
    nm, fn, qty, mat = INFO[name]
    mass = f"{meta['vol'] * 1.24 * 0.55:.0f} g (cetak, infill 20%)"
    fig, ax = sheet(f"{nm.upper()}  ({name})", no, total, lab, mat, mass)
    fx, fz = 25, 285 - 18 - (Z + 2 * m) * s                     # pandangan depan
    place(ax, files["depan"], fx, fz, X + 2 * m, Z + 2 * m, s)
    tx, tz = fx, fz - 12 - (Y + 2 * m) * s                       # pandangan atas di bawah depan
    place(ax, files["atas"], tx, tz, X + 2 * m, Y + 2 * m, s)
    sx, sz = fx + (X + 2 * m) * s + 12, fz                       # pandangan kiri di kanan depan
    place(ax, files["kiri"], sx, sz, Y + 2 * m, Z + 2 * m, s)
    lab_kw = dict(fontsize=7, style="italic", color="#334155")
    ax.text(fx, fz + (Z + 2 * m) * s + 2, "PANDANGAN DEPAN", **lab_kw)
    ax.text(tx, tz - 4, "PANDANGAN ATAS", **lab_kw)
    ax.text(sx, sz + (Z + 2 * m) * s + 2, "PANDANGAN SAMPING KIRI", **lab_kw)
    # dimensi keseluruhan
    a = (fx + m * s, fz + m * s); b_ = (fx + (m + X) * s, fz + m * s)
    dim(ax, a, b_, -6, f"{X:.1f}")
    dim(ax, (fx + m * s, fz + m * s), (fx + m * s, fz + (m + Z) * s), -6, f"{Z:.1f}", horiz=False)
    dim(ax, (sx + m * s, sz + m * s), (sx + (m + Y) * s, sz + m * s), -6, f"{Y:.1f}")
    # iso
    import matplotlib.image as mi
    im = mi.imread(files["iso"])
    ih, iw = im.shape[:2]
    bw = 150; bh = bw * ih / iw
    if bh > 95:
        bh = 95; bw = bh * iw / ih
    ax.imshow(im, extent=(408 - bw, 408, 60, 60 + bh), zorder=1)
    ax.text(408 - bw, 60 + bh + 2, "ISOMETRI (tanpa skala)", **lab_kw)
    notes = [f"Fungsi: {fn}" if fn else "", f"Jumlah: {qty}", f"Bahan: {mat}, nozzle 0,4 mm, layer 0,2 mm",
             "Lubang ulir M3 = Ø2,6 mm; lubang tembus M3 = Ø3,4 mm", "Orientasi cetak: lihat file STL (sudah diatur)",
             "Ukuran = dimensi luar keseluruhan; ukuran rinci ambil dari model parametrik build.py"] + DETAIL.get(name, [])
    ax.text(242, 58, "CATATAN:\n" + "\n".join(f"- {n}" for n in notes if n), fontsize=6.3, va="bottom")
    return fig


def assembly_sheet(meta_all, files, no, total, b):
    shell = [k for k in meta_all if k.startswith("dinding")] + ["kantong_jari_ppg"]
    lo = [min(meta_all[k]["bounds"][0][i] for k in shell) for i in range(3)]
    hi = [max(meta_all[k]["bounds"][1][i] for k in shell) for i in range(3)]
    X, Y, Z = (hi[i] - lo[i] for i in range(3))
    s, m = 0.5, 6.0
    fig, ax = sheet("GAMBAR RAKITAN (ASSEMBLY)", no, total, "1 : 2", "PLA / PETG", "± 595 g filamen")
    fx, fz = 25, 285 - 20 - (Z + 2 * m) * s
    place(ax, files["depan"], fx, fz, X + 2 * m, Z + 2 * m, s)
    tx, tz = fx, fz - 14 - (Y + 2 * m) * s
    place(ax, files["atas"], tx, tz, X + 2 * m, Y + 2 * m, s)
    sx, sz = fx + (X + 2 * m) * s + 16, fz
    place(ax, files["kiri"], sx, sz, Y + 2 * m, Z + 2 * m, s)
    lab_kw = dict(fontsize=7, style="italic", color="#334155")
    ax.text(fx, fz + (Z + 2 * m) * s + 2, "PANDANGAN DEPAN", **lab_kw)
    ax.text(tx, tz - 4, "PANDANGAN ATAS", **lab_kw)
    ax.text(sx, sz + (Z + 2 * m) * s + 2, "PANDANGAN SAMPING KIRI", **lab_kw)
    P = lambda x, z: (fx + (m + x - lo[0]) * s, fz + (m + z - lo[2]) * s)        # titik pandangan depan
    S = lambda y, z: (sx + (m + y - lo[1]) * s, sz + (m + z - lo[2]) * s)        # titik pandangan kiri
    dim(ax, P(lo[0], lo[2]), P(hi[0], lo[2]), -7, f"{X:.0f}")
    dim(ax, P(lo[0], lo[2]), P(lo[0], hi[2]), -7, f"{Z:.0f}", horiz=False)
    dim(ax, S(-b.A, lo[2]), S(b.D + b.A, lo[2]), -7, f"{b.D + 2 * b.A:.0f}")
    dim(ax, S(lo[1], lo[2]), S(b.D + b.A, lo[2]), -15, f"{b.D + b.A - lo[1]:.0f} (dgn kantong jari)")
    callouts = [(P(b.CAM_LENS[0], b.CAM_LENS[1]), "Kamera ESP32-CAM Ø9"), (P(b.BUZ[0], b.BUZ[1]), "Buzzer"),
                (P(b.FING[0], b.FING[1]), "Kantong jari PPG (MAX30102)"), (P(b.DHT[0], b.DHT[1]), "Ventilasi DHT11"),
                (P(b.PCB[0] + 40, b.PCB[1] + 25), "Layar CYD 2,8 in"), (P(133, 18), "Baki ambil obat"),
                (P(100, b.H), "Celah masuk wadah"), (S(b.USBC[0], b.USBC[1]), "Port cas USB-C"),
                (S(8, 120), "Saklar daya")]
    front = sorted([c for c in callouts if c[1] not in ("Port cas USB-C", "Saklar daya")], key=lambda c: -c[0][1])
    side = [c for c in callouts if c[1] in ("Port cas USB-C", "Saklar daya")]
    col_x = sx + (Y + 2 * m) * s + 30
    ys = [fz + (Z + 2 * m) * s - 6 - i * 11 for i in range(len(front))]
    for ((x, y), txt), ty in zip(front, ys):
        ax.plot(x, y, "o", ms=1.6, color="#1d4ed8")
        ax.annotate(txt, (x, y), (col_x, ty), fontsize=6.4, va="center", color="#1d4ed8",
                    arrowprops=dict(arrowstyle="-", lw=0.35, color="#1d4ed8", shrinkA=0, shrinkB=0))
    for (x, y), txt in side:
        ax.plot(x, y, "o", ms=1.6, color="#b45309")
        ax.annotate(txt, (x, y), (x - 26, y + 8), fontsize=6.4, ha="right", color="#b45309",
                    arrowprops=dict(arrowstyle="-", lw=0.35, color="#b45309"))
    import matplotlib.image as mi
    im = mi.imread(files["iso"])
    ih, iw = im.shape[:2]
    bh = 150; bw = bh * iw / ih
    ax.imshow(im, extent=(408 - bw, 408, 56, 56 + bh), zorder=1)
    ax.text(408 - bw, 58 + bh + 2, "ISOMETRI RAKITAN", **lab_kw)
    return fig


def exploded_sheet(files, anchors, meta_all, no, total):
    import matplotlib.image as mi
    fig, ax = sheet("GAMBAR URAI (EXPLODED VIEW) & DAFTAR PART", no, total, "tanpa skala")
    im = mi.imread(files["urai"])
    ih, iw = im.shape[:2]
    x0, y0, bw = 14, 56, 255
    bh = bw * ih / iw
    if bh > 228:
        bh = 228; bw = bh * iw / ih
    ax.imshow(im, extent=(x0, x0 + bw, y0, y0 + bh), zorder=1)
    names = list(INFO)
    for i, n in enumerate(names, 1):
        if n not in anchors:
            continue
        u, v = anchors[n]
        px, py = x0 + u * bw, y0 + v * bh
        ang = math.atan2(py - (y0 + bh / 2), px - (x0 + bw / 2))
        bx, by = px + 14 * math.cos(ang), py + 14 * math.sin(ang)
        ax.plot([px, bx], [py, by], lw=0.4, color="#1d4ed8", zorder=3)
        ax.add_patch(__import__("matplotlib.pyplot").pyplot.Circle((bx, by), 3.2, fc="white", ec="#1d4ed8", lw=0.7, zorder=4))
        ax.text(bx, by, str(i), ha="center", va="center", fontsize=6, zorder=5, color="#1d4ed8", weight="bold")
    # daftar part
    tx, ty = 274, 284
    ax.text(tx, ty, "DAFTAR PART", fontsize=8, weight="bold")
    hdr = ("No", "Nama part", "Jml", "Bahan")
    cols = (0, 8, 92, 104)
    ty -= 5
    for c, h in zip(cols, hdr):
        ax.text(tx + c, ty, h, fontsize=6.2, weight="bold")
    for i, n in enumerate(names, 1):
        ty -= 6.6
        nm, fn, q, mat = INFO[n]
        for c, v in zip(cols, (str(i), nm, str(q), mat)):
            ax.text(tx + c, ty, v, fontsize=6.0)
        ax.plot([tx, tx + 134], [ty - 2.2, ty - 2.2], lw=0.2, color="#94a3b8")
    ty -= 9
    ax.text(tx, ty, "Non-cetak: 3x MG90S, PCA9685, CYD ESP32-2432S028,\nESP32-CAM, MAX30102, DHT11, buzzer, LiPo 103450,\n"
                    "IP5306 USB-C, saklar, baut M3/M2", fontsize=5.8, va="top", color="#334155")
    return fig


def main():
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.backends.backend_pdf import PdfPages
    b, meta = prepare()
    jobs, sizes, files = [], {}, {}
    order = list(INFO)
    for n in order:
        stl = os.path.join(TMP, f"{n}.stl")
        bd = meta[n]["bounds"]
        files[n] = {}
        for v in ("depan", "atas", "kiri"):
            out = os.path.join(TMP, f"{n}__{v}.png")
            j, _ = make_job(stl, bd, v, out)
            jobs.append(j); files[n][v] = out
        out = os.path.join(TMP, f"{n}__iso.png")
        jobs.append(dict(items=[dict(stl=stl, color=(0.55, 0.72, 0.98) if INFO[n][3].startswith("PETG") else (0.86, 0.9, 0.96))],
                         bounds=bd, view="iso", out=out, ortho=max(bd[1][i] - bd[0][i] for i in range(3)) * 1.7,
                         res=(900, 700), shaded=True, thick=1.6))
        files[n]["iso"] = out
    # rakitan
    allstl = [dict(stl=os.path.join(TMP, f"{n}.stl"), color=(0.86, 0.9, 0.96)) for n in order] + \
             [dict(stl=os.path.join(TMP, "_elektronik.stl"), color=(0.3, 0.34, 0.4))]
    shell = [n for n in order if n.startswith("dinding")] + ["kantong_jari_ppg"]
    lo = [min(meta[n]["bounds"][0][i] for n in shell) for i in range(3)]
    hi = [max(meta[n]["bounds"][1][i] for n in shell) for i in range(3)]
    asm = {}
    for v in ("depan", "atas", "kiri"):
        W, H = view_box((lo, hi), v)
        out = os.path.join(TMP, f"_asm__{v}.png")
        jobs.append(dict(items=[dict(stl=os.path.join(TMP, f"{n}.stl")) for n in shell],
                         bounds=(lo, hi), view=v, out=out, ortho=max(W, H) + 12, res=(int((W + 12) * PPM), int((H + 12) * PPM)),
                         hidden=False, thick=2.2))
        asm[v] = out
    out = os.path.join(TMP, "_asm__iso.png")
    jobs.append(dict(items=allstl, bounds=(lo, [hi[0], hi[1], hi[2] + 120]), view="iso", out=out, ortho=430, res=(1300, 1300),
                     shaded=True, thick=1.4))
    asm["iso"] = out
    urai_items = []
    for n in order:
        e = EXPLODE.get(n, (0, 0, 0))
        urai_items.append(dict(stl=os.path.join(TMP, f"{n}.stl"), name=n, offset=e,
                               color=(0.55, 0.72, 0.98) if INFO[n][3].startswith("PETG") else (0.88, 0.91, 0.96)))
    out_u = os.path.join(TMP, "_urai.png")
    jobs.append(dict(items=urai_items, bounds=([lo[0] - 150, lo[1] - 250, lo[2] - 110], [hi[0] + 150, hi[1] + 170, hi[2] + 175]),
                     view="iso", out=out_u, ortho=720, res=(2000, 1800), shaded=True, thick=1.2, anchors=True))
    run_blender(jobs)
    anchors = json.load(open(os.path.join(TMP, "anchors.json")))[out_u]
    os.makedirs(OUTD, exist_ok=True)
    total = 2 + len(order)
    pdf_path = os.path.join(OUTD, "GT_ARTA-C_Portable_v2.pdf")
    import matplotlib.pyplot as plt
    with PdfPages(pdf_path) as pdf:
        fig = assembly_sheet(meta, asm, 1, total, b); pdf.savefig(fig); fig.savefig(os.path.join(OUTD, "GT-01_rakitan.png"), dpi=110); plt.close(fig)
        fig = exploded_sheet({"urai": out_u}, anchors, meta, 2, total); pdf.savefig(fig)
        fig.savefig(os.path.join(OUTD, "GT-02_gambar_urai.png"), dpi=110); plt.close(fig)
        for i, n in enumerate(order, 3):
            fig = part_sheet(n, meta[n], files[n], i, total); pdf.savefig(fig); plt.close(fig)
    print("PDF:", pdf_path, "lembar:", total)


if __name__ == "__main__":
    if "--" in sys.argv:
        blender_main(sys.argv[sys.argv.index("--") + 1])
    else:
        main()
