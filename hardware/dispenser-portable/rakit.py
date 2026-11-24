"""Gambar langkah perakitan ARTA-C Portable v2 -> rakit/langkah_XX.png (Blender EEVEE).

Setiap langkah menampilkan part yang sudah terpasang (abu-abu) + part baru langkah itu (biru).

  python rakit.py
"""
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, "_rakit_tmp")
OUTD = os.path.join(HERE, "rakit")
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"

# (judul, kelompok baru, arah kamera dari pusat (x, y, z), kelompok disembunyikan)
STEPS = [
    ("Dinding belakang + blok sudut bawah", ["back", "blok_bawah"], (-0.55, -1.0, 0.75), []),
    ("Servo 2 + braket + tuas", ["s2"], (-0.35, -1.0, 0.55), []),
    ("Servo 1 + roda gigi G1/G2", ["s1"], (-0.75, -1.0, 0.55), []),
    ("Pemandu kiri, landasan, corong", ["frame"], (-0.55, -1.0, 0.6), []),
    ("Dinding samping & bawah, rel, pemandu kanan", ["sides"], (-0.55, -1.0, 0.6), []),
    ("Kereta pelatuk + servo 3", ["car"], (-0.45, -1.0, 0.5), []),
    ("Wadah + blister dari celah atas, dinding atas", ["wadah", "top"], (-0.6, -1.0, 0.8), []),
    ("Dinding depan + elektronik (sisi dalam)", ["front"], (0.45, 1.0, 0.45), "only_front"),
    ("Rakitan selesai", ["front"], (0.55, -1.0, 0.35), []),
]


def prepare():
    sys.path.insert(0, HERE)
    import build as b
    os.makedirs(TMP, exist_ok=True)
    for f in os.listdir(TMP):
        os.remove(os.path.join(TMP, f))
    st = b.statics()
    wl = b.walls_placed()
    dm = b.dummies()
    cb = b.cb_at(1)
    base, domes, caps = b.blister_parts(cb)
    G = {
        "back": [("dinding_belakang", wl["dinding_belakang"], "part")],
        "blok_bawah": [(f"blok_{n}", st[f"blok_{n}"], "part") for n in ("BL", "BR")],
        "s2": [("braket_s2", st["braket_s2"], "part"), ("servo2", dm[1][1], "servo"), ("tuas", b.part_tuas(0.0), "part")],
        "s1": [("braket_s1", st["braket_s1"], "part"), ("servo1", dm[0][1], "servo"), ("G1", st["G1"], "part"),
               ("G2", b.part_g2(), "part"), ("spacer", st["spacer"], "part")],
        "frame": [("pemandu_kiri", st["pemandu_kiri"], "part"), ("landasan", st["landasan"], "part"),
                  ("corong", st["corong"], "part")],
        "sides": [("dinding_kiri", wl["dinding_kiri"], "part"), ("dinding_kanan", wl["dinding_kanan"], "part"),
                  ("dinding_bawah", wl["dinding_bawah"], "part"), ("pemandu_kanan", st["pemandu_kanan"], "part"),
                  ("rel", st["rel"], "part")] + [(f"blok_{n}", st[f"blok_{n}"], "part") for n in ("TL", "TR")],
        "car": [("kereta", b.kereta(b.XC), "part"), ("servo3", b.servo3_dummy(b.XC), "servo"),
                ("engkol", b.engkol3(b.XC, 0), "part"), ("pelatuk", b.pelatuk(b.XC, 0), "accent")],
        "wadah": [("wadah_belakang", b.wadah_belakang(cb), "part"), ("wadah_depan", b.wadah_depan(cb), "part"),
                  ("blister", base, "foil")] + [(f"kubah_{c}{r}", m, "dome") for (c, r), m in domes]
                 + [(f"kaplet_{c}{r}", m, "caplet") for (c, r), m in caps],
        "top": [("dinding_atas", wl["dinding_atas"], "part")],
        "front": [("dinding_depan", wl["dinding_depan"], "part"), ("klem_a", st["klem_a"], "part"),
                  ("klem_b", st["klem_b"], "part"), ("kantong_jari", st["kantong_jari"], "dark")]
                 + [(f"elek_{i}", m, k) for i, (k, m) in enumerate(dm[2:])],
    }
    meta = {}
    for g, items in G.items():
        for n, m, kind in items:
            fn = f"{g}__{n}.stl"
            b.to_tm(m).export(os.path.join(TMP, fn))
            meta[fn] = dict(group=g, kind=kind)
    json.dump(dict(parts=meta, steps=STEPS), open(os.path.join(TMP, "rakit.json"), "w"))


def blender_main():
    import bpy
    from mathutils import Vector

    data = json.load(open(os.path.join(TMP, "rakit.json")))
    sc = bpy.context.scene
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = 1400, 1000
    sc.eevee.taa_render_samples = 48
    sc.view_settings.view_transform = "Standard"
    sc.render.film_transparent = False
    world = bpy.data.worlds.new("W")
    sc.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.92, 0.94, 0.97, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.45

    def mat(name, rgb, rough=0.5, metal=0.0, alpha=1.0):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        p = m.node_tree.nodes["Principled BSDF"]
        p.inputs["Base Color"].default_value = (*rgb, 1)
        p.inputs["Roughness"].default_value = rough
        p.inputs["Metallic"].default_value = metal
        if alpha < 1:
            p.inputs["Alpha"].default_value = alpha
            m.surface_render_method = "DITHERED"
        return m

    M = {"old": mat("old", (0.62, 0.65, 0.7), 0.55), "new": mat("new", (0.02, 0.16, 0.85), 0.4),
         "servo": mat("servo", (0.05, 0.05, 0.06), 0.4), "accent": mat("accent", (1.0, 0.35, 0.03), 0.4),
         "foil": mat("foil", (0.8, 0.8, 0.82), 0.25, 1.0), "dome": mat("dome", (0.95, 0.97, 1.0), 0.1, 0.0, 0.35),
         "caplet": mat("caplet", (0.55, 0.12, 0.06), 0.35), "dark": mat("dark", (0.04, 0.04, 0.05), 0.5),
         "pcb": mat("pcb", (0.02, 0.18, 0.12), 0.4), "lcd": mat("lcd", (0.02, 0.03, 0.05), 0.15),
         "bat": mat("bat", (0.15, 0.2, 0.3), 0.5), "dht": mat("dht", (0.2, 0.45, 0.85), 0.5)}
    objs = {}
    for fn, info in data["parts"].items():
        bpy.ops.wm.stl_import(filepath=os.path.join(TMP, fn))
        o = bpy.context.selected_objects[0]
        o.scale = (0.001,) * 3
        objs[fn] = (o, info)
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 3.6
    sun.rotation_euler = (math.radians(40), math.radians(-25), math.radians(-30))
    sc.collection.objects.link(sun)
    fill = bpy.data.objects.new("fill", bpy.data.lights.new("fill", "SUN"))
    fill.data.energy = 1.2
    fill.rotation_euler = (math.radians(-50), math.radians(30), math.radians(150))
    sc.collection.objects.link(fill)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.lens = 50
    sc.collection.objects.link(cam)
    sc.camera = cam
    os.makedirs(OUTD, exist_ok=True)
    order = ["back", "blok_bawah", "s2", "s1", "frame", "sides", "car", "wadah", "top", "front"]
    done = set()
    for i, (title, new, d, hide) in enumerate(data["steps"], 1):
        vis = []
        for fn, (o, info) in objs.items():
            g = info["group"]
            show = (g in done or g in new) if hide != "only_front" else g == "front"
            o.hide_render = not show
            if not show:
                continue
            vis.append(o)
            kind = info["kind"]
            is_new = g in new and i < len(data["steps"])
            if kind in ("part",):
                m = M["new"] if is_new else M["old"]
            else:
                m = M.get(kind, M["old"])
            o.data.materials.clear()
            o.data.materials.append(m)
        done.update(new)
        # kamera membingkai part yang tampak
        pts = [o.matrix_world @ Vector(c) for o in vis for c in o.bound_box]
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        c = (lo + hi) / 2
        r = (hi - lo).length / 2
        dv = Vector(d).normalized()
        dist = r / math.tan(math.radians(18)) * 1.32
        cam.location = c + dv * dist
        cam.rotation_euler = (-dv).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(OUTD, f"langkah_{i:02d}.png")
        bpy.ops.render.render(write_still=True)
        print("LANGKAH", i, title)


if __name__ == "__main__":
    if "--" in sys.argv:
        blender_main()
    else:
        prepare()
        r = subprocess.run([BLENDER, "-b", "--factory-startup", "-P", os.path.abspath(__file__), "--"],
                           capture_output=True, text=True)
        print("\n".join(l for l in r.stdout.splitlines() if l.startswith("LANGKAH") or "Error" in l))
        if r.returncode:
            print(r.stderr[-2000:])
