"""Video rancangan teknik ARTA-C Portable v2: rakitan berputar -> terurai (exploded) berlabel -> dirakit kembali.

  python video_teknik.py          -> animasi/ARTA-C_rancangan_teknik_exploded.mp4 (1920x1080)
  python video_teknik.py --test   -> beberapa frame uji
"""
import json
import math
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, "_vt_tmp")
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
FPS, N = 30, 750
RES = (1920, 1080)

COLORS = {   # kelompok warna
    "dinding": (0.84, 0.88, 0.93), "rangka": (0.95, 0.96, 0.98), "gerak": (0.98, 0.58, 0.12),
    "gear": (0.16, 0.45, 0.95), "wadah": (0.45, 0.68, 0.98), "jari": (0.06, 0.07, 0.09),
    "servo": (0.1, 0.12, 0.15), "pcb": (0.1, 0.42, 0.22), "pcb_y": (0.85, 0.65, 0.1), "lcd": (0.02, 0.03, 0.06),
    "bat": (0.3, 0.36, 0.45), "obat": (0.78, 0.05, 0.06), "foil": (0.8, 0.81, 0.84), "dht": (0.2, 0.6, 0.95),
}
GROUP = {"kereta": "gerak", "pelatuk": "gerak", "engkol_servo3": "gerak", "tuas_servo2": "gerak",
         "gear_G1": "gear", "gear_G2": "gear", "spacer_G2": "gear", "wadah_belakang": "wadah",
         "wadah_depan": "wadah", "kantong_jari_ppg": "jari"}
LABELS = {   # label pada video (nama singkat)
    "dinding_depan": "Dinding depan + layar & sensor", "dinding_belakang": "Dinding belakang", "dinding_atas": "Dinding atas (celah wadah)",
    "dinding_bawah": "Dinding bawah", "dinding_kiri": "Dinding kiri (port USB-C)", "dinding_kanan": "Dinding kanan",
    "kantong_jari_ppg": "Kantong jari PPG (MAX30102)", "rel_kereta": "Rel kereta", "kereta": "Kereta pelatuk + servo 3",
    "pelatuk": "Pelatuk", "tuas_servo2": "Tuas servo 2", "gear_G1": "Roda gigi G1 (z40)", "gear_G2": "Roda gigi G2 (z36/z12)",
    "pemandu_kiri": "Pemandu kiri", "pemandu_kanan": "Pemandu kanan", "landasan": "Landasan",
    "corong_baki": "Corong & baki obat", "wadah_belakang": "Wadah blister (rack)", "wadah_depan": "Bingkai wadah",
    "braket_servo1": "Braket servo 1", "braket_servo2": "Braket servo 2", "_esp32cam": "ESP32-CAM",
    "_baterai": "Baterai LiPo 2000 mAh", "_ip5306": "Modul cas IP5306 (USB-C)", "_cyd": "Layar CYD 2,8\" (LVGL)",
    "_dht": "DHT11", "_buzzer": "Buzzer", "_blister": "Blister obat utuh",
}
CAPTIONS = [(0, 90, "ARTA-C Portable v2  -  rancangan teknik"),
            (90, 240, "Gambar urai: seluruh part cetak 3D dan komponen elektronik"),
            (240, 480, "29 file STL cetak  -  3 servo MG90S  -  ESP32 CYD + ESP32-CAM  -  MAX30102  -  DHT11  -  LiPo + USB-C"),
            (480, 600, "Mekanisme: wadah turun baris demi baris, kereta pelatuk kiri-kanan, pelatuk mendorong kaplet"),
            (600, 750, "Dirakit kembali  -  168 x 206 x 54 mm  -  +/-555 g filamen")]


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def prepare():
    sys.path.insert(0, HERE)
    import build as b
    import gambar_teknik as gt
    os.makedirs(TMP, exist_ok=True)
    for f in os.listdir(TMP):
        p = os.path.join(TMP, f)
        if os.path.isfile(p):
            os.remove(p)
    _, parts = gt.parts_device()
    objs = []

    def add(name, m, color, explode, label=True):
        b.to_tm(m).export(os.path.join(TMP, f"{name}.stl"))
        objs.append(dict(name=name, color=color, explode=explode, label=label and name in LABELS))

    for n, m in parts.items():
        grp = GROUP.get(n, "dinding" if n.startswith("dinding") else "rangka")
        add(n, m, COLORS[grp], gt.EXPLODE.get(n, (0, 0, 0)))
    # elektronik & blister (ikut part induknya saat diurai)
    d = b.dummies()
    ex_front = gt.EXPLODE["dinding_depan"]
    add("_servo1", d[0][1], COLORS["servo"], (-60, 70, 0), False)
    add("_servo2", d[1][1], COLORS["servo"], (0, 60, -60), False)
    add("_cyd", d[2][1], COLORS["pcb_y"], (0, -120, 0))
    add("_lcd", d[3][1], (0.05, 0.25, 0.65), (0, -120, 0), False)
    add("_baterai", d[4][1], COLORS["bat"], (-20, -120, -20))
    add("_ip5306", d[5][1], COLORS["pcb"], (-60, -110, 0))
    add("_esp32cam", d[6][1], COLORS["pcb"], (-20, -130, 30))
    add("_kamera", b.union([d[7][1], d[8][1]]), COLORS["servo"], (-20, -130, 30), False)
    add("_buzzer", d[9][1], COLORS["servo"], (-30, -125, 10))
    add("_max30102", b.union([d[10][1], d[11][1]]), COLORS["pcb"], (0, -265, -55), False)
    add("_dht", b.union([d[12][1], d[13][1]]), COLORS["dht"], (20, -125, -10))
    add("_servo3", b.servo3_dummy(b.XC), COLORS["servo"], gt.EXPLODE["kereta"], False)
    cb = b.cb_at(1)
    base, domes, caps = b.blister_parts(cb)
    ex_w = gt.EXPLODE["wadah_belakang"]
    add("_blister", b.union([base] + [m for _, m in domes]), COLORS["foil"], (ex_w[0], ex_w[1] - 20, ex_w[2] + 40))
    add("_kaplet", b.union([m for _, m in caps]), COLORS["obat"], (ex_w[0], ex_w[1] - 20, ex_w[2] + 40), False)
    # lintasan: urai bertahap per kelompok
    order = {n["name"]: i for i, n in enumerate(objs)}
    frames = []
    for f in range(N):
        fr = {}
        for o in objs:
            k = order[o["name"]] / max(1, len(objs) - 1)
            a0 = 90 + 60 * k
            e = ease((f - a0) / 90.0) if f < 600 else 1 - ease((f - 600 - 40 * (1 - k)) / 90.0)
            fr[o["name"]] = [c * e for c in o["explode"]]
        ang = math.radians(-35 + 360 * ease((f - 240) / 240.0) + 20 * min(1, f / 240))
        frames.append(dict(off=fr, cam_ang=ang))
    cap = {f: next((c[2] for c in CAPTIONS if c[0] <= f < c[1]), "") for f in range(N)}
    json.dump(dict(objs=objs, frames=frames, n=N, fps=FPS, res=RES, center=(b.W / 2, b.D / 2, b.H / 2 + 20)),
              open(os.path.join(TMP, "vt.json"), "w"))
    json.dump(cap, open(os.path.join(TMP, "captions.json"), "w"))


def blender_main(tmp, frames_sel):
    import bpy
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector

    data = json.load(open(os.path.join(tmp, "vt.json")))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = data["res"]
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Medium High Contrast"
        sc.eevee.taa_render_samples = 48
        sc.eevee.use_raytracing = True
    except Exception:
        pass
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.9, 0.93, 0.97, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.45
    objs = {}
    for o in data["objs"]:
        bpy.ops.wm.stl_import(filepath=os.path.join(tmp, o["name"] + ".stl"))
        ob = bpy.context.selected_objects[0]
        m = bpy.data.materials.new(o["name"]); m.use_nodes = True
        p = m.node_tree.nodes["Principled BSDF"]
        p.inputs["Base Color"].default_value = (*o["color"], 1)
        p.inputs["Roughness"].default_value = 0.42 if o["name"].startswith("dinding") else 0.35
        if o["name"] == "_blister":
            p.inputs["Metallic"].default_value = 0.6
        if o["name"] == "_lcd":
            p.inputs["Emission Color"].default_value = (0.15, 0.45, 1.0, 1)
            p.inputs["Emission Strength"].default_value = 1.5
        ob.data.materials.append(m)
        bpy.ops.object.shade_auto_smooth(angle=math.radians(30))
        ob["home"] = list(ob.location)
        objs[o["name"]] = (ob, o)
    bpy.ops.mesh.primitive_plane_add(size=6000, location=(80, 20, -240))
    pl = bpy.context.object
    pm = bpy.data.materials.new("lantai"); pm.use_nodes = True
    pm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.93, 0.94, 0.96, 1)
    pm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.3
    pl.data.materials.append(pm)
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(40), math.radians(12), math.radians(-30)))
    bpy.context.object.data.energy = 3.2
    bpy.ops.object.light_add(type="AREA", location=(250, -500, 500))
    a = bpy.context.object; a.data.energy = 5e6; a.data.size = 600
    a.rotation_euler = (Vector((80, 20, 100)) - a.location).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.object.light_add(type="AREA", location=(-400, 400, 300))
    a2 = bpy.context.object; a2.data.energy = 2e6; a2.data.size = 500
    a2.rotation_euler = (Vector((80, 20, 100)) - a2.location).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam
    cam.data.lens = 50; cam.data.clip_end = 10000
    cx, cy, cz = data["center"]
    out = os.path.join(tmp, "frames"); os.makedirs(out, exist_ok=True)
    labels = {}
    for i in frames_sel:
        fr = data["frames"][i]
        for name, (ob, o) in objs.items():
            ob.location = Vector(fr["off"][name])
        e = max(abs(v) for v in fr["off"]["dinding_depan"]) / 170.0
        dist = 640 + 560 * e
        a = fr["cam_ang"]
        cam.location = Vector((cx + dist * math.sin(a), cy - dist * math.cos(a), cz + 210 + 170 * e))
        tgt = Vector((cx, cy, cz + 55 * e))
        cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        sc.render.filepath = os.path.join(out, f"f_{i:04d}.png")
        bpy.ops.render.render(write_still=True)
        lab = {}
        for name, (ob, o) in objs.items():
            if not o["label"]:
                continue
            bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
            ctr = sum(bb, Vector()) / 8
            p = world_to_camera_view(sc, cam, ctr)
            lab[name] = (p.x, 1 - p.y, p.z)
        labels[i] = lab
    json.dump(labels, open(os.path.join(tmp, f"labels_{frames_sel[0]}.json"), "w"))


def overlay():
    """Label part + keterangan (PIL) di atas frame render."""
    from PIL import Image, ImageDraw, ImageFont
    cap = json.load(open(os.path.join(TMP, "captions.json")))
    data = json.load(open(os.path.join(TMP, "vt.json")))
    labels = {}
    for f in os.listdir(TMP):
        if f.startswith("labels_"):
            labels.update({int(k): v for k, v in json.load(open(os.path.join(TMP, f))).items()})
    fnt = lambda s: ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", s)
    fb = lambda s: ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", s)
    out = os.path.join(TMP, "final"); os.makedirs(out, exist_ok=True)
    W, H = data["res"]
    for f in sorted(labels):
        im = Image.open(os.path.join(TMP, "frames", f"f_{f:04d}.png")).convert("RGB")
        d = ImageDraw.Draw(im, "RGBA")
        e = max(abs(v) for v in data["frames"][f]["off"]["dinding_depan"]) / 170.0
        if e > 0.6:
            alpha = int(255 * min(1, (e - 0.6) / 0.3))
            pts = sorted(labels[f].items(), key=lambda kv: kv[1][1])
            used = []
            for name, (u, v, z) in pts:
                if z <= 0 or not (0.03 < u < 0.97 and 0.06 < v < 0.86):
                    continue
                px, py = u * W, v * H
                side = 1 if px > W / 2 else -1
                lx = px + side * 70
                ly = py - 26
                for uy in used:
                    if abs(uy[1] - ly) < 30 and abs(uy[0] - lx) < 330:
                        ly = uy[1] + 31
                used.append((lx, ly))
                txt = LABELS[name]
                tw = d.textlength(txt, font=fnt(22))
                bx0 = lx if side > 0 else lx - tw - 16
                d.line([(px, py), (lx, ly + 15)], fill=(29, 78, 216, alpha), width=2)
                d.ellipse([px - 4, py - 4, px + 4, py + 4], fill=(29, 78, 216, alpha))
                d.rounded_rectangle([bx0, ly, bx0 + tw + 16, ly + 31], 7, fill=(255, 255, 255, int(alpha * 0.92)),
                                    outline=(29, 78, 216, alpha), width=2)
                d.text((bx0 + 8, ly + 2), txt, font=fnt(22), fill=(15, 23, 42, alpha))
        c = cap.get(str(f), "")
        if c:
            tw = d.textlength(c, font=fb(32))
            d.rounded_rectangle([(W - tw) / 2 - 24, H - 96, (W + tw) / 2 + 24, H - 40], 14, fill=(15, 23, 42, 200))
            d.text(((W - tw) / 2, H - 92), c, font=fb(32), fill=(255, 255, 255, 255))
        d.text((30, 24), "ARTA-C Portable v2", font=fb(30), fill=(29, 78, 216, 255))
        d.text((30, 60), "Rancangan teknik  |  gambar urai", font=fnt(22), fill=(51, 65, 85, 255))
        im.save(os.path.join(out, f"f_{f:04d}.png"))


def ffmpeg():
    import glob
    if shutil.which("ffmpeg"):
        return shutil.which("ffmpeg")
    hits = glob.glob(os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Packages",
                                  "Gyan.FFmpeg*", "*", "bin", "ffmpeg.exe"))
    return hits[0] if hits else "ffmpeg"


if __name__ == "__main__":
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1:]
        fs = [int(x) for x in args[1].split(",")] if len(args) > 1 else list(range(N))
        blender_main(args[0], fs)
        sys.exit(0)
    test = "--test" in sys.argv
    prepare()
    for d in ("frames", "final"):
        p = os.path.join(TMP, d)
        if os.path.isdir(p):
            shutil.rmtree(p)
    sel = "0,150,300,420,560,700" if test else ",".join(str(i) for i in range(N))
    subprocess.run([BLENDER, "-b", "-P", os.path.abspath(__file__), "--", TMP, sel], check=True,
                   stdout=subprocess.DEVNULL)
    overlay()
    if not test:
        os.makedirs(os.path.join(HERE, "animasi"), exist_ok=True)
        out = os.path.join(HERE, "animasi", "ARTA-C_rancangan_teknik_exploded.mp4")
        subprocess.run([ffmpeg(), "-y", "-framerate", str(FPS), "-i", os.path.join(TMP, "final", "f_%04d.png"),
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", out], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        shutil.copy(os.path.join(TMP, "final", "f_0420.png"), os.path.join(HERE, "render", "07_gambar_urai_berlabel.png"))
        print("video:", out)
    print("selesai")
