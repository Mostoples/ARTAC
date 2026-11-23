"""Ekspor model ARTA-C (dari CAD parametrik) ke GLB untuk halaman showcase three.js.

  python buat_model.py   ->  artac.glb   (satuan mm, z ke atas; node bernama per part)
"""
import os
import sys

import numpy as np
import trimesh
from PIL import Image
from trimesh.visual.material import PBRMaterial

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
HW = os.path.join(ROOT, "hardware", "dispenser-portable")
sys.path.insert(0, HW)
import build as b  # noqa: E402

P = {   # warna (sRGB 0-1), metallic, roughness, alpha
    "dinding": ((0.93, 0.95, 0.98), 0.0, 0.45, 1.0), "rangka": ((0.97, 0.98, 0.99), 0.0, 0.5, 1.0),
    "gear": ((0.18, 0.48, 1.0), 0.0, 0.35, 1.0), "gerak": ((0.98, 0.6, 0.15), 0.0, 0.4, 1.0),
    "wadah": ((0.55, 0.74, 1.0), 0.0, 0.35, 1.0), "foil": ((0.85, 0.86, 0.9), 0.9, 0.25, 1.0),
    "kubah": ((0.9, 0.95, 1.0), 0.0, 0.05, 0.35), "obat": ((0.86, 0.1, 0.12), 0.0, 0.25, 1.0),
    "servo": ((0.1, 0.12, 0.16), 0.0, 0.5, 1.0), "pcb": ((0.1, 0.45, 0.25), 0.2, 0.5, 1.0),
    "pcb_y": ((0.88, 0.66, 0.12), 0.2, 0.5, 1.0), "jari": ((0.06, 0.07, 0.08), 0.0, 0.6, 1.0),
    "bat": ((0.3, 0.36, 0.45), 0.3, 0.4, 1.0), "dht": ((0.2, 0.6, 0.95), 0.0, 0.4, 1.0),
    "lensa": ((0.02, 0.03, 0.05), 0.5, 0.05, 1.0),
}


def mat(key):
    c, m, r, a = P[key]
    return PBRMaterial(name=key, baseColorFactor=[*c, a], metallicFactor=m, roughnessFactor=r,
                       alphaMode="BLEND" if a < 1 else "OPAQUE", doubleSided=a < 1)


def add(scene, name, manifold, key):
    t = b.to_tm(manifold)
    t.visual = trimesh.visual.TextureVisuals(material=mat(key))
    scene.add_geometry(t, node_name=name, geom_name=name)


def screen_quad(scene, png):
    x0 = b.PCB[0] + b.PCB[2] - b.ACT_FROM_USB - b.ACT_W / 2
    z0 = b.PCB[1] + b.PCB[3] / 2 - b.ACT_H / 2
    y = 0.25
    v = np.array([[x0, y, z0], [x0 + b.ACT_W, y, z0], [x0 + b.ACT_W, y, z0 + b.ACT_H], [x0, y, z0 + b.ACT_H]])
    f = np.array([[0, 2, 1], [0, 3, 2]])
    uv = np.array([[0, 0], [1, 0], [1, 1], [0, 1]])
    img = Image.open(png).convert("RGB")
    m = PBRMaterial(name="layar", baseColorTexture=img, emissiveTexture=img, emissiveFactor=[1, 1, 1],
                    metallicFactor=0, roughnessFactor=0.2)
    t = trimesh.Trimesh(v, f, process=False)
    t.visual = trimesh.visual.TextureVisuals(uv=uv, material=m)
    scene.add_geometry(t, node_name="layar", geom_name="layar")


def main():
    sc = trimesh.Scene()
    for n, m in b.walls_placed().items():
        add(sc, n, m, "dinding")
    st = b.statics()
    for n, m in st.items():
        if n == "kantong_jari":
            add(sc, "kantong_jari", m, "jari")
        elif n in ("G1", "spacer"):
            add(sc, "gear_" + n, m, "gear")
        else:
            add(sc, "rangka_" + n, m, "rangka")
    add(sc, "gear_G2", b.part_g2(), "gear")
    cb = b.cb_at(1)
    add(sc, "wadah_belakang", b.wadah_belakang(cb), "wadah")
    add(sc, "wadah_depan", b.wadah_depan(cb), "wadah")
    base, domes, caps = b.blister_parts(cb)
    add(sc, "wadah_foil", base, "foil")
    add(sc, "wadah_kubah", b.union([m for _, m in domes]), "kubah")
    for (c, r), m in caps:
        add(sc, f"wadah_kaplet_{c}{r}", m, "obat")
    add(sc, "kereta_badan", b.kereta(b.XC), "gerak")
    add(sc, "kereta_servo3", b.servo3_dummy(b.XC), "servo")
    add(sc, "kereta_engkol", b.engkol3(b.XC), "gerak")
    add(sc, "kereta_pelatuk", b.pelatuk(b.XC), "gerak")
    add(sc, "tuas", b.part_tuas(), "gerak")
    d = b.dummies()
    kinds = ["servo", "servo", "pcb_y", "lensa", "bat", "pcb", "pcb", "servo", "lensa", "servo", "pcb", "lensa", "pcb", "dht"]
    names = ["servo1", "servo2", "cyd_pcb", "cyd_lcd", "baterai", "ip5306", "esp32cam", "kamera", "kamera_lensa",
             "buzzer", "max30102", "max30102_sensor", "dht11_pcb", "dht11"]
    for (k, m), nm, kd in zip(d, names, kinds):
        add(sc, "elek_" + nm, m, kd)
    screen_quad(sc, os.path.join(ROOT, "ui3d", "layar", "home@3x.png"))
    out = os.path.join(HERE, "artac.glb")
    sc.export(out)
    print(out, os.path.getsize(out) // 1024, "KB", len(sc.geometry), "node")


if __name__ == "__main__":
    main()


def meta():
    import json
    sys.path.insert(0, HW)
    import gambar_teknik as gt
    m = dict(W=b.W, D=b.D, H=b.H, XC=b.XC, Z_P=b.Z_P, PZ=b.PZ, PX=b.PX, CB_EJ=b.CB_EJ, CB1=b.cb_at(1),
             cols=[b.pocket_xz(c, 1, 0)[0] for c in range(1, 5)], G1=b.G1, G2=b.G2, R2=b.G2B_T / 2,
             G1_RATIO=b.G2S_T / b.G1_T, S2=b.S2, LEVER_L=b.LEVER_L, Y_S3=b.Y_S3, CRANK3=b.CRANK3,
             FING=b.FING, explode=gt.EXPLODE)
    json.dump(m, open(os.path.join(HERE, "artac.json"), "w"), indent=1)
    print("artac.json")


if __name__ == "__main__":
    meta()
