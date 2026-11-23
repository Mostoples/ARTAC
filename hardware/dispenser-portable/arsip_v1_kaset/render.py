"""Render pratinjau rakitan (PNG) + rakitan.glb untuk dilihat di 3D Viewer."""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import build as b

COL = {"rangka": "#f2f4f7", "gear": "#3b82f6", "kaset": "#93c5fd", "tutup": "#bfdbfe", "pelatuk": "#f59e0b",
       "servo": "#334155", "pcb": "#eab308", "lcd": "#0f172a", "bat": "#64748b", "obat": "#dc2626",
       "akrilik": "#dbe4ee"}


def assembly(day=3, dz=0.0, theta=0.0, acrylic=("belakang",)):
    xl = b.cas_left_at(day)
    items = [("rangka", b.part_rel()), ("rangka", b.part_corong()), ("rangka", b.part_dek()),
             ("rangka", b.part_klem_servo()), ("rangka", b.part_tabung()), ("rangka", b.part_braket_b()),
             ("rangka", b.part_dudukan_layar())]
    items += [("rangka", b.part_blok(n)) for n in b.CORNERS]
    items += [("gear", b.part_g1()), ("gear", b.part_g2()), ("gear", b.part_g3())]
    items += [("pelatuk", b.part_pelatuk(dz)), ("pelatuk", b.part_engkol(theta))]
    items += [("kaset", b.cas_place(b.kaset_badan_local() + b.kaset_alas_local(), xl)),
              ("tutup", b.cas_place(b.kaset_tutup_local(), xl))]
    items += [("obat", c) for c in b.caplets(xl)]
    items += b.dummies(dz)
    for n, m in b.walls_placed().items():
        if n == "dinding_depan" and "depan" not in acrylic:
            continue
        if n != "dinding_depan" and "belakang" not in acrylic:
            continue
        items.append(("akrilik", m))
    return items


def draw(ax, items, view, light=(0.4, -0.8, 0.6), alpha_acr=0.18):
    L = np.array(light) / np.linalg.norm(light)
    for kind, m in items:
        t = b.to_tm(m)
        tri = t.vertices[t.faces]
        n = t.face_normals
        shade = 0.45 + 0.55 * np.clip(n @ L, 0, 1)
        base = np.array(matplotlib.colors.to_rgb(COL[kind]))
        fc = np.clip(base[None, :] * shade[:, None], 0, 1)
        a = alpha_acr if kind == "akrilik" else 1.0
        pc = Poly3DCollection(tri, facecolors=np.c_[fc, np.full(len(fc), a)], edgecolors="none", linewidths=0)
        ax.add_collection3d(pc)
    ax.set_xlim(-5, b.W + 5); ax.set_ylim(-60, 90); ax.set_zlim(-5, b.H + 5)
    ax.set_box_aspect((b.W + 10, 150, b.H + 10))
    ax.view_init(*view)
    ax.set_axis_off()


def render(name, items, view, title, size=(11, 9), zoom=None):
    fig = plt.figure(figsize=size, dpi=110)
    ax = fig.add_subplot(111, projection="3d", proj_type="ortho")
    draw(ax, items, view)
    if zoom:
        ax.set_xlim(*zoom[0]); ax.set_ylim(*zoom[1]); ax.set_zlim(*zoom[2])
        ax.set_box_aspect(tuple(z[1] - z[0] for z in zoom))
    fig.suptitle(title, fontsize=13)
    fig.tight_layout()
    fig.savefig(os.path.join(b.OUT, "render", name), bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    # GLB rakitan berwarna (buka dengan 3D Viewer / Blender)
    scene = trimesh.Scene()
    for i, (kind, m) in enumerate(assembly(day=3, acrylic=("belakang", "depan"))):
        t = b.to_tm(m)
        rgba = (np.array(matplotlib.colors.to_rgba(COL[kind], 1.0)) * 255).astype(np.uint8)
        t.visual.face_colors = np.tile(rgba, (len(t.faces), 1))
        scene.add_geometry(t, node_name=f"{kind}_{i}")
    scene.export(os.path.join(b.OUT, "rakitan.glb"))
    print("glb selesai")
