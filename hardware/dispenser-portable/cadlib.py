"""Pustaka geometri kecil (manifold3d) untuk model ARTA-C."""
import math

import numpy as np
import trimesh
from manifold3d import CrossSection, Manifold

SEG = 48
MOD = 1.0


def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def cyl_z(cx, cy, z0, z1, r, seg=SEG):
    return Manifold.cylinder(z1 - z0, r, r, seg).translate([cx, cy, z0])


def cyl_y(cx, cz, y0, y1, r, seg=SEG):
    return Manifold.cylinder(y1 - y0, r, r, seg).rotate([-90, 0, 0]).translate([cx, y0, cz])


def cyl_x(cy, cz, x0, x1, r, seg=SEG):
    return Manifold.cylinder(x1 - x0, r, r, seg).rotate([0, 90, 0]).translate([x0, cy, cz])


def prism_xz(pts, y0, y1):
    """Poligon di bidang (x,z) diekstrusi sepanjang y."""
    area = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    cs = CrossSection([pts if area > 0 else pts[::-1]])
    return cs.extrude(y1 - y0).rotate([90, 0, 0]).translate([0, y1, 0])



def union(parts):
    return Manifold.batch_boolean(parts, manifold3d_op("add"))


def manifold3d_op(name):
    from manifold3d import OpType
    return {"add": OpType.Add, "sub": OpType.Subtract}[name]



def gear_poly(z, m=MOD, bl=0.15, pa_deg=20.0):
    pa = math.radians(pa_deg)
    rp, rb = z * m / 2, z * m / 2 * math.cos(pa)
    ra, rf = rp + m, rp - 1.25 * m
    inv = lambda a: math.tan(a) - a
    psi = (math.pi * m / 2 - bl) / (2 * rp)
    th = lambda r: psi + inv(pa) - inv(math.acos(min(1.0, rb / max(r, rb))))
    rs = np.linspace(max(rb, rf), ra, 7)
    pts = []
    for k in range(z):
        c = 2 * math.pi * k / z
        if rf < rb:
            a = c - th(rs[0]); pts.append((rf * math.cos(a), rf * math.sin(a)))
        for r in rs:
            a = c - th(r); pts.append((r * math.cos(a), r * math.sin(a)))
        for r in rs[::-1]:
            a = c + th(r); pts.append((r * math.cos(a), r * math.sin(a)))
        if rf < rb:
            a = c + th(rs[0]); pts.append((rf * math.cos(a), rf * math.sin(a)))
        a1, a2 = c + th(rs[0]), c + 2 * math.pi / z - th(rs[0])
        for t in np.linspace(a1, a2, 5)[1:-1]:
            pts.append((rf * math.cos(t), rf * math.sin(t)))
    return pts


def gear(teeth, cx, cy, z0, z1, bore=0.0, phase=0.0):
    g = CrossSection([gear_poly(teeth)]).rotate(phase).extrude(z1 - z0).translate([cx, cy, z0])
    if bore:
        g = g - cyl_z(cx, cy, z0 - 1, z1 + 1, bore / 2)
    return g


def rack(x0, x1, y_pitch, y_back, z0, z1, m=MOD, bl=0.15):
    """Rack sepanjang x, gigi menghadap -y."""
    p = math.pi * m
    hp = (p / 2 - bl) / 2
    t20 = math.tan(math.radians(20))
    polys = [[(x0, y_pitch + 1.25 * m), (x1, y_pitch + 1.25 * m), (x1, y_back), (x0, y_back)]]
    x = x0 + p / 2
    while x < x1 - p / 2:
        polys.append([(x - hp - 1.25 * m * t20, y_pitch + 1.25 * m + 0.01),
                      (x - hp + m * t20, y_pitch - m),
                      (x + hp - m * t20, y_pitch - m),
                      (x + hp + 1.25 * m * t20, y_pitch + 1.25 * m + 0.01)][::-1])
        x += p
    cs = CrossSection.batch_boolean([CrossSection([pp]) for pp in polys], manifold3d_op("add"))
    return cs.extrude(z1 - z0).translate([0, 0, z0])



def to_tm(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts),
                           process=True)


def save_stl(name, m, rot=None):
    t = to_tm(m)
    if rot is not None:
        t.apply_transform(rot)
    t.apply_translation(-t.bounds[0])
    t.export(os.path.join(OUT, "stl", name + ".stl"))
    return t


RX = lambda deg: trimesh.transformations.rotation_matrix(math.radians(deg), [1, 0, 0])
RY = lambda deg: trimesh.transformations.rotation_matrix(math.radians(deg), [0, 1, 0])

