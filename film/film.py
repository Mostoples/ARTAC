"""ARTA-C "Day 47" - shot 3D sinematik (Blender 5.2 EEVEE, 1920x816, 24 fps).

  python film.py SHOT [--test f1,f2,..]      ->  _frames/SHOT/f_####.png
  python film.py all                          ->  render semua shot berurutan

Model: public/showcase/artac.glb (koordinat alat, mm, z ke atas setelah diputar balik).
Kinematika diporting dari showcase/index.html (wadah turun per baris, kereta, engkol, pelatuk).
"""
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GLB = os.path.join(ROOT, "public", "showcase", "artac.glb")
META = os.path.join(ROOT, "public", "showcase", "artac.json")
LAYAR = os.path.join(ROOT, "ui3d", "layar")
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
FPS, RW, RH = 24, 1920, 816

# shot 3D: (mulai detik di film, durasi detik, set)
SHOTS = {
    "dawn":   (0.0, 8.5, "kitchen"),
    "reveal": (35.0, 6.5, "studio"),
    "face":   (41.5, 4.5, "studio"),
    "ppg":    (46.0, 6.5, "studio"),
    "inside": (52.5, 7.0, "studio"),
    "peck":   (59.5, 8.5, "studio"),
    "notify": (68.0, 9.0, "studio"),
    "end":    (82.5, 7.5, "studio"),
}


def nframes(shot):
    return int(round(SHOTS[shot][1] * FPS))


# ---------------------------------------------------------------- util waktu
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_io(t):          # lebih lembut dari smoothstep (quintic)
    t = clamp(t)
    return t * t * t * (t * (6 * t - 15) + 10)


def seg(t, a, b):
    return clamp((t - a) / (b - a)) if b > a else float(t >= a)


def lerp(a, b, t):
    if isinstance(a, (list, tuple)):
        return [x + (y - x) * t for x, y in zip(a, b)]
    return a + (b - a) * t


def keys(t, ks, fn=ease_io):
    """ks: [(t, value), ...] -> nilai terinterpolasi (ease per segmen)."""
    if t <= ks[0][0]:
        return ks[0][1]
    for (t0, v0), (t1, v1) in zip(ks, ks[1:]):
        if t <= t1:
            return lerp(v0, v1, fn(seg(t, t0, t1)))
    return ks[-1][1]


# ---------------------------------------------------------------- state per shot
M = json.load(open(META))
EJ = M["CB_EJ"] - M["CB1"]            # 18 mm: wadah di posisi masuk
ROW = M["PZ"]
PECK_COL, PECK_ROW = 2, 3             # hari ke-47: baris 1-2 sudah habis
DROW = -(PECK_ROW - 1) * ROW          # offset wadah agar baris 3 di garis pelatuk
CARX = M["cols"][PECK_COL - 1] - M["XC"]


def state(shot, t):
    """Semua besaran animasi (mm/derajat/0..1) pada detik lokal t."""
    s = dict(wadahZ=DROW, carX=0.0, theta=0.0, cap=0.0, wall=1.0, screens={"home": 1.0}, finger=None,
             glow=0.0, key=1.0, rim=1.0, sun=1.0, turn=0.0, screen_e=1.0)
    if shot == "dawn":
        s["sun"] = lerp(0.25, 1.0, smooth(seg(t, 0.0, 6.5)))
        s["screens"] = {"home": 1.0}
    elif shot == "reveal":
        s["key"] = smooth(seg(t, 1.4, 4.6))
        s["rim"] = lerp(0.25, 1.0, smooth(seg(t, 0.0, 2.5)))
        on = smooth(seg(t, 3.4, 3.9))
        s["screen_e"] = on
        s["screens"] = {"boot": 1.0 - smooth(seg(t, 5.2, 5.7)), "home": smooth(seg(t, 5.2, 5.7))}
    elif shot == "face":
        k = smooth(seg(t, 1.5, 1.9))
        s["screens"] = {"alarm": 1 - k, "face": k}
    elif shot == "ppg":
        s["finger"] = keys(t, [(0.3, -230.0), (2.3, -14.0)])
        s["glow"] = smooth(seg(t, 2.4, 2.9))
        k = smooth(seg(t, 2.6, 3.0))
        s["screens"] = {"face": 1 - k, "ppg": k}
    elif shot == "inside":
        s["wall"] = lerp(1.0, 0.1, smooth(seg(t, 0.2, 1.4)))
        s["wadahZ"] = keys(t, [(0.0, EJ), (1.4, EJ), (2.3, 0.0), (2.9, 0.0), (3.8, -ROW), (4.3, -ROW), (5.2, DROW)])
        s["carX"] = keys(t, [(5.0, 0.0), (6.6, CARX)])
        s["screens"] = {"dispense": 1.0}
    elif shot == "peck":
        s["wall"] = 0.1
        s["hide"] = ["dinding_belakang", "dinding_atas", "elek_baterai", "elek_ip5306", "rangka_blok_BL", "rangka_blok_BR",
                     "rangka_blok_TL", "rangka_blok_TR", "dinding_kiri"]
        s["carX"] = CARX
        s["theta"] = keys(t, [(0.6, 0.0), (2.4, 180.0), (4.6, 180.0), (5.6, 0.0)])
        s["cap"] = keys(t, [(1.3, 0.0), (2.4, 0.3), (4.8, 1.0)], fn=lambda x: x)
        s["screens"] = {"dispense": 1.0}
    elif shot == "notify":
        s["wall"] = lerp(0.1, 1.0, smooth(seg(t, 0.0, 1.2)))
        s["cap"] = 1.0
        k = smooth(seg(t, 0.4, 0.9))
        s["screens"] = {"dispense": 1 - k, "done": k}
    elif shot == "end":
        s["cap"] = 1.0
        s["turn"] = lerp(-24.0, 16.0, t / SHOTS["end"][1])
        s["screens"] = {"done": 1.0 - smooth(seg(t, 3.0, 3.6)), "home": smooth(seg(t, 3.0, 3.6))}
        s["key"] = 1.0 - 0.25 * smooth(seg(t, 5.0, 7.5))
    return s


# kamera: (t, posisi, target, lensa mm) relatif ke titik acuan bernama (meter dunia)
def camera(shot, t, P):
    if shot == "dawn":
        k = keys(t, [(0.0, 0.0), (8.5, 1.0)], fn=lambda x: x)
        pos = lerp([0.62, -1.02, 0.30], [0.40, -0.72, 0.205], ease_io(k * 0.9 + 0.1 * k * k))
        tgt = lerp([0.02, 0.0, 0.095], [0.0, 0.0, 0.105], k)
        return pos, tgt, 40, 2.2
    if shot == "reveal":
        a = math.radians(lerp(-62, -12, ease_io(t / 6.5)))
        r = lerp(0.85, 0.72, ease_io(t / 6.5))
        pos = [r * math.sin(a), -r * math.cos(a), lerp(0.06, 0.13, ease_io(t / 6.5))]
        return pos, [0.0, 0.0, 0.1], 45, 4.0
    if shot == "face":
        c = P["face"]
        pos = lerp([c[0] + 0.05, c[1] - 0.44, c[2] + 0.06], [c[0] + 0.02, c[1] - 0.35, c[2] + 0.035], ease_io(t / 4.5))
        return pos, c, 55, 4.0
    if shot == "ppg":
        c = P["tunnel"]
        pos = lerp([c[0] - 0.20, c[1] - 0.22, c[2] + 0.07], [c[0] - 0.14, c[1] - 0.17, c[2] + 0.05], ease_io(t / 6.5))
        tgt = [c[0] + 0.012, c[1] + 0.02, c[2] + 0.012]
        return pos, tgt, 60, 3.2
    if shot == "inside":
        c = P["mech"]
        a = math.radians(lerp(-38, -18, ease_io(t / 7.0)))
        r = 0.48
        pos = [c[0] + r * math.sin(a), c[1] - r * math.cos(a), c[2] + lerp(0.16, 0.11, ease_io(t / 7.0))]
        return pos, c, 50, 5.6
    if shot == "peck":
        c = P["cap"]
        fall = P["tray"]
        # cutaway dari belakang: kaplet menembus foil ke arah kamera lalu jatuh ke baki
        k = smooth(seg(t, 2.6, 4.2))
        tgt = lerp([c[0], c[1] + 0.012, c[2]], [c[0], c[1] + 0.02, c[2] - 0.03], k)
        tgt = lerp(tgt, P["mech"], smooth(seg(t, 5.4, 8.5)))
        pos = lerp([c[0] - 0.10, c[1] + 0.20, c[2] + 0.07], [c[0] - 0.08, c[1] + 0.16, c[2] + 0.045], ease_io(t / 8.5))
        pos = lerp(pos, [pos[0] - 0.09, pos[1] + 0.22, pos[2] + 0.03], smooth(seg(t, 5.4, 8.5)))
        return pos, tgt, 70, 5.0
    if shot == "notify":
        pos = lerp([0.16, -0.80, 0.15], [0.13, -0.68, 0.135], ease_io(t / 9.0))
        return pos, [0.11, 0.0, 0.1], 40, 3.5
    if shot == "end":
        return [-0.02, -0.78, 0.13], [-0.15, 0.0, 0.1], 38, 4.0


# ================================================================ Blender
def blender_main(shot, test):
    import bpy
    from mathutils import Matrix, Vector

    sc = bpy.context.scene
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = RW, RH, 100
    sc.render.fps = FPS
    sc.view_settings.view_transform = "AgX"
    for look in ("AgX - Medium High Contrast", "Medium High Contrast"):
        try:
            sc.view_settings.look = look
            break
        except TypeError:
            pass
    sc.eevee.taa_render_samples = 40
    sc.eevee.use_raytracing = True
    try:
        sc.eevee.ray_tracing_options.resolution_scale = "2"
        sc.eevee.fast_gi_method = "GLOBAL_ILLUMINATION"
    except Exception:
        pass
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.45
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = "PNG"

    def srgb(h):
        h = h.lstrip("#")
        c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0]

    def principled(name, col, rough=0.45, metal=0.0, coat=0.0, trans=0.0, sss=0.0, alpha_ctl=False, emit=None):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = srgb(col) if isinstance(col, str) else col
        b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = metal
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Transmission Weight"].default_value = trans
        if sss:
            b.inputs["Subsurface Weight"].default_value = sss
            b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
            b.inputs["Subsurface Scale"].default_value = 0.004
        if emit:
            b.inputs["Emission Color"].default_value = srgb(emit[0])
            b.inputs["Emission Strength"].default_value = emit[1]
        if trans:
            m.surface_render_method = "BLENDED"
            try:
                m.use_raytrace_refraction = True
            except AttributeError:
                pass
        return m

    # ---------------- model
    bpy.ops.import_scene.gltf(filepath=GLB)
    alat = bpy.data.objects.new("ALAT", None)
    sc.collection.objects.link(alat)
    alat.scale = (0.001,) * 3
    alat.location = (-M["XC"] * 0.001 + 0.019, -0.024, 0.0)       # badan alat di tengah dunia
    fix = Matrix.Rotation(math.radians(-90), 4, "X")
    O = {}
    for o in [o for o in bpy.data.objects if o.type == "MESH"]:
        o.data.transform(fix @ o.matrix_world)
        o.parent = None
        o.matrix_world = Matrix.Identity(4)
        o.parent = alat
        O[o.name] = o
    for o in [o for o in bpy.data.objects if o.type == "EMPTY" and o is not alat]:
        bpy.data.objects.remove(o)
    for o in O.values():
        bpy.context.view_layer.objects.active = o
        o.data.shade_smooth() if o.name.startswith(("wadah_kaplet", "wadah_kubah")) else None

    # material sinematik (palet AQUENT)
    wallm = principled("M_wall", "#EEF2F8", 0.34, coat=0.25)
    wallm.surface_render_method = "BLENDED"
    wallm.use_transparency_overlap = False
    wb = wallm.node_tree.nodes["Principled BSDF"]
    MAT = {
        "dinding": wallm,
        "rangka": principled("M_frame", "#C9D3E2", 0.55),
        "gear": principled("M_gear", "#2F7BFF", 0.32, coat=0.4),
        "gerak": principled("M_car", "#1A2238", 0.4),
        "pelatuk": principled("M_plunger", "#FF8A1F", 0.35, coat=0.3),
        "tuas": principled("M_lever", "#5FA2FF", 0.35),
        "wadah": principled("M_holder", "#1646D6", 0.3, coat=0.5),
        "foil": principled("M_foil", "#D9DDE3", 0.22, metal=1.0),
        "kubah": principled("M_dome", "#F4F8FF", 0.08, coat=1.0),
        "obat": principled("M_caplet", "#C2412A", 0.32, coat=0.6),
        "servo": principled("M_servo", "#16181D", 0.45),
        "pcb": principled("M_pcb", "#0E3B2E", 0.4),
        "lensa": principled("M_glass", "#05070B", 0.08, coat=1.0),
        "jari": principled("M_tunnel", "#E6EBF3", 0.4),
        "bat": principled("M_batt", "#2E3442", 0.5),
    }
    for n, o in O.items():
        if n == "layar":
            continue
        if n.startswith("dinding") or n == "rangka_depan_extra":
            m = MAT["dinding"]
        elif n == "kereta_pelatuk":
            m = MAT["pelatuk"]
        elif n == "kereta_engkol":
            m = MAT["gear"]
        elif n == "tuas":
            m = MAT["tuas"]
        elif n.startswith("gear"):
            m = MAT["gear"]
        elif n.startswith("kereta_servo") or n.startswith("elek_servo") or n in ("elek_buzzer", "elek_kamera"):
            m = MAT["servo"]
        elif n.startswith("kereta"):
            m = MAT["gerak"]
        elif n == "wadah_foil":
            m = MAT["foil"]
        elif n == "wadah_kubah":
            m = MAT["kubah"]
        elif n.startswith("wadah_kaplet"):
            m = MAT["obat"]
        elif n.startswith("wadah"):
            m = MAT["wadah"]
        elif n == "kantong_jari":
            m = MAT["jari"]
        elif n in ("elek_cyd_lcd", "elek_kamera_lensa", "elek_max30102_sensor"):
            m = MAT["lensa"]
        elif n == "elek_baterai":
            m = MAT["bat"]
        elif n.startswith("elek"):
            m = MAT["pcb"]
        else:
            m = MAT["rangka"]
        o.data.materials.clear()
        o.data.materials.append(m)

    # layar: rantai gambar UI dengan bobot ber-keyframe
    names = ["home", "boot", "alarm", "face", "ppg", "dispense", "done"]
    scr = bpy.data.materials.new("M_screen")
    scr.use_nodes = True
    nt = scr.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(em.outputs[0], out.inputs[0])
    acc = None
    SW = {}
    for n in names:
        img = nt.nodes.new("ShaderNodeTexImage")
        img.image = bpy.data.images.load(os.path.join(LAYAR, f"{n}@3x.png"))
        mul = nt.nodes.new("ShaderNodeMix")
        mul.data_type = "RGBA"
        mul.blend_type = "MULTIPLY"
        mul.inputs["Factor"].default_value = 1.0
        nt.links.new(img.outputs["Color"], mul.inputs[6])
        mul.inputs[7].default_value = (0, 0, 0, 1)
        SW[n] = mul.inputs[7]
        if acc is None:
            acc = mul.outputs[2]
        else:
            add = nt.nodes.new("ShaderNodeMix")
            add.data_type = "RGBA"
            add.blend_type = "ADD"
            add.inputs["Factor"].default_value = 1.0
            nt.links.new(acc, add.inputs[6])
            nt.links.new(mul.outputs[2], add.inputs[7])
            acc = add.outputs[2]
    nt.links.new(acc, em.inputs["Color"])
    O["layar"].data.materials.clear()
    O["layar"].data.materials.append(scr)

    # jari (kapsul meruncing + kuku) untuk shot PPG, ujung di y=0 sepanjang -y
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=8.0, depth=170, location=(0, -85, 0), rotation=(math.pi / 2, 0, 0))
    f1 = bpy.context.object
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=8.0, location=(0, 0, 0))
    f2 = bpy.context.object
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=6.0, location=(0, -6.5, 5.4), scale=(1.0, 1.55, 0.35))
    nail = bpy.context.object
    for p in (f1, f2):
        p.data.materials.append(principled("M_skin", "#C98E6E", 0.5, sss=0.35))
    nail.data.materials.append(principled("M_nail", "#E8BBA8", 0.18, coat=0.6))
    bpy.ops.object.select_all(action="DESELECT")
    for p in (f1, f2, nail):
        p.select_set(True)
    bpy.context.view_layer.objects.active = f1
    bpy.ops.object.join()
    finger = bpy.context.object
    finger.name = "jari"
    finger.data.shade_smooth()
    finger.parent = alat
    finger.scale = (1.0, 1.0, 0.86)
    ppg_light = bpy.data.lights.new("ppg_led", "POINT")
    ppg_light.color = (1.0, 0.08, 0.05)
    ppg_light.shadow_soft_size = 0.002
    pl = bpy.data.objects.new("ppg_led", ppg_light)
    sc.collection.objects.link(pl)
    pl.parent = alat
    pl.location = (M["FING"][0], -14.0, M["FING"][1] - 7.0)

    # ---------------- titik acuan (meter dunia, pose dasar dari GLB)
    bpy.context.view_layer.update()

    def ctr(n, dz_mm=0.0):
        o = O[n]
        cs = [o.matrix_world @ Vector(c) for c in o.bound_box]
        v = sum(cs, Vector()) / 8
        return [v.x, v.y, v.z + dz_mm * 0.001]

    P = {
        "face": lerp(ctr("layar"), ctr("elek_kamera_lensa"), 0.35),
        "tunnel": (alat.matrix_world @ Vector((M["FING"][0], -45.0, M["FING"][1]))).to_tuple(),
        "mech": ctr("wadah_foil", DROW + 8),
        "cap": ctr(f"wadah_kaplet_{PECK_COL}{PECK_ROW}", DROW),
        "tray": ctr("rangka_corong"),
    }
    cap_name = f"wadah_kaplet_{PECK_COL}{PECK_ROW}"
    cap0 = O[cap_name]
    capc = sum((Vector(c) for c in cap0.bound_box), Vector()) / 8       # pusat kaplet (mm, lokal alat)
    capz = capc.z + DROW                                                # tinggi kaplet saat dipatuk
    # origin tiap komponen di pusatnya (urutan transparansi benar); B = posisi dasar
    B = {}
    for n, o in O.items():
        c = sum((Vector(v) for v in o.bound_box), Vector()) / 8
        o.data.transform(Matrix.Translation(-c))
        B[n] = Matrix.Translation(c)
        o.matrix_basis = B[n]
    tray_floor = min((O["rangka_corong"].matrix_world @ Vector(c)).z for c in O["rangka_corong"].bound_box) * 1000 + 6
    fall_mm = capz - tray_floor
    print("ACUAN", {k: [round(x, 3) for x in v] for k, v in P.items()}, "jatuh", round(fall_mm, 1))

    # ---------------- set
    world = bpy.data.worlds.new("W")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]

    def area(name, loc, rot, size, energy, col, sy=None):
        d = bpy.data.lights.new(name, "AREA")
        d.energy, d.color = energy, col
        d.shape = "RECTANGLE"
        d.size, d.size_y = size, sy or size
        o = bpy.data.objects.new(name, d)
        sc.collection.objects.link(o)
        o.location = loc
        o.rotation_euler = [math.radians(a) for a in rot]
        return d

    def aim(o, target):
        d = Vector(target) - o.location
        o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

    L = {}
    set_ = SHOTS[shot][2]
    if set_ == "kitchen":
        bg.inputs[0].default_value = (0.010, 0.014, 0.024, 1)
        bg.inputs[1].default_value = 1.0
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0.12, 0))
        tab = bpy.context.object
        tab.scale = (2.2, 1.5, 1)
        wood = principled("M_wood", "#6B4A33", 0.42, coat=0.35)
        wn = wood.node_tree
        wave = wn.nodes.new("ShaderNodeTexWave")
        wave.inputs["Scale"].default_value = 3.0
        wave.inputs["Distortion"].default_value = 9.0
        wave.inputs["Detail"].default_value = 6.0
        mapn = wn.nodes.new("ShaderNodeMapping")
        mapn.inputs["Scale"].default_value = (0.6, 9.0, 1.0)
        tc = wn.nodes.new("ShaderNodeTexCoord")
        wn.links.new(tc.outputs["Object"], mapn.inputs[0])
        wn.links.new(mapn.outputs[0], wave.inputs[0])
        ramp = wn.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = srgb("#3E2717")
        ramp.color_ramp.elements[1].color = srgb("#8A6043")
        wn.links.new(wave.outputs["Fac"], ramp.inputs[0])
        wn.links.new(ramp.outputs[0], wn.nodes["Principled BSDF"].inputs["Base Color"])
        tab.data.materials.append(wood)
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0.62, 0.6), rotation=(math.pi / 2, 0, 0))
        wall = bpy.context.object
        wall.scale = (3, 1.4, 1)
        wall.data.materials.append(principled("M_plaster", "#D9D2C6", 0.85))
        # mug keramik (untuk minum obat) + gagang
        mug = principled("M_mug", "#E9E4DA", 0.3, coat=0.5)
        bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.04, depth=0.095, location=(0.24, 0.16, 0.0475),
                                            end_fill_type="NOTHING")
        g = bpy.context.object
        sol = g.modifiers.new("s", "SOLIDIFY")
        sol.thickness = 0.004
        g.data.materials.append(mug)
        g.data.shade_smooth()
        bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.04, depth=0.006, location=(0.24, 0.16, 0.003))
        bpy.context.object.data.materials.append(mug)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.024, minor_radius=0.0055, location=(0.282, 0.16, 0.05),
                                         rotation=(math.pi / 2, 0, 0))
        bpy.context.object.data.materials.append(mug)
        bpy.context.object.data.shade_smooth()
        bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.036, depth=0.002, location=(0.24, 0.16, 0.07))
        bpy.context.object.data.materials.append(principled("M_tea", "#3B1F0E", 0.05, coat=1.0))
        # ponsel PMO tergeletak, kartu pengobatan
        bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.24, -0.16, 0.0045), rotation=(0, 0, math.radians(18)))
        ph = bpy.context.object
        ph.scale = (0.072, 0.15, 0.009)
        ph.data.materials.append(principled("M_phone", "#0D1220", 0.25, coat=1.0))
        bevel = ph.modifiers.new("b", "BEVEL")
        bevel.width, bevel.segments = 0.004, 4
        bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.17, 0.12, 0.0006), rotation=(0, 0, math.radians(-9)))
        card = bpy.context.object
        card.scale = (0.105, 0.148, 0.0012)
        card.data.materials.append(principled("M_card", "#F3E7C9", 0.8))
        # matahari pagi lewat kerai
        sun = bpy.data.lights.new("sun", "SUN")
        sun.color = (1.0, 0.68, 0.42)
        sun.angle = math.radians(1.2)
        so = bpy.data.objects.new("sun", sun)
        sc.collection.objects.link(so)
        d = Vector((0.82, 0.42, -0.36)).normalized()
        so.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        L["sun"] = (sun, 6.0)
        c0 = Vector((0.0, 0.1, 0.1)) - d * 1.4
        for i in range(-12, 13):
            bpy.ops.mesh.primitive_cube_add(size=1, location=c0 + Vector((0, 0, i * 0.045)))
            sl = bpy.context.object
            sl.scale = (0.02, 2.0, 0.024)
            sl.rotation_euler = (0, 0, math.atan2(d.y, d.x))
            sl.visible_camera = False
            sl.visible_glossy = False
        L["fill"] = (area("fill", (0.6, -0.9, 0.5), (0, 0, 0), 1.2, 6.0, (0.62, 0.74, 1.0)), 1.0)
        aim(bpy.data.objects["fill"], (0, 0, 0.1))
        L["screen"] = 1.2
    else:
        bg.inputs[0].default_value = (0.0035, 0.0065, 0.018, 1)
        bg.inputs[1].default_value = 1.0
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0.3, 0))
        fl = bpy.context.object
        fl.scale = (6, 6, 1)
        floor = principled("M_floor", "#0A1430", 0.28, coat=0.6)
        fl.data.materials.append(floor)
        # dinding cyclorama melengkung
        bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=1.6, depth=4, location=(0, 1.9, 1.6), rotation=(0, math.pi / 2, 0))
        cyc = bpy.context.object
        cyc.data.materials.append(principled("M_cyc", "#0B1A3E", 0.6))
        k = area("key", (-0.5, -0.65, 0.62), (0, 0, 0), 0.6, 26.0, (1.0, 0.97, 0.93), sy=0.42)
        aim(bpy.data.objects["key"], (0, 0, 0.1))
        r1 = area("rimL", (-0.55, 0.45, 0.32), (0, 0, 0), 0.25, 28.0, (0.25, 0.5, 1.0), sy=0.9)
        aim(bpy.data.objects["rimL"], (0, 0, 0.12))
        r2 = area("rimR", (0.6, 0.38, 0.26), (0, 0, 0), 0.25, 22.0, (0.35, 0.62, 1.0), sy=0.9)
        aim(bpy.data.objects["rimR"], (0, 0, 0.12))
        top = area("top", (0.05, 0.05, 0.85), (0, 0, 0), 0.9, 7.0, (0.85, 0.9, 1.0))
        aim(bpy.data.objects["top"], (0, 0, 0.0))
        glow = area("floorglow", (0, 0.55, 0.002), (0, 0, 0), 2.0, 0.0, (0.18, 0.48, 1.0), sy=0.05)
        L.update(key=(k, 26.0), rimL=(r1, 28.0), rimR=(r2, 22.0), top=(top, 7.0))
        L["screen"] = 1.6

    # kamera
    camd = bpy.data.cameras.new("cam")
    camd.sensor_width = 36
    cam = bpy.data.objects.new("cam", camd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    camd.dof.use_dof = True
    camd.clip_start = 0.005

    # ---------------- animasi: keyframe tiap frame (agar motion blur benar)
    N = nframes(shot)
    walls = [o for n, o in O.items() if n.startswith("dinding") or n == "rangka_depan_extra"]
    wadah = [o for n, o in O.items() if n.startswith("wadah_")]
    kereta = [o for n, o in O.items() if n.startswith("kereta_")]
    dome = MAT["kubah"]
    dome.surface_render_method = "DITHERED"
    dome.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.28
    if shot == "peck":                                               # cutaway x-ray: kaplet terlihat menembus foil
        gh = principled("M_xray", "#5FA2FF", 0.3, emit=("#2F7BFF", 0.15))
        gh.surface_render_method = "BLENDED"
        gh.use_transparency_overlap = False
        gh.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.16
        for n in ("wadah_belakang", "wadah_depan", "rangka_landasan", "rangka_corong", "kereta_badan"):
            O[n].data.materials.clear()
            O[n].data.materials.append(gh)
        fo = principled("M_foilx", "#D9DDE3", 0.25, metal=1.0)
        fo.surface_render_method = "BLENDED"
        fo.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.35
        O["wadah_foil"].data.materials.clear()
        O["wadah_foil"].data.materials.append(fo)
    for n, o in O.items():
        if n.startswith("wadah_kaplet_") and int(n[-1]) < PECK_ROW:
            o.hide_render = o.hide_viewport = True               # baris yang sudah diminum

    def about(axis, pivot, ang, extra=(0, 0, 0)):
        return (Matrix.Translation(Vector(pivot) + Vector(extra)) @ Matrix.Rotation(ang, 4, axis)
                @ Matrix.Translation(-Vector(pivot)))

    def apply(s):
        K = {n: Matrix.Identity(4) for n in O}
        for o in wadah:
            K[o.name] = Matrix.Translation((0, 0, s["wadahZ"]))
        th2 = (EJ - s["wadahZ"]) / M["R2"]
        K["gear_G2"] = about("Y", (M["G2"][0], 0, M["G2"][1]), th2)
        K["gear_G1"] = about("Y", (M["G1"][0], 0, M["G1"][1]), -th2 * M["G1_RATIO"])
        for o in kereta:
            K[o.name] = Matrix.Translation((s["carX"], 0, 0))
        K["tuas"] = about("Y", (M["S2"][0], 0, M["S2"][1]), math.asin(s["carX"] / M["LEVER_L"]))
        t = math.radians(s["theta"])
        K["kereta_engkol"] = about("Z", (M["XC"], M["Y_S3"], 0), t, (s["carX"], 0, 0))
        K["kereta_pelatuk"] = Matrix.Translation((s["carX"], M["CRANK3"] * (1 - math.cos(t)), 0))
        d = s["cap"]
        cap0.hide_render = d >= 1.0 and shot not in ("peck", "notify", "end")
        if d > 0:
            # dorong menembus foil (+y), lalu jatuh ke baki dengan gravitasi, berguling, memantul kecil
            y = min(d, 0.3) / 0.3 * 16.0
            drop = spin = 0.0
            if d > 0.3:
                g = ((d - 0.3) / 0.7) ** 2 * 1.15                 # >1 = sudah mendarat
                drop = fall_mm * min(1.0, g)
                if g > 1.0:
                    drop -= 3.0 * math.sin(math.pi * clamp((g - 1.0) / 0.15))
                spin = min(g, 1.0) * 2.4
                y += 6.0 * min(g, 1.0)
            K[cap_name] = (Matrix.Translation((0, y, DROW - drop)) @ Matrix.Translation(capc)
                           @ Matrix.Rotation(spin, 4, "X") @ Matrix.Translation(-capc))
        for n, o in O.items():
            o.matrix_basis = K[n] @ B[n]
        wb.inputs["Alpha"].default_value = s["wall"]
        for o in walls:
            o.hide_render = s["wall"] < 0.02
        for n in s.get("hide", []):
            O[n].hide_render = True
        for n in names:
            v = s["screens"].get(n, 0.0) * s["screen_e"] * L["screen"]
            SW[n].default_value = (v, v, v, 1)
        if shot == "ppg" and s["finger"] is not None:
            finger.location = (M["FING"][0], s["finger"], M["FING"][1] - 0.8)
            finger.hide_render = False
        else:
            finger.hide_render = True
        ppg_light.energy = 0.25 * s["glow"]
        if "sun" in L:
            L["sun"][0].energy = L["sun"][1] * s["sun"]
        for k_ in ("key", "top"):
            if k_ in L:
                L[k_][0].energy = L[k_][1] * s["key"]
        for k_ in ("rimL", "rimR"):
            if k_ in L:
                L[k_][0].energy = L[k_][1] * s["rim"]
        alat.rotation_euler.z = math.radians(s["turn"])

    def key_all(f):
        for o in list(O.values()) + [finger, alat, cam]:
            o.keyframe_insert("location", frame=f)
            o.keyframe_insert("rotation_euler", frame=f)
            o.keyframe_insert("scale", frame=f)
            o.keyframe_insert("hide_render", frame=f)
        wb.inputs["Alpha"].keyframe_insert("default_value", frame=f)
        for n in names:
            SW[n].keyframe_insert("default_value", frame=f)
        for d_, _ in [v for k_, v in L.items() if k_ != "screen"]:
            d_.keyframe_insert("energy", frame=f)
        ppg_light.keyframe_insert("energy", frame=f)
        camd.keyframe_insert("lens", frame=f)
        camd.dof.keyframe_insert("focus_distance", frame=f)
        camd.dof.keyframe_insert("aperture_fstop", frame=f)

    for o in O.values():
        o.rotation_mode = "XYZ"
    for f in range(N + 1):
        t = f / FPS
        s = state(shot, t)
        apply(s)
        pos, tgt, lens, fstop = camera(shot, t, P)
        cam.location = pos
        dv = Vector(tgt) - Vector(pos)
        cam.rotation_euler = dv.to_track_quat("-Z", "Y").to_euler()
        camd.lens = lens
        camd.dof.focus_distance = dv.length
        camd.dof.aperture_fstop = fstop
        key_all(f + 1)
    for a in [o.animation_data.action for o in bpy.data.objects if o.animation_data and o.animation_data.action]:
        try:
            for fc in a.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"
        except AttributeError:
            pass

    outdir = os.path.join(HERE, "_frames", shot)
    os.makedirs(outdir, exist_ok=True)
    if test:
        for f in test:
            sc.frame_set(f)
            sc.render.filepath = os.path.join(outdir, f"test_{f:04d}.png")
            bpy.ops.render.render(write_still=True)
    else:
        sc.frame_start, sc.frame_end = 1, N
        sc.render.use_overwrite = False                          # lanjutkan render yang terputus
        sc.render.filepath = os.path.join(outdir, "f_")
        bpy.ops.render.render(animation=True)
    print("SELESAI", shot)


def done(shot):
    d = os.path.join(HERE, "_frames", shot)
    return os.path.isdir(d) and len([f for f in os.listdir(d) if f.startswith("f_")]) >= nframes(shot)


def run(shot, test):
    if not test:
        for attempt in range(3):                             # driver GPU kadang crash: ulangi, frame lama dilewati
            if done(shot):
                print("SELESAI", shot)
                return
            run_once(shot, None)
        print("GAGAL", shot)
        return
    run_once(shot, test)


def run_once(shot, test):
    args = [BLENDER, "-b", "--factory-startup", "-P", os.path.abspath(__file__), "--", shot]
    if test:
        args += ["--test", ",".join(map(str, test))]
    r = subprocess.run(args, capture_output=True, text=True)
    lines = [l for l in r.stdout.splitlines() if l.startswith(("ACUAN", "SELESAI")) or "Error" in l or "Traceback" in l]
    print("\n".join(lines))
    if r.returncode or not any(l.startswith("SELESAI") for l in lines):
        print(r.stdout[-3000:], r.stderr[-3000:])


if __name__ == "__main__":
    if "--" in sys.argv:                                     # dijalankan di dalam Blender
        a = sys.argv[sys.argv.index("--") + 1:]
        tst = [int(x) for x in a[a.index("--test") + 1].split(",")] if "--test" in a else None
        blender_main(a[0], tst)
    else:
        sh = sys.argv[1]
        tst = [int(x) for x in sys.argv[sys.argv.index("--test") + 1].split(",")] if "--test" in sys.argv else None
        for s_ in (SHOTS if sh == "all" else [sh]):
            run(s_, tst)
