"""Animasi 3D ARTA-C Portable v2 (konsep pemanggang roti) -> MP4 + gambar render + rakitan.glb.

  python anim.py          render penuh (Blender EEVEE + ffmpeg)
  python anim.py --test   beberapa frame uji
"""
import glob
import json
import math
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, "_anim_tmp")
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
FPS, N = 30, 810
STILLS = {12: "00_muka_depan_kamera_sensor.png", 330: "08_cek_jari_ppg.png", 40: "01_produk.png", 150: "02_blister_masuk_wadah.png", 240: "03_wadah_dimasukkan_seperti_roti.png",
          420: "04_pelatuk_mematuk.png", 535: "05_kaplet_keluar_ke_belakang.png", 790: "06_obat_di_baki.png"}


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def seg(f, a, b):
    return ease((f - a) / (b - a))


def lerp(a, b, t):
    return a + (b - a) * t


# ------------------------------------------------------------------ data (python biasa)
def prepare():
    sys.path.insert(0, HERE)
    import build as b
    import trimesh

    os.makedirs(TMP, exist_ok=True)
    for f in glob.glob(os.path.join(TMP, "*")):
        if os.path.isfile(f):
            os.remove(f)

    def save(name, m):
        b.to_tm(m).export(os.path.join(TMP, name + ".stl"))

    CB0 = b.cb_at(1)
    walls = b.walls_placed()
    save("S__dinding", b.union([m for n, m in walls.items() if n not in ("dinding_depan", "dinding_belakang")]))
    save("M__dinding_depan", walls["dinding_depan"])
    save("M__dinding_belakang", walls["dinding_belakang"])
    st = b.statics()
    save("S__rangka", b.union([m for k, m in st.items() if k != "kantong_jari"]))
    save("S__jari", st["kantong_jari"])
    # sekrup kepala rata di semua lubang dinding
    from manifold3d import Manifold as _M
    heads = []
    for wn, sp in b.wall_specs().items():
        for (u, v) in sp["holes"]:
            h = _M.cylinder(0.6, 2.75, 2.75, 24).translate([u, v, -0.25])
            h = h - b.box(u - 1.6, u + 1.6, v - 0.35, v + 0.35, -1, 0.1) - b.box(u - 0.35, u + 0.35, v - 1.6, v + 1.6, -1, 0.1)
            heads.append(h.transform(b.WALL_M[wn]))
    for x, z in b.FING_BOLT:
        heads.append(b.cyl_y(x, z, b.FING_Y[1] - 0.6, b.FING_Y[1] + 0.01, 2.75, 24))
    save("S__sekrup", b.union(heads))
    # jari (kapsul) untuk adegan PPG: ujung di y=0, badan ke -y
    jari = (b.cyl_y(0, 0, -75, -8, 8.0, 40) + _M.sphere(8.0, 40).translate([0, -8, 0]))
    save("M__jarikulit", jari)
    for i, (kind, m) in enumerate(b.dummies()):
        save(f"S__{kind}_{i}", m)
    save("M__wadah", b.wadah_belakang(CB0))
    save("M__wadahdepan", b.wadah_depan(CB0))
    base, domes, caps = b.blister_parts(CB0)
    save("M__foil", base)
    T = b.CAP_T - 0.4
    cap_home = {}
    dome_home = {}
    for (c, r), m in domes:
        x, z = b.pocket_xz(c, r, CB0)
        save(f"M__kubah_{c}{r}", m.translate([-x, -b.BASE_Y[0], -z]))
        dome_home[(c, r)] = (x, b.BASE_Y[0], z)
    save("C__kaplet", b.caplet())
    for (c, r), _ in caps:
        x, z = b.pocket_xz(c, r, CB0)
        cap_home[(c, r)] = (x, b.BASE_Y[0] - T / 2 - 0.3, z)
    save("M__G1", b.part_g1().translate([-b.G1[0], 0, -b.G1[1]]))
    save("M__G2", b.part_g2().translate([-b.G2[0], 0, -b.G2[1]]))
    save("M__tuas", b.part_tuas().translate([-b.S2[0], 0, -b.S2[1]]))
    save("M__kereta", b.kereta(b.XC))
    save("M__servo3", b.servo3_dummy(b.XC))
    save("M__engkol", b.engkol3(b.XC, 0).translate([-b.XC, -b.Y_S3, 0]))
    save("M__pelatuk", b.pelatuk(b.XC, 0))

    # ---------------- lintasan
    TABLE = -b.A
    DX_T, CB_T = 215.0, TABLE                          # wadah berdiri di meja (kanan alat)
    CB_HIGH = b.H + 8.0
    cols = [b.pocket_xz(c, 1, 0)[0] for c in range(1, 5)]

    def wadah_pose(f):                                  # (dx, cb, y_blister, y_frame)
        yb = lerp(-95, 0, seg(f, 75, 120))
        yf = lerp(-60, 0, seg(f, 122, 150))
        if f < 165:
            return DX_T, CB_T, yb, yf
        if f < 200:
            return DX_T, lerp(CB_T, CB_HIGH, seg(f, 165, 200)), 0, 0
        if f < 225:
            return lerp(DX_T, 0, seg(f, 200, 225)), CB_HIGH, 0, 0
        if f < 255:
            return 0, lerp(CB_HIGH, b.CB_EJ, seg(f, 225, 255)), 0, 0
        if f < 300:
            return 0, b.CB_EJ, 0, 0
        if f < 360:
            return 0, lerp(b.CB_EJ, b.cb_at(1), seg(f, 300, 360)), 0, 0
        if f < 650:
            return 0, b.cb_at(1), 0, 0
        return 0, lerp(b.cb_at(1), b.cb_at(2), seg(f, 650, 710)), 0, 0

    pecks = [(c, 360 + i * 95) for i, c in enumerate((1, 2, 3))]  # (kolom, frame mulai)

    def carriage(f):                                    # (x poros servo3, theta engkol)
        x = b.XC
        th = 0.0
        prev = b.XC
        for c, f0 in pecks:
            xc = cols[c - 1]
            if f < f0:
                break
            x = lerp(prev, xc, seg(f, f0, f0 + 25))
            if f >= f0 + 25:
                x = xc
                if f < f0 + 70:
                    th = 180.0 * seg(f, f0 + 28, f0 + 70)
                else:
                    th = 180.0 * (1 - seg(f, f0 + 72, f0 + 90))
            prev = xc
        if f >= 650:
            x = lerp(cols[2], b.XC, seg(f, 650, 690))
            th = 0.0
        return x, th

    frames = []
    release = {}
    g = 3.0                                             # gravitasi diperlambat (mm/frame^2)
    for f in range(N):
        fr = {}
        dx, cb, yb, yf = wadah_pose(f)
        dz = cb - CB0
        fr["M__wadah"] = [dx, 0, dz, 0, 0, 0, 1]
        fr["M__wadahdepan"] = [dx, yf, dz, 0, 0, 0, 1]
        fr["M__foil"] = [dx, yb, dz, 0, 0, 0, 1]
        th2 = (b.CB_EJ - cb) / (b.G2B_T / 2) if cb <= b.CB_EJ else 0.0      # rack turun -> G2 berputar +y
        th1 = -th2 * b.G2S_T / b.G1_T
        fr["M__G2"] = [b.G2[0], 0, b.G2[1], 0, th2, 0, 1]
        fr["M__G1"] = [b.G1[0], 0, b.G1[1], 0, th1, 0, 1]
        xs, th = carriage(f)
        fr["M__tuas"] = [b.S2[0], 0, b.S2[1], 0, b.lever_angle(xs), 0, 1]
        fr["M__kereta"] = [xs - b.XC, 0, 0, 0, 0, 0, 1]
        fr["M__servo3"] = [xs - b.XC, 0, 0, 0, 0, 0, 1]
        fr["M__engkol"] = [xs, b.Y_S3, 0, 0, 0, math.radians(th), 1]
        s = b.CRANK3 * (1 - math.cos(math.radians(th)))
        fr["M__pelatuk"] = [xs - b.XC, s, 0, 0, 0, 0, 1]
        pad_tip = b.Y_S3 - b.CRANK3 + s + b.PAD_LP
        for (c, r), (hx, hy, hz) in dome_home.items():
            crushed = 1.0
            push = 0.0
            active = (r == 1 and any(cc == c and f >= f0 + 25 for cc, f0 in pecks))
            if active:
                push = max(0.0, pad_tip - (b.DOME_TIP + 0.3))
            done = (r == 1 and any(cc == c and f >= f0 + 70 for cc, f0 in pecks))
            if active:
                crushed = max(0.12, 1 - min(push, b.DOME_H) / b.DOME_H) if not done else 0.12
            fr[f"M__kubah_{c}{r}"] = [hx + dx, hy + yb, hz + dz, 0, 0, 0, crushed]
            key = f"C__kaplet_{c}{r}"
            cx, cy, cz = cap_home[(c, r)]
            p = [cx + dx, cy + yb + (push if not done else 0), cz + dz]
            if active and not done:
                p[1] = cy + push
            if done or (active and push > 12.5):
                if key not in release:
                    release[key] = f
                t = f - release[key]
                x0, y0, z0 = cx, cy + 12.6, cz
                zr = b.ramp_back_z(x0) + T / 2
                tf = math.sqrt(2 * (z0 - zr) / g)
                tray_x, rest_y = 133.0, 6.0 + (c - 1) * 10.5
                slope = math.atan(20 / 47)
                if t <= tf:
                    p = [x0, lerp(y0, 40.5, min(1, t / 4)), z0 - 0.5 * g * t * t]
                    rot = (math.pi / 2 * min(1, t / tf), 0, 0)
                else:
                    u = (t - tf)
                    if u <= 14:
                        x = lerp(x0, 148.0, ease(u / 14))
                        p = [x, 40.5, b.ramp_back_z(x) + T / 2]
                        rot = (math.pi / 2, math.atan(50 / 106), 0)
                    elif u <= 20:
                        k = (u - 14) / 6
                        p = [lerp(148, tray_x, k), 40.5, lerp(b.ramp_back_z(148), b.ramp_fwd_z(40.5), k) + T / 2]
                        rot = (math.pi / 2 + slope * k, 0, 0)
                    else:
                        k = ease(min(1, (u - 20) / 14))
                        yy = lerp(40.5, rest_y, k)
                        p = [tray_x, yy, b.ramp_fwd_z(yy) + T / 2 + 0.3]
                        rot = (math.pi / 2 + slope, 0, 0)
                fr[key] = [*p, *rot, 1]
                continue
            fr[key] = [*p, 0, 0, 0, 1]
        fr["alpha"] = 1.0 - 0.9 * seg(f, 255, 300)
        fr["alpha_b"] = 1.0 - 0.88 * seg(f, 445, 470) + 0.88 * seg(f, 565, 590)
        fr["screen"] = 0 if f < 300 else (1 if f < 360 else (2 if f < 640 else 3))
        if 300 <= f < 362:
            yt = lerp(-150, -11.5, seg(f, 300, 322)) if f < 345 else lerp(-11.5, -150, seg(f, 345, 362))
        else:
            yt = None
        fr["M__jarikulit"] = [b.FING[0], yt, b.FING[1], 0, 0, 0, 1] if yt is not None else [0, 0, -3000, 0, 0, 0, 1]
        frames.append(fr)

    cams = [(0, (60, -300, 120), (81, 0, 100)), (25, (40, -320, 150), (81, 0, 100)),
            (70, (300, -430, 250), (160, 20, 95)),
            (95, (470, -330, 190), (310, -20, 70)), (160, (470, -320, 200), (300, -10, 80)),
            (200, (380, -470, 390), (190, 20, 200)), (255, (300, -470, 360), (100, 20, 190)),
            (290, (150, -330, 150), (80, -20, 75)), (300, (40, -245, 108), (78, -25, 63)),
            (350, (30, -230, 104), (78, -25, 63)), (372, (165, -230, 235), (98, 25, 165)),
            (440, (175, -235, 225), (100, 25, 160)), (455, (430, -90, 250), (100, 25, 150)),
            (475, (300, 380, 230), (95, 35, 140)), (560, (300, 380, 220), (100, 35, 130)),
            (578, (430, -90, 240), (100, 25, 150)), (600, (200, -260, 200), (105, 25, 150)),
            (640, (240, -300, 120), (120, 25, 60)),
            (720, (150, -175, 45), (133, 12, 8)), (809, (140, -165, 42), (133, 12, 8))]
    lcd = dict(x0=b.PCB[0] + b.PCB[2] - b.ACT_FROM_USB - b.ACT_W / 2, z0=b.PCB[1] + b.PCB[3] / 2 - b.ACT_H / 2,
               w=b.ACT_W, h=b.ACT_H)
    json.dump(dict(frames=frames, cams=cams, table=TABLE, n=N, fps=FPS, lcd=lcd), open(os.path.join(TMP, "anim.json"), "w"))
    screens = [("Masukkan wadah", "blister ke celah atas", "#2563eb", "\u2193", "28\u00b0C  65%RH  \u2022  baterai 86%"),
               ("Cek PPG jari \u2713", "\u2665 78 bpm  SpO2 98%", "#7c3aed", "\u2665",
                "TD ~118/76*  GD ~105 mg/dL*   *estimasi"),
               ("Wajah terverifikasi \u2713", "Saatnya minum obat", "#2563eb", "1", "\u2665 78 bpm  \u2022  SpO2 98%"),
               ("Hari ke-1", "Obat sudah keluar \u2713", "#16a34a", "1", "\u2665 78 bpm  \u2022  SpO2 98%  \u2022  28\u00b0C")]
    for i, (l1, l2, col, big, st) in enumerate(screens):
        make_screen(os.path.join(TMP, f"lcd_{i}.png"), l1, l2, col, big, st)

    # rakitan.glb (pose baris 1)
    import numpy as np
    import matplotlib.colors as mc
    col = {"dinding": "#dbe4ee", "rangka": "#f2f4f7", "gear": "#3b82f6", "wadah": "#93c5fd", "pelatuk": "#f59e0b",
           "servo": "#334155", "pcb": "#eab308", "lcd": "#0f172a", "bat": "#64748b", "obat": "#dc2626", "foil": "#cbd5e1",
           "dht": "#38bdf8"}
    sc = trimesh.Scene()
    items = [("dinding", m) for m in walls.values()] + [("rangka", m) for m in b.statics().values()]
    items += [(k if k in col else "servo", m) for k, m in b.dummies()]
    items += [("gear", b.part_g2()), ("wadah", b.wadah_belakang(CB0)), ("wadah", b.wadah_depan(CB0)), ("foil", base)]
    items += [("obat", m) for _, m in caps] + [("pelatuk", b.kereta(cols[0])), ("pelatuk", b.pelatuk(cols[0])),
                                               ("servo", b.servo3_dummy(cols[0])), ("pelatuk", b.engkol3(cols[0])),
                                               ("pelatuk", b.part_tuas(b.lever_angle(cols[0])))]
    for i, (k, m) in enumerate(items):
        t = b.to_tm(m)
        t.visual.face_colors = np.tile((np.array(mc.to_rgba(col[k])) * 255).astype(np.uint8), (len(t.faces), 1))
        sc.add_geometry(t, node_name=f"{k}_{i}")
    sc.export(os.path.join(HERE, "rakitan.glb"))


def make_screen(path, l1, l2, color, big, status=""):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(3.2, 2.4), dpi=100)
    fig.patch.set_facecolor("#eef4ff")
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off(); ax.set_xlim(0, 320); ax.set_ylim(0, 240)
    ax.add_patch(plt.Rectangle((0, 205), 320, 35, color=color))
    ax.text(12, 222, "ARTA-C", color="white", fontsize=15, weight="bold", va="center")
    ax.text(308, 222, "07:00", color="white", fontsize=12, va="center", ha="right")
    ax.text(160, 190, status, fontsize=9.5, ha="center", va="center", color="#334155")
    ax.add_patch(plt.Circle((160, 118), 50, color="white", ec=color, lw=6))
    ax.text(160, 118, big, fontsize=40, weight="bold", ha="center", va="center", color=color)
    ax.text(160, 45, l1, fontsize=12, ha="center", color="#475569")
    ax.text(160, 20, l2, fontsize=13, ha="center", color="#0f172a", weight="bold")
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)


# ------------------------------------------------------------------ Blender
MAT = {"dinding": (0.86, 0.9, 0.95), "dinding_depan": (0.86, 0.9, 0.95), "dinding_belakang": (0.86, 0.9, 0.95), "rangka": (0.95, 0.96, 0.98),
       "servo": (0.12, 0.14, 0.18), "servo3": (0.12, 0.14, 0.18), "pcb": (0.85, 0.65, 0.1), "lcd": (0.02, 0.03, 0.06),
       "bat": (0.35, 0.4, 0.48), "dht": (0.2, 0.6, 0.95), "wadah": (0.42, 0.65, 0.97), "wadahdepan": (0.6, 0.78, 1.0),
       "foil": (0.82, 0.83, 0.86), "kubah": (0.92, 0.96, 1.0), "kaplet": (0.75, 0.04, 0.05),
       "G1": (0.15, 0.42, 0.95), "G2": (0.15, 0.42, 0.95), "tuas": (0.98, 0.62, 0.1), "kereta": (0.98, 0.62, 0.1),
       "engkol": (0.98, 0.62, 0.1), "pelatuk": (0.95, 0.45, 0.05), "jari": (0.05, 0.055, 0.065),
       "sekrup": (0.75, 0.76, 0.78), "jarikulit": (0.86, 0.62, 0.5)}


def blender_main(tmp, test):
    import bpy
    from mathutils import Vector

    data = json.load(open(os.path.join(tmp, "anim.json")))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.exposure = -0.6
    try:
        sc.view_settings.look = "AgX - Medium High Contrast"
        sc.eevee.taa_render_samples = 48
        sc.eevee.use_raytracing = True
    except Exception:
        pass
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.93, 0.95, 0.98, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.45
    mats = {}

    def mat(kind):
        if kind in mats:
            return mats[kind]
        m = bpy.data.materials.new(kind); m.use_nodes = True
        p = m.node_tree.nodes["Principled BSDF"]
        p.inputs["Base Color"].default_value = (*MAT.get(kind, MAT["rangka"]), 1)
        p.inputs["Roughness"].default_value = 0.4
        if kind in ("foil", "sekrup"):
            p.inputs["Metallic"].default_value = 1.0; p.inputs["Roughness"].default_value = 0.3
        if kind in ("dinding", "dinding_depan", "dinding_belakang", "rangka"):
            p.inputs["Roughness"].default_value = 0.55
        if kind == "jarikulit":
            p.inputs["Roughness"].default_value = 0.5
            p.inputs["Subsurface Weight"].default_value = 0.3
            p.inputs["Subsurface Radius"].default_value = (1.0, 0.4, 0.25)
        if kind == "kubah":
            p.inputs["Alpha"].default_value = 0.35; p.inputs["Roughness"].default_value = 0.05
        if kind == "kaplet":
            p.inputs["Roughness"].default_value = 0.25
        mats[kind] = m
        return m

    objs = {}
    for f in sorted(os.listdir(tmp)):
        if not f.endswith(".stl"):
            continue
        grp, name = f[:-4].split("__")
        bpy.ops.wm.stl_import(filepath=os.path.join(tmp, f))
        o = bpy.context.selected_objects[0]
        kind = name.split("_")[0] if grp in ("S", "C") or name.startswith("kubah") else name
        if grp == "S" and name.startswith("dinding"):
            kind = "dinding"
        o.data.materials.append(mat(kind))
        bpy.ops.object.shade_auto_smooth(angle=math.radians(30))
        if grp == "C":
            for c in range(1, 5):
                for r in range(1, 8):
                    k = o.copy(); k.data = o.data
                    bpy.context.collection.objects.link(k)
                    objs[f"C__kaplet_{c}{r}"] = k
            bpy.data.objects.remove(o)
        else:
            objs[f"{grp}__{name}"] = o

    bpy.ops.mesh.primitive_plane_add(size=4000, location=(150, 0, data["table"] - 0.01))
    bpy.context.object.data.materials.append(mat("rangka"))
    lcd = data["lcd"]
    bpy.ops.mesh.primitive_plane_add(size=1, location=(lcd["x0"] + lcd["w"] / 2, 0.3, lcd["z0"] + lcd["h"] / 2),
                                     rotation=(math.radians(90), 0, 0))
    scr = bpy.context.object; scr.scale = (lcd["w"], lcd["h"], 1)
    for i in range(4):
        sm = bpy.data.materials.new(f"layar{i}"); sm.use_nodes = True
        nt = sm.node_tree; nt.nodes.clear()
        tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(os.path.join(tmp, f"lcd_{i}.png"))
        em = nt.nodes.new("ShaderNodeEmission"); em.inputs[1].default_value = 1.5
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(tex.outputs[0], em.inputs[0]); nt.links.new(em.outputs[0], out.inputs[0])
        scr.data.materials.append(sm)

    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(45), math.radians(15), math.radians(-30)))
    bpy.context.object.data.energy = 3.0
    bpy.ops.object.light_add(type="AREA", location=(150, -380, 380))
    a = bpy.context.object; a.data.energy = 3e6; a.data.size = 400
    a.rotation_euler = (Vector((120, 15, 90)) - a.location).to_track_quat("-Z", "Y").to_euler()

    tgt = bpy.data.objects.new("target", None); bpy.context.collection.objects.link(tgt)
    bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam
    cam.data.lens = 45; cam.data.clip_end = 8000
    con = cam.constraints.new("TRACK_TO"); con.target = tgt
    con.track_axis = "TRACK_NEGATIVE_Z"; con.up_axis = "UP_Y"
    for fr, loc, tg in data["cams"]:
        cam.location = loc; cam.keyframe_insert("location", frame=fr)
        tgt.location = tg; tgt.keyframe_insert("location", frame=fr)

    pd = objs["M__dinding_depan"].data.materials[0].node_tree.nodes["Principled BSDF"]
    objs["M__dinding_belakang"].data.materials.clear()
    objs["M__dinding_belakang"].data.materials.append(mat("dinding_belakang"))
    pb = objs["M__dinding_belakang"].data.materials[0].node_tree.nodes["Principled BSDF"]
    for i, fr in enumerate(data["frames"]):
        for k, v in fr.items():
            if k == "alpha":
                pd.inputs["Alpha"].default_value = v
                pd.inputs["Alpha"].keyframe_insert("default_value", frame=i)
                continue
            if k == "alpha_b":
                pb.inputs["Alpha"].default_value = v
                pb.inputs["Alpha"].keyframe_insert("default_value", frame=i)
                continue
            if k == "screen":
                continue
            o = objs[k]
            o.location = v[:3]; o.rotation_euler = v[3:6]; o.scale = (1, v[6], 1)
            o.keyframe_insert("location", frame=i); o.keyframe_insert("rotation_euler", frame=i)
            if k.startswith("M__kubah"):
                o.keyframe_insert("scale", frame=i)

    outdir = os.path.join(tmp, "frames"); os.makedirs(outdir, exist_ok=True)
    custom = os.environ.get("ANIM_FRAMES")
    frames = ([int(x) for x in custom.split(",")] if custom else sorted(STILLS)) if test else range(data["n"])
    for i in frames:
        sc.frame_set(i)
        for poly in scr.data.polygons:
            poly.material_index = data["frames"][i]["screen"]
        sc.render.filepath = os.path.join(outdir, f"f_{i:04d}.png")
        bpy.ops.render.render(write_still=True)


CAPTIONS = [(0, 75, "ARTA-C Portable  -  dispenser obat TB pintar dengan pemantauan PMO"),
            (75, 165, "1   PMO menjepit blister obat utuh di dalam wadah"),
            (165, 255, "2   Wadah dimasukkan ke celah atas, seperti roti di pemanggang"),
            (255, 300, "Tampilan dalam: dinding depan dibuat transparan"),
            (300, 362, "3   Cek jari PPG (MAX30102): detak jantung & SpO2  -  TD & gula darah: estimasi"),
            (362, 455, "4   Verifikasi wajah ESP32-CAM  -  servo 1 menurunkan wadah per baris, servo 2 menggeser kereta"),
            (455, 590, "5   Pelatuk (servo 3) menekan kubah: kaplet tembus foil ke belakang"),
            (590, 700, "6   Kaplet meluncur ke baki ambil  -  layar: obat sudah keluar"),
            (700, 810, "7   Riwayat minum obat & data vital terkirim ke aplikasi ARTA-C untuk PMO")]


def add_captions(src_dir, dst_dir):
    from PIL import Image, ImageDraw, ImageFont
    os.makedirs(dst_dir, exist_ok=True)
    fb = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 34)
    fs = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 22)
    for fn in sorted(os.listdir(src_dir)):
        f = int(fn[2:6])
        im = Image.open(os.path.join(src_dir, fn)).convert("RGB")
        W, H = im.size
        d = ImageDraw.Draw(im, "RGBA")
        c = next((t for a, b_, t in CAPTIONS if a <= f < b_), "")
        if c:
            a, b_ = next((a, b_) for a, b_, t in CAPTIONS if a <= f < b_)
            al = min(1.0, (f - a) / 8.0, (b_ - f) / 8.0)
            tw = d.textlength(c, font=fb)
            d.rounded_rectangle([(W - tw) / 2 - 28, H - 104, (W + tw) / 2 + 28, H - 42], 16, fill=(15, 23, 42, int(205 * al)))
            d.text(((W - tw) / 2, H - 99), c, font=fb, fill=(255, 255, 255, int(255 * al)))
        d.text((34, 26), "ARTA-C", font=fb, fill=(29, 78, 216, 255))
        d.text((36, 68), "Portable v2  |  dispenser obat TB", font=fs, fill=(51, 65, 85, 255))
        im.save(os.path.join(dst_dir, fn))


def ffmpeg():
    if shutil.which("ffmpeg"):
        return shutil.which("ffmpeg")
    hits = glob.glob(os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Packages",
                                  "Gyan.FFmpeg*", "*", "bin", "ffmpeg.exe"))
    return hits[0] if hits else "ffmpeg"


if __name__ == "__main__":
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1:]
        blender_main(args[0], "--test" in args)
        sys.exit(0)
    test = "--test" in sys.argv
    prepare()
    fd = os.path.join(TMP, "frames")
    if os.path.isdir(fd):
        shutil.rmtree(fd)
    subprocess.run([BLENDER, "-b", "-P", os.path.abspath(__file__), "--", TMP] + (["--test"] if test else []),
                   check=True, stdout=subprocess.DEVNULL)
    os.makedirs(os.path.join(HERE, "render"), exist_ok=True)
    for f, name in STILLS.items():
        src = os.path.join(fd, f"f_{f:04d}.png")
        if os.path.exists(src):
            shutil.copy(src, os.path.join(HERE, "render", name))
    if not test:
        os.makedirs(os.path.join(HERE, "animasi"), exist_ok=True)
        out = os.path.join(HERE, "animasi", "ARTA-C_portable_animasi.mp4")
        fin = os.path.join(TMP, "final")
        if os.path.isdir(fin):
            shutil.rmtree(fin)
        add_captions(fd, fin)
        subprocess.run([ffmpeg(), "-y", "-framerate", str(FPS), "-i", os.path.join(fin, "f_%04d.png"), "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", "-crf", "20", out], check=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        print("video:", out)
    print("selesai")
