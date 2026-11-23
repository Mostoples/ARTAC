"""Animasi 3D ARTA-C Portable (Blender EEVEE -> MP4).

  python anim.py            -> animasi/ARTA-C_portable_animasi.mp4
  python anim.py --test     -> beberapa frame uji saja
Alur: blister -> isi kaset 7 hari -> tutup -> masukkan ke alat -> gear menggeser kaset
      -> pelatuk turun -> kaplet meluncur ke baki.
"""
import json
import math
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, "_anim_tmp")
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
FPS, N_FRAMES = 30, 720


# ------------------------------------------------------------------ bagian python biasa
def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def seg(f, f0, f1):
    return ease((f - f0) / (f1 - f0))


def prepare():
    sys.path.insert(0, HERE)
    import build as b
    from manifold3d import Manifold

    os.makedirs(TMP, exist_ok=True)
    for f in os.listdir(TMP):
        os.remove(os.path.join(TMP, f))

    def save(name, m):
        b.to_tm(m).export(os.path.join(TMP, name + ".stl"))

    # ---- statis
    walls = b.walls_placed()
    save("S__dinding", b.union([m for n, m in walls.items() if n != "dinding_depan"]))
    save("M__dinding_depan", walls["dinding_depan"])
    stat = [b.part_rel(), b.part_corong(), b.part_dek(), b.part_klem_servo(), b.part_tabung(), b.part_braket_b(),
            b.part_dudukan_layar()] + [b.part_blok(n) for n in b.CORNERS]
    save("S__rangka", b.union(stat))
    for kind, m in b.dummies(0):
        save(f"S__{kind}_{abs(hash(str(m.bounding_box()))) % 1000}", m)

    # ---- bergerak (mesh lokal di sekitar pivot)
    save("M__kaset", b.cas_place(b.kaset_badan_local() + b.kaset_alas_local(), 0))
    save("M__membran", b.box(0, b.LC, b.CAS_Y0, b.CAS_Y0 + b.DC, b.ZB + b.PLATE_T, b.ZB + b.PLATE_T + b.MEM_T))
    save("M__tutup", b.cas_place(b.kaset_tutup_local(), 0))
    save("M__G1", b.part_g1().translate([-b.X_A, -b.Y_C, 0]))
    save("M__G2", b.part_g2().translate([-b.X_G2, -b.Y_C, 0]))
    save("M__G3", b.part_g3().translate([-b.X_S, -b.Y_C, 0]))
    save("M__pelatuk", b.part_pelatuk(0))
    save("M__engkol", b.part_engkol(0).translate([-b.X_B, 0, -b.Z_B]))
    T = b.CAP_T - 0.4
    r = b.CAP_W / 2
    cap = (Manifold.cylinder(T, r, r, 32).translate([0, -(b.CAP_L / 2 - r), -T / 2])
           + Manifold.cylinder(T, r, r, 32).translate([0, (b.CAP_L / 2 - r), -T / 2])).hull()
    save("C__kaplet", cap)
    # blister 7 x 4 (dibaringkan di meja)
    BX0, BY0, PX, PY = 0.0, 0.0, 14.0, 25.0
    base = b.box(-8, 7 * PX - 6, -13, 4 * PY - 12, 0, 0.8)
    domes = []
    for c in range(7):
        for rr in range(4):
            d = (Manifold.cylinder(T + 1.5, r + 1, r + 1, 32).translate([c * PX, rr * PY - (b.CAP_L / 2 - r), 0.8])
                 + Manifold.cylinder(T + 1.5, r + 1, r + 1, 32).translate([c * PX, rr * PY + (b.CAP_L / 2 - r), 0.8])).hull()
            domes.append(d)
    save("M__blister_foil", base)
    save("M__blister_kubah", b.union(domes))

    # ---- lintasan
    TABLE = -b.ACR
    zoff_table = TABLE - b.ZB                       # kaset di meja
    x_out = b.W + b.ACR + 45.0                      # kaset di luar (kanan)
    x_eject = b.X_S + 4.0
    x_day = lambda d: b.cas_left_at(d)
    blis_org = (x_out + 4.0, -150.0, TABLE)         # pojok blister di meja (depan kaset)
    floor_cell = b.ZB + b.PLATE_T + b.MEM_T + 0.2

    def cas_pose(f):
        if f < 285:
            return x_out, zoff_table
        if f < 345:                                  # angkat ke tinggi rel
            t = seg(f, 285, 345)
            return x_out, zoff_table * (1 - t)
        if f < 420:
            return x_out + (x_eject - x_out) * seg(f, 345, 420), 0.0
        if f < 480:
            return x_eject + (x_day(1) - x_eject) * seg(f, 420, 480), 0.0
        if f < 610:
            return x_day(1), 0.0
        return x_day(1) + (x_day(2) - x_day(1)) * seg(f, 610, 660), 0.0

    def crank(f):
        if f < 480:
            return 0.0
        if f < 570:
            return 180.0 * seg(f, 480, 570)
        return 180.0 * (1 - seg(f, 570, 610))

    frames = []
    caps_assign = [(d, k) for d in range(1, 8) for k in range(3)] + [(d, 3) for d in range(1, 8)]  # 21 dipindah + 7 sisa
    detach = {}
    for f in range(N_FRAMES):
        fr = {}
        xl, zo = cas_pose(f)
        fr["M__kaset"] = [xl, 0, zo, 0, 0, 0]
        fr["M__membran"] = [xl, 0, zo, 0, 0, 0]
        # tutup: dari meja ke atas kaset (255..285), lalu ikut kaset
        if f < 255:
            fr["M__tutup"] = [x_out, 45.0, zoff_table - (b.ZT - b.ZB), 0, 0, 0]
        elif f < 285:
            t = seg(f, 255, 285)
            fr["M__tutup"] = [x_out, 45.0 * (1 - t), zoff_table - (b.ZT - b.ZB) * (1 - t) + 25 * math.sin(math.pi * t), 0, 0, 0]
        else:
            fr["M__tutup"] = [xl, 0, zo, 0, 0, 0]
        # gear
        th3 = -(xl - x_eject) / b.R3 if xl <= x_eject else 0.0
        th2 = -th3 * b.G3S_T / b.G2B_T
        th1 = -th2 * b.G2S_T / b.G1_T
        fr["M__G3"] = [b.X_S, b.Y_C, 0, 0, 0, th3]
        fr["M__G2"] = [b.X_G2, b.Y_C, 0, 0, 0, th2]
        fr["M__G1"] = [b.X_A, b.Y_C, 0, 0, 0, th1]
        th = crank(f)
        dz = -b.STROKE * (1 - math.cos(math.radians(th))) / 2
        fr["M__pelatuk"] = [0, 0, dz, 0, 0, 0]
        fr["M__engkol"] = [b.X_B, 0, b.Z_B, 0, math.radians(th), 0]
        fr["M__blister_foil"] = [*blis_org, 0, 0, 0]
        fr["M__blister_kubah"] = [*blis_org, 0, 0, 0]
        tip = b.ROD_TIP_UP + dz
        for idx, (d, k) in enumerate(caps_assign):
            key = f"C__kaplet_{idx:02d}"
            src = (blis_org[0] + (d - 1) * PX, blis_org[1] + k * PY, TABLE + 0.8 + T / 2)
            cell = lambda xl_, zo_: (xl_ + b.cell_cx(d), b.Y_C, zo_ + floor_cell + k * b.CAP_T + T / 2)
            f0 = 75 + idx * 7
            if f < f0 or k == 3:
                p = src
            elif f < f0 + 30:
                t = seg(f, f0, f0 + 30)
                dst = cell(x_out, zoff_table)
                p = tuple(src[i] + (dst[i] - src[i]) * t for i in range(3))
                p = (p[0], p[1], p[2] + 70 * math.sin(math.pi * t))
            else:
                p = cell(xl, zo)
                if d == 1 and f >= 480:
                    top = floor_cell + 3 * b.CAP_T
                    s = max(0.0, top - tip)
                    p = (p[0], p[1], p[2] - s)
                    if key not in detach and p[2] < b.ZB - 1:
                        detach[key] = (f, p)
                    if key in detach:
                        fd, pd = detach[key]
                        tt = f - fd
                        x_end = 22.0 + k * 9.0
                        z_ramp = b.ramp_z(pd[0]) + T / 2 + 1
                        tf = 7
                        if tt <= tf:
                            p = (pd[0], pd[1], pd[2] + (z_ramp - pd[2]) * (tt / tf) ** 2)
                        else:
                            u = min(1.0, (tt - tf) / 18.0)
                            x = pd[0] + (x_end - pd[0]) * u ** 1.6
                            z = max(b.ramp_z(x), 8.5) + T / 2 + 0.6 if x > 46 else 8.5 + T / 2 + 0.3
                            yy = pd[1] + (k - 1) * 5.0 * u
                            ang = math.atan(33.0 / 60.6) if x > 46 else 0.0
                            fr[key] = [x, yy, z, 0, -ang, 0]
                            continue
            fr[key] = [p[0], p[1], p[2], 0, 0, 0]
        fr["alpha_depan"] = 1.0 - 0.88 * seg(f, 345, 395)
        frames.append(fr)

    cams = [(0, (-170, -430, 250), (100, 15, 80)), (70, (340, -440, 250), (110, 15, 70)),
            (100, (420, -300, 170), (300, -60, 0)), (250, (440, -280, 190), (300, -40, 10)),
            (340, (420, -420, 230), (210, 15, 60)), (420, (260, -390, 240), (115, 15, 90)),
            (480, (210, -260, 190), (105, 15, 95)), (560, (150, -260, 120), (70, 15, 50)),
            (650, (60, -190, 70), (32, 12, 12)), (719, (55, -180, 65), (32, 12, 12))]
    data = dict(frames=frames, cams=cams, table=TABLE, n=N_FRAMES, fps=FPS, lcd=dict(
        x0=b.PCB_X0 + b.PCB_L - b.ACT_FROM_USB - b.ACT_W / 2, z0=b.PCB_Z0 + b.PCB_W / 2 - b.ACT_H / 2,
        w=b.ACT_W, h=b.ACT_H))
    json.dump(data, open(os.path.join(TMP, "anim.json"), "w"))
    make_screens(os.path.join(TMP, "lcd_1.png"), "Hari ke-1", "Saatnya minum obat", "#2563eb")
    make_screens(os.path.join(TMP, "lcd_2.png"), "Hari ke-1", "Obat sudah keluar  \u2713", "#16a34a")


def make_screens(path, l1, l2, color):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(3.2, 2.4), dpi=100)
    fig.patch.set_facecolor("#eef4ff")
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off(); ax.set_xlim(0, 320); ax.set_ylim(0, 240)
    ax.add_patch(plt.Rectangle((0, 205), 320, 35, color=color))
    ax.text(12, 222, "ARTA-C", color="white", fontsize=15, weight="bold", va="center")
    ax.text(308, 222, "07:00", color="white", fontsize=12, va="center", ha="right")
    ax.add_patch(plt.Circle((160, 120), 60, color="white", ec=color, lw=6))
    ax.text(160, 128, l1.split("-")[-1], fontsize=40, weight="bold", ha="center", va="center", color=color)
    ax.text(160, 88, "hari ke", fontsize=11, ha="center", color="#475569")
    ax.text(160, 35, l2, fontsize=14, ha="center", color="#0f172a", weight="bold")
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)


# ------------------------------------------------------------------ bagian Blender
MAT = {"rangka": (0.95, 0.96, 0.98), "dinding": (0.86, 0.9, 0.95), "dinding_depan": (0.86, 0.9, 0.95),
       "servo": (0.12, 0.14, 0.18), "pcb": (0.85, 0.65, 0.1), "lcd": (0.02, 0.03, 0.06), "bat": (0.35, 0.4, 0.48),
       "kaset": (0.45, 0.68, 0.98), "membran": (0.08, 0.08, 0.08), "tutup": (0.72, 0.84, 1.0),
       "G1": (0.15, 0.42, 0.95), "G2": (0.15, 0.42, 0.95), "G3": (0.15, 0.42, 0.95),
       "pelatuk": (0.98, 0.62, 0.1), "engkol": (0.98, 0.62, 0.1), "kaplet": (0.75, 0.04, 0.05),
       "blister_foil": (0.8, 0.8, 0.82), "blister_kubah": (0.9, 0.95, 1.0)}


def blender_main(tmp, test):
    import bpy
    from mathutils import Vector

    data = json.load(open(os.path.join(tmp, "anim.json")))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    sc.render.fps = data["fps"]
    sc.frame_start, sc.frame_end = 0, data["n"] - 1
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.exposure = -0.7
    try:
        sc.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    try:
        sc.eevee.taa_render_samples = 32
        sc.eevee.use_shadows = True
    except Exception:
        pass
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.93, 0.95, 0.98, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.45

    mats = {}

    def mat(kind):
        base = kind.split("_")[0] if kind not in MAT else kind
        if base not in MAT:
            base = "rangka"
        if kind in mats:
            return mats[kind]
        m = bpy.data.materials.new(kind); m.use_nodes = True
        p = m.node_tree.nodes["Principled BSDF"]
        p.inputs["Base Color"].default_value = (*MAT[base], 1)
        p.inputs["Roughness"].default_value = 0.4
        if base in ("blister_foil",):
            p.inputs["Metallic"].default_value = 1.0; p.inputs["Roughness"].default_value = 0.3
        if base in ("blister_kubah",):
            p.inputs["Alpha"].default_value = 0.35; p.inputs["Roughness"].default_value = 0.05
        if base == "kaset":
            p.inputs["Alpha"].default_value = 0.55
        if base == "kaplet":
            p.inputs["Roughness"].default_value = 0.25
        mats[kind] = m
        return m

    objs = {}
    for f in sorted(os.listdir(tmp)):
        if not f.endswith(".stl"):
            continue
        grp, kind = f[:-4].split("__")
        bpy.ops.wm.stl_import(filepath=os.path.join(tmp, f))
        o = bpy.context.selected_objects[0]
        o.data.materials.append(mat(kind.rsplit("_", 1)[0] if grp == "S" and kind[-1].isdigit() else kind))
        bpy.ops.object.shade_auto_smooth(angle=math.radians(30))
        if grp == "C":
            src = o
            for i in range(28):
                c = src.copy(); c.data = src.data
                bpy.context.collection.objects.link(c)
                objs[f"C__kaplet_{i:02d}"] = c
            bpy.data.objects.remove(src)
        else:
            objs[f"{grp}__{kind}"] = o
    # meja
    bpy.ops.mesh.primitive_plane_add(size=3000, location=(150, 0, data["table"] - 0.01))
    bpy.context.object.data.materials.append(mat("rangka"))
    # layar LVGL
    lcd = data["lcd"]
    imgs = [bpy.data.images.load(os.path.join(tmp, "lcd_1.png")), bpy.data.images.load(os.path.join(tmp, "lcd_2.png"))]
    bpy.ops.mesh.primitive_plane_add(size=1, location=(lcd["x0"] + lcd["w"] / 2, 0.3, lcd["z0"] + lcd["h"] / 2),
                                     rotation=(math.radians(90), 0, 0))
    scr = bpy.context.object; scr.scale = (lcd["w"], lcd["h"], 1)
    sm = bpy.data.materials.new("layar"); sm.use_nodes = True
    nt = sm.node_tree; nt.nodes.clear()
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = imgs[0]
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs[1].default_value = 1.6
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(tex.outputs[0], em.inputs[0]); nt.links.new(em.outputs[0], out.inputs[0])
    scr.data.materials.append(sm)

    # cahaya
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(45), math.radians(15), math.radians(-30)))
    bpy.context.object.data.energy = 3.0
    bpy.ops.object.light_add(type="AREA", location=(150, -350, 350))
    a = bpy.context.object; a.data.energy = 3e6; a.data.size = 400
    a.rotation_euler = (Vector((150, 15, 60)) - a.location).to_track_quat("-Z", "Y").to_euler()

    # kamera
    tgt = bpy.data.objects.new("target", None); bpy.context.collection.objects.link(tgt)
    bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam
    cam.data.lens = 45; cam.data.clip_end = 6000
    con = cam.constraints.new("TRACK_TO"); con.target = tgt
    con.track_axis = "TRACK_NEGATIVE_Z"; con.up_axis = "UP_Y"
    for fr, loc, tg in data["cams"]:
        cam.location = loc; cam.keyframe_insert("location", frame=fr)
        tgt.location = tg; tgt.keyframe_insert("location", frame=fr)

    # kunci frame objek
    pdepan = objs["M__dinding_depan"].data.materials[0].node_tree.nodes["Principled BSDF"]
    for i, fr in enumerate(data["frames"]):
        for k, v in fr.items():
            if k == "alpha_depan":
                pdepan.inputs["Alpha"].default_value = v
                pdepan.inputs["Alpha"].keyframe_insert("default_value", frame=i)
                continue
            o = objs[k]
            o.location = v[:3]; o.rotation_euler = v[3:]
            o.keyframe_insert("location", frame=i); o.keyframe_insert("rotation_euler", frame=i)
    sm2 = sm.copy(); sm2.node_tree.nodes["Image Texture"].image = imgs[1]
    scr.data.materials.append(sm2)
    sc.frame_set(0)

    outdir = os.path.join(tmp, "frames")
    os.makedirs(outdir, exist_ok=True)
    frames = [0, 150, 380, 470, 540, 700] if test else range(data["n"])
    for i in frames:
        sc.frame_set(i)
        for poly in scr.data.polygons:
            poly.material_index = 0 if i < 540 else 1
        sc.render.filepath = os.path.join(outdir, f"f_{i:04d}.png")
        bpy.ops.render.render(write_still=True)


def ffmpeg():
    if shutil.which("ffmpeg"):
        return shutil.which("ffmpeg")
    import glob
    hits = glob.glob(os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Packages", "Gyan.FFmpeg*", "*", "bin", "ffmpeg.exe"))
    return hits[0] if hits else "ffmpeg"


if __name__ == "__main__":
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1:]
        blender_main(args[0], "--test" in args)
    else:
        test = "--test" in sys.argv
        prepare()
        subprocess.run([BLENDER, "-b", "-P", os.path.abspath(__file__), "--", TMP] + (["--test"] if test else []),
                       check=True, stdout=subprocess.DEVNULL)
        if not test:
            os.makedirs(os.path.join(HERE, "animasi"), exist_ok=True)
            out = os.path.join(HERE, "animasi", "ARTA-C_portable_animasi.mp4")
            subprocess.run([ffmpeg(), "-y", "-framerate", str(FPS), "-i", os.path.join(TMP, "frames", "f_%04d.png"),
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", out], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("video:", out)
        else:
            print("frame uji:", os.listdir(os.path.join(TMP, "frames")))
