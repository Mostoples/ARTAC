"""Render pratinjau dengan Blender (CLI).

  python render_blender.py            -> render/*.png
Langkah 1 (python biasa): ekspor kelompok part ke _blend_tmp/*.stl
Langkah 2: menjalankan Blender -b -P render_blender.py -- <dir>
"""
import os
import subprocess
import sys

BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, "_blend_tmp")

COL = {"rangka": (0.93, 0.95, 0.97, 1), "gear": (0.15, 0.42, 0.95, 1), "kaset": (0.45, 0.68, 0.98, 1),
       "tutup": (0.72, 0.84, 1.0, 1), "pelatuk": (0.98, 0.62, 0.1, 1), "servo": (0.12, 0.14, 0.18, 1),
       "pcb": (0.85, 0.65, 0.1, 1), "lcd": (0.02, 0.03, 0.06, 1), "bat": (0.35, 0.4, 0.48, 1),
       "obat": (0.8, 0.05, 0.05, 1), "akrilik": (0.86, 0.9, 0.95, 1), "membran": (0.1, 0.1, 0.1, 1)}


def export_groups():
    sys.path.insert(0, HERE)
    import build as b
    import render as r
    os.makedirs(TMP, exist_ok=True)
    scenes = {
        "A": r.assembly(day=3, acrylic=("belakang", "depan")),
        "B": r.assembly(day=3, dz=-b.STROKE, theta=180.0, acrylic=("belakang",)),
    }
    # kaset terurai
    xl = 40.0
    ex = [("kaset", b.cas_place(b.kaset_badan_local(), xl)),
          ("tutup", b.cas_place(b.kaset_tutup_local(), xl).translate([0, 0, 22])),
          ("membran", b.box(xl, xl + b.LC, b.CAS_Y0, b.CAS_Y0 + b.DC, b.ZB + b.PLATE_T, b.ZB + b.PLATE_T + b.MEM_T)
           .translate([0, 0, -16])),
          ("kaset", b.cas_place(b.kaset_alas_local(), xl).translate([0, 0, -30]))]
    ex += [("obat", c.translate([0, 0, 0])) for c in b.caplets(xl)]
    scenes["C"] = ex
    for sc, items in scenes.items():
        groups = {}
        for kind, m in items:
            groups.setdefault(kind, []).append(m)
        for kind, ms in groups.items():
            t = b.to_tm(b.union(ms) if len(ms) > 1 else ms[0])
            t.export(os.path.join(TMP, f"{sc}__{kind}.stl"))


def blender_main(tmp):
    import bpy
    import math
    from mathutils import Vector

    def reset():
        bpy.ops.wm.read_factory_settings(use_empty=True)
        sc = bpy.context.scene
        sc.render.engine = "CYCLES"
        sc.cycles.samples = 48
        sc.cycles.use_denoising = True
        sc.render.resolution_x, sc.render.resolution_y = 1600, 1200
        sc.view_settings.view_transform = "AgX"
        w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
        w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
        w.node_tree.nodes["Background"].inputs[1].default_value = 0.9
        return sc

    def mat(kind):
        m = bpy.data.materials.new(kind); m.use_nodes = True
        bsdf = m.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = COL[kind]
        bsdf.inputs["Roughness"].default_value = 0.45
        if kind in ("gear", "kaset", "pelatuk"):
            bsdf.inputs["Roughness"].default_value = 0.35
        return m

    def load(sc_id):
        objs = []
        for f in sorted(os.listdir(tmp)):
            if f.startswith(sc_id + "__"):
                kind = f.split("__")[1][:-4]
                bpy.ops.wm.stl_import(filepath=os.path.join(tmp, f))
                o = bpy.context.selected_objects[0]
                o.data.materials.append(mat(kind))
                bpy.ops.object.shade_auto_smooth(angle=math.radians(30))
                objs.append(o)
        return objs

    def lights():
        bpy.ops.object.light_add(type="SUN", rotation=(math.radians(50), math.radians(10), math.radians(-35)))
        bpy.context.object.data.energy = 3.5
        bpy.ops.object.light_add(type="AREA", location=(100, -300, 300))
        a = bpy.context.object; a.data.energy = 2.5e6; a.data.size = 300
        a.rotation_euler = (Vector((100, 15, 80)) - a.location).to_track_quat("-Z", "Y").to_euler()

    def cam(loc, target, ortho=None, lens=60):
        bpy.ops.object.camera_add(location=loc)
        c = bpy.context.object
        c.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        c.data.clip_end = 5000
        if ortho:
            c.data.type = "ORTHO"; c.data.ortho_scale = ortho
        else:
            c.data.lens = lens
        bpy.context.scene.camera = c

    def shoot(path):
        bpy.context.scene.render.filepath = path
        bpy.ops.render.render(write_still=True)

    out = os.path.join(os.path.dirname(tmp), "render")
    jobs = [("A", "01_rakitan_iso.png", (330, -440, 360), (99, 15, 80), None, 55),
            ("B", "02_mekanisme_tanpa_dinding_depan.png", (300, -430, 330), (99, 15, 90), None, 55),
            ("B", "03_tampak_depan.png", (99, -800, 83), (99, 15, 83), 245, None),
            ("C", "04_kaset_terurai.png", (250, -230, 190), (92, 15, 70), None, 60)]
    for sc_id, name, loc, tgt, ortho, lens in jobs:
        reset(); load(sc_id); lights(); cam(loc, tgt, ortho, lens or 50)
        shoot(os.path.join(out, name))


if __name__ == "__main__":
    if "--" in sys.argv:
        blender_main(sys.argv[sys.argv.index("--") + 1])
    else:
        export_groups()
        for f in os.listdir(os.path.join(HERE, "render")):
            os.remove(os.path.join(HERE, "render", f))
        subprocess.run([BLENDER, "-b", "-P", os.path.abspath(__file__), "--", TMP], check=True,
                       stdout=subprocess.DEVNULL)
        print("render Blender selesai:", os.listdir(os.path.join(HERE, "render")))
