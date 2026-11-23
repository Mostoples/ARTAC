"""Ikon 3D ARTA-C (Blender CLI, Cycles, latar transparan) - gaya AQUENT putih-biru.

  blender -b --factory-startup -P ikon3d.py -- <out_dir> [nama...] [--size 512]
"""
import math
import os
import sys

import bpy
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(ARGS[0]) if ARGS else os.path.join(os.path.dirname(os.path.abspath(__file__)), "ikon")
SIZE = int(ARGS[ARGS.index("--size") + 1]) if "--size" in ARGS else 512
ONLY = [a for a in ARGS[1:] if not a.startswith("--") and not a.isdigit()]

BLUE, DEEP, ICE, WHITE = (0.184, 0.482, 1.0), (0.086, 0.275, 0.84), (0.867, 0.922, 1.0), (0.96, 0.97, 0.99)
RED, OK, WARN = (0.86, 0.12, 0.14), (0.098, 0.725, 0.478), (0.96, 0.647, 0.141)
REG = {}


def asset(name):
    def deco(f):
        REG[name] = f
        return f
    return deco


def srgb(c):
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


def mat(name, color, rough=0.35, metal=0.0, emit=0.0, glass=False):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*srgb(color), 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    p.inputs["Coat Weight"].default_value = 0.6
    p.inputs["Coat Roughness"].default_value = 0.08
    if emit:
        p.inputs["Emission Color"].default_value = (*srgb(color), 1)
        p.inputs["Emission Strength"].default_value = emit
    if glass:
        p.inputs["Transmission Weight"].default_value = 0.85
        p.inputs["Roughness"].default_value = 0.05
        p.inputs["IOR"].default_value = 1.45
    return m


def put(o, m, smooth=True):
    o.data.materials.clear(); o.data.materials.append(m)
    if smooth and o.type == "MESH":
        for pl in o.data.polygons:
            pl.use_smooth = True
    return o


def bevel(o, w=0.04, seg=4):
    b = o.modifiers.new("bv", "BEVEL"); b.width = w; b.segments = seg; b.limit_method = "ANGLE"
    return o


def capsule(r, L, m, loc=(0, 0, 0), rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=L, vertices=64, location=(0, 0, 0))
    c = bpy.context.object
    objs = [c]
    for s in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=64, ring_count=32, location=(0, 0, s * L / 2))
        objs.append(bpy.context.object)
    for o in objs:
        put(o, m)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = c
    bpy.ops.object.join()
    c.location = loc; c.rotation_euler = rot
    return c


def rbox(sx, sy, sz, m, loc=(0, 0, 0), r=0.15):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.scale = (sx, sy, sz)
    bpy.ops.object.transform_apply(scale=True)
    bevel(o, r, 6)
    return put(o, m)


# ------------------------------------------------------------------ ikon
@asset("pil")
def pil():
    mr, mw = mat("merah", RED, 0.22), mat("putih", WHITE, 0.3)
    parts = []
    for sgn, m in ((-1, mr), (1, mw)):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.42, depth=0.62, vertices=64, location=(sgn * 0.31, 0, 0),
                                            rotation=(0, math.radians(90), 0))
        parts.append(put(bpy.context.object, m))
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.42, segments=64, ring_count=32, location=(sgn * 0.62, 0, 0))
        parts.append(put(bpy.context.object, m))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.425, minor_radius=0.012, location=(0, 0, 0), rotation=(0, math.radians(90), 0))
    parts.append(put(bpy.context.object, mat("garis", (0.75, 0.78, 0.84), 0.3)))
    bpy.ops.object.empty_add(location=(0, 0, 0))
    root = bpy.context.object
    for p in parts:
        p.parent = root
    root.rotation_euler = (math.radians(15), math.radians(-28), math.radians(25))


@asset("jantung")
def jantung():
    import bmesh
    me = bpy.data.meshes.new("hati"); o = bpy.data.objects.new("hati", me); bpy.context.collection.objects.link(o)
    bm = bmesh.new()
    pts = []
    for k in range(160):
        t = 2 * math.pi * k / 160
        x = 16 * math.sin(t) ** 3
        z = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append(bm.verts.new((x / 16, 0.18, z / 16)))
    f = bm.faces.new(pts)
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    vs = [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, -0.36, 0), verts=vs)
    bm.to_mesh(me); bm.free()
    bpy.context.view_layer.objects.active = o
    b = o.modifiers.new("bv", "BEVEL"); b.width = 0.17; b.segments = 10; b.limit_method = "NONE"
    s_ = o.modifiers.new("sub", "SUBSURF"); s_.levels = 2; s_.render_levels = 2
    put(o, mat("hati", (0.93, 0.2, 0.3), 0.18, emit=0.15))
    bpy.ops.curve.primitive_bezier_curve_add()
    cv = bpy.context.object
    pts2 = [(-1.35, 0), (-0.55, 0), (-0.32, 0.45), (-0.08, -0.5), (0.18, 0.28), (0.36, 0), (1.35, 0)]
    sp = cv.data.splines[0]
    sp.bezier_points.add(len(pts2) - 2)
    for bp, (x, z) in zip(sp.bezier_points, pts2):
        bp.co = (x, -0.5, z - 0.05); bp.handle_left_type = bp.handle_right_type = "VECTOR"
    cv.data.bevel_depth = 0.05; cv.data.bevel_resolution = 6
    cv.data.materials.append(mat("putih_glow", WHITE, 0.2, emit=0.8))


@asset("wajah")
def wajah():
    mb = mat("biru", BLUE, 0.25, emit=0.25)
    for sx in (-1, 1):
        for sz in (-1, 1):
            rbox(0.55, 0.16, 0.16, mb, (sx * 0.78, 0, sz * 1.0), 0.07)
            rbox(0.16, 0.16, 0.55, mb, (sx * 1.0, 0, sz * 0.78), 0.07)
    mw = mat("putih", WHITE, 0.3)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.42, segments=64, ring_count=32, location=(0, 0, 0.3))
    put(bpy.context.object, mw)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.62, segments=64, ring_count=32, location=(0, 0, -0.62))
    o = bpy.context.object; o.scale = (1, 0.7, 0.62); put(o, mw)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.85, minor_radius=0.03, location=(0, 0, -0.02), rotation=(math.radians(90), 0, 0))
    put(bpy.context.object, mat("scan", BLUE, 0.2, emit=2.0))


@asset("blister")
def blister():
    rbox(2.2, 0.12, 1.5, mat("foil", (0.82, 0.84, 0.88), 0.25, metal=0.9), (0, 0, 0), 0.1)
    mr = mat("merah", RED, 0.22)
    mk = mat("kubah", ICE, glass=True)
    for i in range(4):
        for j in range(2):
            x, z = -0.78 + i * 0.52, -0.33 + j * 0.66
            capsule(0.15, 0.22, mr, (x, -0.13, z), (0, math.radians(90), 0))
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.24, segments=48, ring_count=24, location=(x, -0.06, z))
            d = bpy.context.object; d.scale = (1.15, 0.55, 0.8); put(d, mk)


@asset("centang")
def centang():
    bpy.ops.mesh.primitive_cylinder_add(radius=1.05, depth=0.35, vertices=96, rotation=(math.radians(90), 0, 0))
    o = bpy.context.object; bevel(o, 0.12, 8); put(o, mat("ok", OK, 0.25, emit=0.15))
    bpy.ops.curve.primitive_bezier_curve_add()
    cv = bpy.context.object
    sp = cv.data.splines[0]
    sp.bezier_points.add(1)
    for bp, (x, z) in zip(sp.bezier_points, [(-0.5, 0.02), (-0.12, -0.38), (0.55, 0.38)]):
        bp.co = (x, -0.22, z); bp.handle_left_type = bp.handle_right_type = "VECTOR"
    cv.data.bevel_depth = 0.12; cv.data.bevel_resolution = 8
    cv.data.materials.append(mat("putih", WHITE, 0.3))


@asset("tetes")
def tetes():
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.8, segments=96, ring_count=48, location=(0, 0, -0.25))
    o = bpy.context.object
    for v in o.data.vertices:
        if v.co.z > 0:
            k = min(1.0, v.co.z / 0.8)
            v.co.x *= (1 - k) ** 1.6
            v.co.y *= (1 - k) ** 1.6
            v.co.z *= 1 + 0.95 * k
    put(o, mat("air", BLUE, glass=True))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.33, segments=48, ring_count=24, location=(0.05, 0, -0.35))
    put(bpy.context.object, mat("inti", DEEP, 0.2, emit=0.6))


@asset("termometer")
def termometer():
    mw = mat("putih", WHITE, 0.3)
    capsule(0.32, 1.6, mw, (0, 0, 0.35))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.55, segments=64, ring_count=32, location=(0, 0, -0.85))
    put(bpy.context.object, mat("biru", BLUE, 0.25, emit=0.3))
    capsule(0.14, 1.1, mat("biru", BLUE, 0.25, emit=0.3), (0, -0.2, 0.0))
    for k in range(4):
        rbox(0.22, 0.06, 0.04, mat("garis", (0.55, 0.62, 0.76), 0.4), (0.28, -0.3, 0.1 + 0.28 * k), 0.015)


@asset("lonceng")
def lonceng():
    prof = [(0.0, 1.0), (0.18, 1.0), (0.22, 0.9), (0.5, 0.75), (0.68, 0.3), (0.78, -0.35), (1.0, -0.55), (1.0, -0.65), (0.0, -0.65)]
    import bmesh
    me = bpy.data.meshes.new("bell"); o = bpy.data.objects.new("bell", me); bpy.context.collection.objects.link(o)
    bm = bmesh.new()
    vs = [bm.verts.new((x, 0, z)) for x, z in prof]
    for a, b in zip(vs[:-1], vs[1:]):
        bm.edges.new((a, b))
    bmesh.ops.spin(bm, geom=bm.verts[:] + bm.edges[:], cent=(0, 0, 0), axis=(0, 0, 1), angle=math.radians(360), steps=96)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bm.to_mesh(me); bm.free()
    put(o, mat("kuning", WARN, 0.25, emit=0.1))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, segments=48, ring_count=24, location=(0, 0, -0.78))
    put(bpy.context.object, mat("biru", BLUE, 0.25, emit=0.3))


@asset("baterai")
def baterai():
    rbox(1.0, 0.7, 1.8, mat("kaca", ICE, glass=True), (0, 0, 0), 0.22)
    rbox(0.4, 0.4, 0.18, mat("putih", WHITE, 0.3), (0, 0, 0.98), 0.06)
    rbox(0.78, 0.5, 1.15, mat("ok", OK, 0.25, emit=0.5), (0, 0, -0.25), 0.15)


@asset("wadah")
def wadah():
    rbox(1.5, 0.18, 2.2, mat("biru_muda", (0.55, 0.72, 0.98), 0.3), (0, 0, 0), 0.1)
    mr = mat("merah", RED, 0.22)
    for i in range(2):
        for j in range(4):
            capsule(0.13, 0.26, mr, (-0.33 + i * 0.66, -0.15, -0.75 + j * 0.5), (0, math.radians(90), 0))
    rbox(0.6, 0.2, 0.16, mat("putih", WHITE, 0.3), (0, 0, 0.98), 0.07)


# ------------------------------------------------------------------ render
def setup():
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for t in ("OPTIX", "CUDA"):
            try:
                prefs.compute_device_type = t; prefs.get_devices()
                for d in prefs.devices:
                    d.use = True
                sc.cycles.device = "GPU"; break
            except Exception:
                pass
    except Exception:
        pass
    sc.cycles.samples = 96; sc.cycles.use_denoising = True
    sc.render.film_transparent = True
    sc.view_settings.view_transform = "Standard"; sc.view_settings.exposure = -0.35
    sc.render.resolution_x = sc.render.resolution_y = SIZE
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.86, 0.9, 0.97, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.7
    bpy.ops.object.light_add(type="AREA", location=(-3, -4, 5))
    k = bpy.context.object; k.data.energy = 900; k.data.size = 5
    k.rotation_euler = (Vector((0, 0, 0)) - k.location).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.object.light_add(type="AREA", location=(4, 2, 1.5))
    r = bpy.context.object; r.data.energy = 600; r.data.size = 3; r.data.color = (0.45, 0.65, 1.0)
    r.rotation_euler = (Vector((0, 0, 0)) - r.location).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.object.camera_add(location=(2.2, -7.5, 2.4))
    cam = bpy.context.object; sc.camera = cam
    cam.data.type = "ORTHO"
    cam.rotation_euler = (Vector((0, 0, 0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    return cam


def frame_cam(cam):
    objs = [o for o in bpy.context.scene.objects if o.type in ("MESH", "CURVE")]
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    c = (lo + hi) / 2
    for o in objs:
        o.location -= c
    cam.data.ortho_scale = max(hi - lo) * 1.32


os.makedirs(OUT, exist_ok=True)
for name, fn in REG.items():
    if ONLY and name not in ONLY:
        continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    cam = setup()
    fn()
    bpy.context.view_layer.update()
    frame_cam(cam)
    bpy.context.scene.render.filepath = os.path.join(OUT, f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print("ikon:", name)
