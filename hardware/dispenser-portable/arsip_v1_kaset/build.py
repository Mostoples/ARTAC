"""ARTA-C Portable - dispenser obat TB (rangka cetak 3D + dinding akrilik).

Semua ukuran dalam mm. Koordinat perangkat (ruang dalam kotak akrilik):
  x = kiri -> kanan (lebar), y = depan -> belakang (tebal), z = bawah -> atas.
  Titik (0,0,0) = pojok dalam kiri-depan-bawah. Akrilik depan menempel di y=0.

Jalankan:  python build.py      -> stl/, dxf/, render/, rakitan.glb
Ubah parameter di bagian PARAMETER lalu jalankan ulang; semua part & lubang akrilik ikut menyesuaikan.
"""
import math
import os

import numpy as np
import trimesh
from manifold3d import CrossSection, Manifold

OUT = os.path.dirname(os.path.abspath(__file__))
SEG = 48

# ============================================================== PARAMETER
# --- kaplet 4FDC (UKUR ULANG dengan jangka sorong!)
CAP_L, CAP_W, CAP_T = 21.0, 10.0, 7.5     # panjang, lebar, tebal kaplet
N_DOSE = 5                                # kapasitas kaplet per hari (dosis 2-5)

# --- akrilik & kotak
ACR = 3.0                                 # tebal dinding cetak
W, D, H = 197.0, 30.0, 166.0              # ruang dalam kotak

# --- kaset 7 hari (wadah obat PMO)
CELL_X = CAP_W + 1.2
CELL_Y = CAP_L + 1.6
CELL_Z = N_DOSE * CAP_T + 1.5
WALL_IN, WALL_END, WALL_SIDE = 1.2, 4.5, 2.0
N_CELL = 8                                # 7 hari + 1 sel parkir (kosong)
PITCH = CELL_X + WALL_IN
LC = 2 * WALL_END + N_CELL * CELL_X + (N_CELL - 1) * WALL_IN
DC = CELL_Y + 2 * WALL_SIDE
PLATE_T, MEM_T, LID_T = 1.5, 1.0, 2.0     # alas, membran karet, tutup
CAS_Y0 = 1.8                              # posisi depan kaset
Y_C = CAS_Y0 + DC / 2                     # sumbu tengah sel (y)
ZB = 58.0                                 # dasar kaset (= atas rel)
ZT = ZB + PLATE_T + MEM_T + CELL_Z        # atas badan kaset
X_S = 98.0                                # posisi stasiun pelatuk (x)

def cell_cx(i):                            # pusat sel ke-i (1..8), koordinat lokal kaset
    return WALL_END + CELL_X / 2 + (i - 1) * PITCH

# --- roda gigi (modul 1)
MOD = 1.0
G1_T, G2S_T, G2B_T, G3S_T, G3B_T = 22, 12, 24, 13, 22
R3 = G3B_T * MOD / 2
Y_RACK = Y_C + R3                          # garis pitch rack (y)
X_G2 = X_S - (G2B_T + G3S_T) * MOD / 2
X_A = X_G2 - (G1_T + G2S_T) * MOD / 2      # poros servo A
L0 = (ZT + 4.3, ZT + 9.3)                  # G3 besar + rack
L1 = (ZT + 9.6, ZT + 14.6)                 # G3 kecil + G2 besar
L2 = (ZT + 14.9, ZT + 19.9)                # G2 kecil + G1
ARM = (ZT + 15.0, ZT + 17.7)               # lengan penahan tabung
DECK = (ZT + 26.0, ZT + 29.0)              # dek servo A

# --- servo A = TowerPro MG946R (rebah terbalik, poros ke bawah)
SA_L, SA_W, SA_H = 40.7, 19.7, 37.0
SA_FL_Z, SA_FL_T, SA_SPLINE = 26.9, 2.5, 5.9
SA_SHAFT_OFF, SA_EAR, SA_HOLE_DX, SA_HOLE_DY = 10.2, 54.0, 49.5, 10.0
SA_CB = DECK[1] + (SA_FL_Z + SA_FL_T)       # z dasar casing (di atas)
SA_CT = SA_CB - SA_H                        # z atas casing (bawah)
SA_TIP = SA_CT - SA_SPLINE
SA_X0, SA_X1 = X_A - (SA_L - SA_SHAFT_OFF), X_A + SA_SHAFT_OFF
SA_XC = (SA_X0 + SA_X1) / 2

# --- servo B = MG90S (poros sumbu y menghadap depan) -> pelatuk scotch-yoke
SB_L, SB_W, SB_H = 22.8, 12.2, 22.7
SB_FL_Z, SB_FL_T, SB_SPLINE = 15.9, 2.5, 4.0
SB_SHAFT_OFF, SB_EAR, SB_HOLE_DX = 5.9, 32.2, 27.8
CRANK_R = 22.0                              # langkah pelatuk = 2 x 22 = 44 mm
SB_YB = 29.4                                # dasar casing (belakang)
SB_YT = SB_YB - SB_H
SB_FL = (SB_YB - SB_FL_Z - SB_FL_T, SB_YB - SB_FL_Z)
X_B = X_S + 15.0
ROD = 4.4                                   # batang pelatuk persegi
ROD_TIP_UP = ZT + 3.0                       # ujung batang saat ditarik
STROKE = 2 * CRANK_R
ZR = ARM[1] + 0.5 + STROKE                  # atas batang saat ditarik
Z_B = ZR - 5.0 - CRANK_R                    # poros servo B

# --- layar CYD ESP32-2432S028 (landscape, USB ke kanan)
PCB_L, PCB_W = 86.0, 50.0
PCB_X0, PCB_Z0 = W - 1.0 - PCB_L, 2.0
LCD_T, PCB_T = 4.0, 1.6
PCB_Y0 = 0.4 + LCD_T                        # muka depan PCB
ACT_W, ACT_H = 57.6, 43.2                   # area aktif LCD 2.8"
ACT_FROM_USB = 47.6                         # pusat LCD dari tepi USB (UKUR ULANG)

# --- baterai LiPo 1S 103450 (10 x 34 x 50) + modul IP5306
BAT = (51.0, 37.0)

PILOT, CLEAR = 2.6, 3.4                     # lubang ulir M3 di plastik / tembus M3


# ============================================================== HELPER
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
    cs = CrossSection([pts])
    return cs.extrude(y1 - y0).rotate([90, 0, 0]).translate([0, y1, 0])


def union(parts):
    return Manifold.batch_boolean(parts, manifold3d_op("add"))


def manifold3d_op(name):
    from manifold3d import OpType
    return {"add": OpType.Add, "sub": OpType.Subtract}[name]


def holes_y(pts, depth, front=True, back=True, r=PILOT / 2):
    """Lubang sekrup M3 dari akrilik depan/belakang (sepanjang y) di titik (x,z)."""
    out = []
    for x, z in pts:
        if front:
            out.append(cyl_y(x, z, -1, depth, r, 24))
        if back:
            out.append(cyl_y(x, z, D - depth, D + 1, r, 24))
    return out


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


# ============================================================== PART: RANGKA
BEAMS = [(0.0, 8.0), (46.0, 54.0), (136.0, 144.0), (W - 8.0, W)]
RAIL_Z = (52.5, ZB)


def part_rel():
    """Rel kaset: rel depan + rel belakang + 4 balok lintang (sekrup ke akrilik)."""
    ps = [box(0, W, 0.3, 3.7, *RAIL_Z), box(0, W, 26.5, D - 0.3, *RAIL_Z),
          box(0, W, 0.3, CAS_Y0 - 0.4, ZB, ZB + 6), box(0, W, CAS_Y0 + DC + 0.4, D - 0.3, ZB, ZB + 6)]
    for x0, x1 in BEAMS:
        ps.append(box(x0, x1, 0.3, D - 0.3, *RAIL_Z))
    m = union(ps)
    zc = sum(RAIL_Z) / 2
    cut = holes_y([((a + b) / 2, zc) for a, b in BEAMS], 10)
    cut += [cyl_x(D / 2, zc, -1, 8, PILOT / 2, 24), cyl_x(D / 2, zc, W - 8, W + 1, PILOT / 2, 24)]
    return m - union(cut)


def ramp_z(x):                               # permukaan luncur corong
    return 11.0 + (x - 46.0) * (33.0 / 60.6)


CHUTE_KOLOM = [(70.0, 15.0), (24.0, 3.25)]


def part_corong():
    """Corong + papan luncur + baki ambil obat (profil x-z diekstrusi sepanjang y)."""
    y0, y1 = 0.3, D - 0.3
    ps = [prism_xz([(46, 8.5), (106.6, ramp_z(106.6) - 2.5), (106.6, ramp_z(106.6)), (46, 11.0)], y0, y1),
          box(10.5, 48.0, y0, y1, 6.0, 8.5),                     # lantai baki
          box(44.0, 48.0, y0, y1, 6.0, 10.4),                    # sambungan papan luncur-baki
          box(105.0, 106.6, y0, y1, ramp_z(105.0) - 1, 52.3),     # dinding corong kanan
          prism_xz([(66, 12), (74, 12), (74, ramp_z(74) - 2.0), (66, ramp_z(66) - 2.0)], y0, y1),
          box(20.0, 28.0, y0, y1, 0.5, 6.2)]
    m = union(ps)
    return m - union(holes_y(CHUTE_KOLOM, 10))


CORNERS = {  # nama: (x0, x1, z0, z1, y0)  -- BR setengah tebal (di belakang layar)
    "BL": (0, 10, 0, 10, 0.3), "TL": (0, 10, H - 10, H, 0.3),
    "TR": (W - 10, W, H - 10, H, 0.3), "BR": (W - 10, W, 0, 10, 16.0)}


def part_blok(name):
    x0, x1, z0, z1, y0 = CORNERS[name]
    m = box(x0, x1, y0, D - 0.3, z0, z1)
    xc, zc = (x0 + x1) / 2, (z0 + z1) / 2
    full = y0 < 1
    ys_side, ys_tb = (12.0, 18.0) if full else (19.5, 22.5)
    cut = holes_y([(xc, zc)], 10 if full else 6, front=full)
    cut.append(cyl_x(ys_side, zc, (x1 - 8) if x0 else -1, (W + 1) if x0 else 8, PILOT / 2, 24))   # dari sisi
    cut.append(cyl_z(xc, ys_tb, (z1 - 8) if z0 else -1, (H + 1) if z0 else 8, PILOT / 2, 24))     # atas/bawah
    return m - union(cut)


DECK_X = (X_S - 78.0, X_S - 6.0)
DECK_KOLOM = [(DECK_X[0] + 4, DECK[0] - 1.0), (X_S - 9.5, DECK[0] - 1.0)]
SA_EAR_HOLES = [(SA_XC - SA_HOLE_DX / 2, Y_C - SA_HOLE_DY / 2), (SA_XC - SA_HOLE_DX / 2, Y_C + SA_HOLE_DY / 2)]
SA_CLAMP_HOLES = [(SA_XC + SA_HOLE_DX / 2, 3.3), (SA_XC + SA_HOLE_DX / 2, D - 3.3)]


def part_dek():
    """Dek servo A + kolom + lengan penahan tabung poros G3 + dudukan poros G2."""
    zk0 = DECK[0] - 5.0
    ps = [box(*DECK_X, 0.3, D - 0.3, *DECK),
          box(DECK_X[0], DECK_X[0] + 8, 0.3, D - 0.3, zk0, DECK[1]),
          box(X_S - 13.0, X_S - 6.0, 0.3, D - 0.3, zk0, DECK[1]),
          box(X_S - 10.0, X_S - 6.0, 17.0, 28.0, ARM[0], zk0 + 0.1),            # web
          box(X_S - 10.0, X_S + 5.0, 10.0, 28.0, *ARM),                          # lengan
          cyl_z(X_G2, Y_C, L2[1] + 0.4 + 5.0, DECK[0] + 0.1, 4.0)]                # boss G2 (di atas hub)
    for x, y in SA_CLAMP_HOLES:
        ps.append(cyl_z(x, y, zk0, DECK[0] + 0.1, 3.0))
    m = union(ps)
    hole_x0 = SA_X0 - 0.4
    cut = [box(hole_x0, SA_X1 + 0.4, Y_C - SA_W / 2 - 0.4, Y_C + SA_W / 2 + 0.4, DECK[0] - 1, DECK[1] + 1),
           cyl_z(X_S, Y_C, ARM[0] - 1, ARM[1] + 1, 7.6 / 2),
           cyl_z(X_G2, Y_C, L2[1], DECK[1] + 1, CLEAR / 2)]
    for x, y in SA_EAR_HOLES:
        cut.append(cyl_z(x, y, zk0 - 1, DECK[1] + 1, PILOT / 2, 24))
    for x, y in SA_CLAMP_HOLES:
        cut.append(cyl_z(x, y, zk0 - 1, DECK[1] + 1, PILOT / 2, 24))
    cut += holes_y(DECK_KOLOM, 10)
    return m - union(cut)


def part_klem_servo():
    x = SA_XC + SA_HOLE_DX / 2
    z0 = DECK[1] + SA_FL_T
    m = box(x - 3.5, x + 3.5, 0.6, D - 0.6, z0, z0 + 3.0)
    m = m + box(x - 3.5, x + 3.5, 0.6, 6.0, DECK[1], z0) + box(x - 3.5, x + 3.5, D - 6.0, D - 0.6, DECK[1], z0)
    return m - union([cyl_z(x, y, DECK[1] - 1, z0 + 4, CLEAR / 2, 24) for _, y in SA_CLAMP_HOLES])


def part_tabung():
    """Tabung poros G3 (lubang persegi untuk batang pelatuk, anti-putar)."""
    z0, z1 = ZT + 2.5, ARM[1]
    m = cyl_z(X_S, Y_C, z0, z1, 7.5 / 2) + cyl_z(X_S, Y_C, z0, z0 + 1.5, 5.5)
    return m - box(X_S - 2.5, X_S + 2.5, Y_C - 2.5, Y_C + 2.5, z0 - 1, z1 + 1)


def part_g1():
    g = gear(G1_T, X_A, Y_C, L2[0], L2[1], phase=180.0 / G1_T) + cyl_z(X_A, Y_C, L2[1], SA_CT - 0.2, 6.0)
    return g - cyl_z(X_A, Y_C, L2[0] + 0.6, SA_CT, 5.6 / 2) - cyl_z(X_A, Y_C, L2[0] - 1, L2[0] + 1, 3.3 / 2)


def part_g2():
    g = gear(G2B_T, X_G2, Y_C, *L1) + gear(G2S_T, X_G2, Y_C, L1[1] - 0.01, L2[1])
    g = g + cyl_z(X_G2, Y_C, L2[1] - 0.01, L2[1] + 0.4, 4.0)
    return g - cyl_z(X_G2, Y_C, L1[0] - 1, L2[1] + 1, CLEAR / 2)


def part_g3():
    g = gear(G3B_T, X_S, Y_C, *L0) + cyl_z(X_S, Y_C, L0[1] - 0.01, L1[0] + 0.01, 5.5)
    g = g + gear(G3S_T, X_S, Y_C, *L1)
    return g - cyl_z(X_S, Y_C, L0[0] - 1, L1[1] + 1, 7.9 / 2)


def part_pelatuk(dz=0.0):
    """Batang pelatuk + jembatan + yoke (slot horizontal untuk pin engkol)."""
    zr = ZR + dz
    rod = box(X_S - ROD / 2, X_S + ROD / 2, Y_C - ROD / 2, Y_C + ROD / 2, ROD_TIP_UP + dz, zr + 0.1)
    rod = rod - box(X_S - 3, X_S + 3, Y_C - 3, Y_C + 3, ROD_TIP_UP + dz - 1, ROD_TIP_UP + dz + 0.6)  # ujung
    rod = rod + box(X_S - ROD / 2 + 0.6, X_S + ROD / 2 - 0.6, Y_C - ROD / 2 + 0.6, Y_C + ROD / 2 - 0.6,
                    ROD_TIP_UP + dz, ROD_TIP_UP + dz + 0.7)
    bridge = box(X_S - 3, X_S + 3, 0.4, Y_C + ROD / 2 + 0.3, zr, zr + 3)
    yoke = box(X_S - 3, X_B + CRANK_R + 5, 0.4, 2.4, zr - 10, zr + 3)
    slot = box(X_B - 2.5, X_B + CRANK_R + 2.5, -1, 4, zr - 5 - 1.9, zr - 5 + 1.9)
    return union([rod, bridge, yoke]) - slot


def crank_angle_for(dz):                    # dz = -(perpindahan pelatuk)
    return math.degrees(math.acos(max(-1, min(1, 1 + 2 * dz / STROKE))))


def part_engkol(theta_deg=0.0):
    """Engkol servo B, r = 22 mm. theta 0 = pelatuk naik, 180 = turun penuh."""
    y0, y1 = SB_YT - SB_SPLINE + 0.3, SB_YT - SB_SPLINE + 3.3
    hub = cyl_y(X_B, Z_B, y0, y1, 5.0)
    t = math.radians(theta_deg)
    px, pz = X_B + CRANK_R * math.sin(t), Z_B + CRANK_R * math.cos(t)
    arm = (cyl_y(px, pz, y0, y1, 3.5) + hub).hull()
    pin = cyl_y(px, pz, 0.9, y0 + 0.01, 1.5, 24)
    m = arm + pin
    return m - cyl_y(X_B, Z_B, y0 - 1, y1 + 1, 4.7 / 2) + cyl_y(X_B, Z_B, y0, y0 + 0.8, 3.0) \
        - cyl_y(X_B, Z_B, y0 - 1, y1 + 1, 2.2 / 2, 24)


SB_BOSS = [(X_B + 21.25, Z_B - 9.0), (X_B + 21.25, Z_B + 9.0), (X_B - 8.25, Z_B)]


def part_braket_b():
    bx0, bx1, bz0, bz1 = X_B - SB_SHAFT_OFF - 0.4, X_B + SB_L - SB_SHAFT_OFF + 0.4, Z_B - SB_W / 2 - 0.4, Z_B + SB_W / 2 + 0.4
    ps = [box(X_B - 10.0, X_B + 25.0, SB_FL[1], SB_FL[1] + 3.0, Z_B - 13.0, Z_B + 13.0)]
    for x, z in SB_BOSS:
        ps.append(box(x - 3.5, x + 3.5, SB_FL[1], D - 0.3, z - 3.5 if x > X_B else z - 13, z + 3.5 if x > X_B else z + 13))
    m = union(ps)
    xc = X_B - SB_SHAFT_OFF + SB_L / 2
    cut = [box(bx0, bx1, 0, D + 1, bz0, bz1)]
    cut += [cyl_y(xc + s * SB_HOLE_DX / 2, Z_B, SB_FL[1] - 1, SB_FL[1] + 8, 1.8 / 2, 24) for s in (-1, 1)]
    cut += holes_y(SB_BOSS, 10, front=False)
    return m - union(cut)


CR_BOSS = [(PCB_X0 + 4.0, 5.5), (PCB_X0 + 4.0, 47.5), (PCB_X0 + 81.5, 47.5)]


def part_dudukan_layar():
    """Dudukan layar CYD (menekan PCB ke akrilik depan) + rak baterai LiPo + rak modul daya."""
    x0, x1, z0, z1 = PCB_X0, PCB_X0 + PCB_L, PCB_Z0, PCB_Z0 + PCB_W
    yb = PCB_Y0 + PCB_T + 0.2
    ps = [box(x0, x1, 14.0, 16.0, z0 - 1.0, z1)]
    for px in (x0, x1 - 6):
        for pz in (z0, z1 - 6):
            ps.append(box(px, px + 6, yb, 14.1, pz, pz + 6))
    ps.append(box(x0 + 8, x0 + 40, 0.4, 16.0, 0.3, 2.0))                 # bibir bawah
    ps.append(box(x1 - 40, x1 - 8, 0.4, 16.0, 0.3, 2.0))
    bx0, bz0 = PCB_X0 + 10.0, 6.0                                                   # rak baterai
    ps.append(box(bx0, bx0 + BAT[0] + 3, 15.9, D - 0.3, bz0, bz0 + BAT[1] + 3))
    ps.append(box(PCB_X0 + 66.0, PCB_X0 + 85.0, 15.9, D - 0.3, 12.0, 42.0))                 # rak modul daya
    for x, z in CR_BOSS:
        ps.append(box(x - 3.5, x + 3.5, 15.9, D - 0.3, z - 3.5, z + 3.5))
    m = union(ps)
    cut = [box(bx0 + 1.5, bx0 + 1.5 + BAT[0], 17.5, D + 1, bz0 + 1.5, bz0 + 1.5 + BAT[1]),
           box(PCB_X0 + 67.5, PCB_X0 + 83.5, 17.5, D + 1, 13.5, 40.5),
           box(bx0 + 20, bx0 + 34, 17.5, D + 1, bz0 - 1, bz0 + 2),         # alur kabel
           box(PCB_X0 + 63.0, PCB_X0 + 69.0, 22.0, D + 1, 20.0, 26.0)]
    cut += holes_y(CR_BOSS, 10, front=False)
    return m - union(cut)


# ============================================================== PART: KASET
def cas_local_cells(z0, z1, open_park=True):
    return [box(cell_cx(i) - CELL_X / 2, cell_cx(i) + CELL_X / 2, WALL_SIDE, WALL_SIDE + CELL_Y, z0, z1)
            for i in range(1, N_CELL + 1)]


CAS_SCREW = [(WALL_END / 2, 6.0), (WALL_END / 2, DC - 6.0), (LC - WALL_END / 2, 6.0), (LC - WALL_END / 2, DC - 6.0)]


def kaset_badan_local():
    z0, z1 = PLATE_T + MEM_T, PLATE_T + MEM_T + CELL_Z
    m = box(0, LC, 0, DC, z0, z1) - union(cas_local_cells(z0 - 1, z1 + 1))
    yp = Y_RACK - CAS_Y0
    m = m + box(0, LC, WALL_SIDE + CELL_Y - 1.6, yp + 1.25 + 1.85, z1, z1 + LID_T + 0.2)   # penutup belakang
    m = m + box(0, LC, yp + 1.25, yp + 1.25 + 1.85, z1, (L0[1] - ZB))                    # punggung rack
    m = m + rack(0, LC, yp, yp + 1.25 + 1.85, z1 + LID_T + 0.8, L0[1] - ZB)
    m = m + box(LC - 0.5, LC + 6, DC / 2 - 4, DC / 2 + 4, 10, 30)                                # pegangan
    cut = [cyl_z(x, y, z0 - 1, z0 + 8, 1.8 / 2, 24) for x, y in CAS_SCREW]
    cut += [cyl_z(x, DC / 2, z1 - 4, z1 + 3, 1.3, 24) for x in (WALL_END / 2, LC - WALL_END / 2)]
    return m - union(cut)


def kaset_alas_local():
    m = box(0, LC, 0, DC, 0, PLATE_T) - union(cas_local_cells(-1, PLATE_T + 1))
    return m - union([cyl_z(x, y, -1, PLATE_T + 1, 2.2 / 2, 24) for x, y in CAS_SCREW])


def kaset_tutup_local():
    z0 = PLATE_T + MEM_T + CELL_Z
    y1 = WALL_SIDE + CELL_Y - 1.6 - 0.3
    m = box(0, LC, 0, y1, z0, z0 + LID_T)
    m = m + union([cyl_z(x, DC / 2, z0 - 2.5, z0 + 0.1, 1.1, 24) for x in (WALL_END / 2, LC - WALL_END / 2)])
    cut = []
    for i in range(1, 8):
        cut.append(cyl_z(cell_cx(i), Y_C - CAS_Y0, z0 - 1, z0 + LID_T + 1, 3.5))
        cut.append(Manifold.cylinder(1.2, 3.5, 5.0, SEG).translate([cell_cx(i), Y_C - CAS_Y0, z0 + LID_T - 1.19]))
    return m - union(cut)


def cas_place(m, x_left):
    return m.translate([x_left, CAS_Y0, ZB])


def cas_left_at(cell):                     # posisi kiri kaset saat sel ke-n di bawah pelatuk
    return X_S - cell_cx(cell)


# ============================================================== DUMMY (render saja)
def dummies(dz_rod):
    d = []
    # servo A
    d.append(("servo", box(SA_X0, SA_X1, Y_C - SA_W / 2, Y_C + SA_W / 2, SA_CT, SA_CB)
              + box(SA_XC - SA_EAR / 2, SA_XC + SA_EAR / 2, Y_C - SA_W / 2, Y_C + SA_W / 2, DECK[1], DECK[1] + SA_FL_T)
              + cyl_z(X_A, Y_C, SA_TIP, SA_CT, 2.75)))
    # servo B
    d.append(("servo", box(X_B - SB_SHAFT_OFF, X_B + SB_L - SB_SHAFT_OFF, SB_YT, SB_YB, Z_B - SB_W / 2, Z_B + SB_W / 2)
              + box(X_B - SB_SHAFT_OFF + SB_L / 2 - SB_EAR / 2, X_B - SB_SHAFT_OFF + SB_L / 2 + SB_EAR / 2,
                    SB_FL[0], SB_FL[1], Z_B - SB_W / 2, Z_B + SB_W / 2)))
    # layar
    d.append(("pcb", box(PCB_X0, PCB_X0 + PCB_L, PCB_Y0, PCB_Y0 + PCB_T, PCB_Z0, PCB_Z0 + PCB_W)))
    d.append(("lcd", box(PCB_X0 + 8, PCB_X0 + 77, 0.4, PCB_Y0, PCB_Z0, PCB_Z0 + PCB_W)))
    d.append(("bat", box(PCB_X0 + 11.5, PCB_X0 + 61.5, 18, 28, 7.5, 7.5 + 34)))
    # kaplet di sel hari 1..7
    return d


def caplets(x_left):
    out = []
    for i in range(1, 8):
        for k in range(3):
            z = ZB + PLATE_T + MEM_T + 0.2 + k * CAP_T
            out.append(box(x_left + cell_cx(i) - CAP_W / 2, x_left + cell_cx(i) + CAP_W / 2,
                           Y_C - CAP_L / 2, Y_C + CAP_L / 2, z, z + CAP_T - 0.4))
    return out


# ============================================================== DINDING CETAK 3D
def wall_specs():
    ox, oz = ACR, ACR
    front_holes = [(5, 5), (5, H - 5), (W - 5, H - 5)]
    front_holes += [((a + b) / 2, sum(RAIL_Z) / 2) for a, b in BEAMS]
    front_holes += CHUTE_KOLOM + DECK_KOLOM
    back_holes = front_holes + [(W - 5, 5)] + CR_BOSS + SB_BOSS
    act_cx = PCB_X0 + PCB_L - ACT_FROM_USB
    act_cz = PCB_Z0 + PCB_W / 2
    front_cut = [("rect", act_cx - 30 + ox, act_cz - 23 + oz, 60, 46),           # jendela layar sentuh
                 ("rect", 12 + ox, 13 + oz, 34, 21)]                             # bukaan baki obat
    tb_holes = lambda zc: [(5, 18.0), (W - 5, 18.0)]
    side = lambda: [(12.0, 5), (12.0, H - 5), (D / 2, sum(RAIL_Z) / 2)]
    cas_open = (ZB - 0.6, L0[1] + 1.2)
    specs = {
        "dinding_depan": dict(size=(W + 2 * ACR, H + 2 * ACR), holes=[(x + ox, z + oz) for x, z in front_holes],
                              cuts=front_cut),
        "dinding_belakang": dict(size=(W + 2 * ACR, H + 2 * ACR), holes=[(x + ox, z + oz) for x, z in back_holes],
                                 cuts=[]),
        "dinding_atas": dict(size=(W + 2 * ACR, D), holes=[(x + ox, y) for x, y in tb_holes(0)], cuts=[]),
        "dinding_bawah": dict(size=(W + 2 * ACR, D), holes=[(x + ox, y) for x, y in tb_holes(0)], cuts=[]),
        "dinding_kiri": dict(size=(D, H), holes=side(), cuts=[("circle", D / 2, 140.0, 3.1)]),
        "dinding_kanan_bawah": dict(size=(D, cas_open[0]), holes=[(19.5, 5), (D / 2, sum(RAIL_Z) / 2)],
                                    cuts=[("rect", 3.5, 10.0, 9.0, 34.0), ("rect", 18.0, 20.0, 9.0, 10.0)]),
        "dinding_kanan_atas": dict(size=(D, H - cas_open[1]), holes=[(12.0, H - 5 - cas_open[1])], cuts=[]),
    }
    return specs, cas_open


def wall_local(spec):
    """Panel dinding di koordinat lokal (u,v) tebal w=0..ACR; w=0 = muka luar (dicetak menghadap bed)."""
    w, h = spec["size"]
    cs = CrossSection.square([w, h])
    cuts = [CrossSection.circle(CLEAR / 2, 32).translate([x, y]) for x, y in spec["holes"]]
    for c in spec["cuts"]:
        if c[0] == "rect":
            cuts.append(CrossSection.square([c[3], c[4]]).translate([c[1], c[2]]))
        else:
            cuts.append(CrossSection.circle(c[3], 48).translate([c[1], c[2]]))
    if cuts:
        cs = cs - CrossSection.batch_boolean(cuts, manifold3d_op("add"))
    m = cs.extrude(ACR)
    cones = [Manifold.cylinder(1.8, 3.3, 1.5, 32).translate([x, y, -0.01]) for x, y in spec["holes"]]
    return m - union(cones) if cones else m


def walls_placed():
    """Semua panel dinding di posisi rakitan."""
    specs, cas_open = wall_specs()
    A = ACR
    M = {"dinding_depan": [[1, 0, 0, -A], [0, 0, 1, -A], [0, 1, 0, -A]],
         "dinding_belakang": [[1, 0, 0, -A], [0, 0, -1, D + A], [0, 1, 0, -A]],
         "dinding_atas": [[1, 0, 0, -A], [0, 1, 0, 0], [0, 0, -1, H + A]],
         "dinding_bawah": [[1, 0, 0, -A], [0, 1, 0, 0], [0, 0, 1, -A]],
         "dinding_kiri": [[0, 0, 1, -A], [1, 0, 0, 0], [0, 1, 0, 0]],
         "dinding_kanan_bawah": [[0, 0, -1, W + A], [1, 0, 0, 0], [0, 1, 0, 0]],
         "dinding_kanan_atas": [[0, 0, -1, W + A], [1, 0, 0, 0], [0, 1, 0, cas_open[1]]]}
    return {n: wall_local(sp).transform(M[n]) for n, sp in specs.items()}


def membran_spec():
    holes = [(x, y) for x, y in CAS_SCREW]
    slits = []
    for i in range(1, 8):
        cx, cy = cell_cx(i), DC / 2
        slits.append(((cx, cy - CELL_Y / 2 + 1.5), (cx, cy + CELL_Y / 2 - 1.5)))
        for s in (-1, 1):
            yy = cy + s * (CELL_Y / 2 - 1.5)
            slits.append(((cx - CELL_X / 2 + 1.5, yy), (cx + CELL_X / 2 - 1.5, yy)))
    return (LC, DC), holes, slits


def write_dxf():
    """Templat potong membran karet kaset (cetak 1:1 di kertas, atau laser)."""
    import ezdxf
    os.makedirs(os.path.join(OUT, "dxf"), exist_ok=True)
    (w, h), holes, slits = membran_spec()
    doc = ezdxf.new("R2010"); doc.units = ezdxf.units.MM
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (w, 0), (w, h), (0, h)], close=True)
    for x, y in holes:
        msp.add_circle((x, y), 1.1)
    for a, b in slits:
        msp.add_line(a, b)
    doc.saveas(os.path.join(OUT, "dxf", "membran_karet_kaset.dxf"))


# ============================================================== EKSPOR
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


def build():
    os.makedirs(os.path.join(OUT, "stl"), exist_ok=True)
    parts = {}
    parts["01_rel_kaset"] = (part_rel(), None)
    parts["02_corong_baki"] = (part_corong(), RX(90))
    for n in CORNERS:
        parts[f"03_blok_sudut_{n}"] = (part_blok(n), None)
    parts["04_dek_servoA"] = (part_dek(), RX(180))
    parts["05_klem_servoA"] = (part_klem_servo(), None)
    parts["06_tabung_poros_G3"] = (part_tabung(), None)
    parts["07_gear_G1_servoA_22T"] = (part_g1(), None)
    parts["08_gear_G2_24T-12T"] = (part_g2(), None)
    parts["09_gear_G3_22T-13T"] = (part_g3(), None)
    parts["10_pelatuk"] = (part_pelatuk(), RX(180))
    parts["11_engkol_servoB"] = (part_engkol(), RX(-90))
    parts["12_braket_servoB"] = (part_braket_b(), RX(-90))
    parts["13_dudukan_layar_baterai"] = (part_dudukan_layar(), RX(90))
    parts["14_kaset_badan"] = (kaset_badan_local(), None)
    parts["15_kaset_alas"] = (kaset_alas_local(), None)
    parts["16_kaset_tutup"] = (kaset_tutup_local(), RX(180))
    for k, (n, sp) in enumerate(wall_specs()[0].items()):
        parts[f"{17 + k}_{n}"] = (wall_local(sp), None)
    report = []
    for name, (m, rot) in parts.items():
        t = save_stl(name, m, rot)
        ext = t.bounds[1] - t.bounds[0]
        raw = m.to_mesh()
        wt = trimesh.Trimesh(np.asarray(raw.vert_properties)[:, :3], np.asarray(raw.tri_verts), process=False).is_watertight
        report.append((name, ext, t.volume / 1000 * 1.24, wt and len(m.decompose()) == 1))
    return parts, report


# ============================================================== CEK TABRAKAN
def clearance_checks():
    xl = cas_left_at(1)
    ok = []
    statics = {"rel": part_rel(), "corong": part_corong(), "dek": part_dek(), "tabung": part_tabung(),
               "G3": part_g3(), "G2": part_g2(), "G1": part_g1(), "braket_B": part_braket_b(),
               "layar": part_dudukan_layar(), **{f"blok_{n}": part_blok(n) for n in CORNERS}}
    for pos_name, cell in (("hari1", 1), ("hari7", 7), ("parkir", 8)):
        x = cas_left_at(cell)
        cas = cas_place(kaset_badan_local() + kaset_alas_local() + kaset_tutup_local(), x)
        for n, s in statics.items():
            if n == "G3":
                continue
            v = (cas ^ s).volume()
            if v > 0.01:
                ok.append(f"TABRAKAN kaset@{pos_name} x {n}: {v:.2f} mm3")
    for dz, th in ((0.0, 0.0), (-STROKE / 2, 90.0), (-STROKE, 180.0)):
        pel = part_pelatuk(dz)
        eng = part_engkol(th)
        for n, s in statics.items():
            for nm, mm in (("pelatuk", pel), ("engkol", eng)):
                if n == "tabung" and nm == "pelatuk":
                    continue
                v = (mm ^ s).volume()
                if v > 0.01:
                    ok.append(f"TABRAKAN {nm}@{th:.0f}deg x {n}: {v:.2f} mm3")
    servos = [m for k, m in dummies(0) if k == "servo"]
    for n, s in statics.items():
        for j, sv in enumerate(servos):
            v = (sv ^ s).volume()
            if v > 0.01:
                ok.append(f"TABRAKAN servo{'AB'[j]} x {n}: {v:.2f} mm3")
    for th in (0.0, 45.0, 90.0, 135.0, 180.0):
        dz = -STROKE * (1 - math.cos(math.radians(th))) / 2
        for j, sv in enumerate(servos):
            for nm, mm in (("pelatuk", part_pelatuk(dz)), ("engkol", part_engkol(th))):
                v = (sv ^ mm).volume()
                if v > 0.01:
                    ok.append(f"TABRAKAN servo{'AB'[j]} x {nm}@{th:.0f}: {v:.2f} mm3")
    for cell in (1, 4, 7):
        cas = cas_place(kaset_badan_local() + kaset_alas_local() + kaset_tutup_local(), cas_left_at(cell))
        v = (cas ^ part_pelatuk(-STROKE)).volume()
        if v > 0.01:
            ok.append(f"TABRAKAN pelatuk turun x kaset sel {cell}: {v:.2f} mm3")
    for i, a in enumerate(list(statics)):
        for b in list(statics)[i + 1:]:
            v = (statics[a] ^ statics[b]).volume()
            if v > 0.01:
                ok.append(f"TABRAKAN {a} x {b}: {v:.2f} mm3")
    return ok


if __name__ == "__main__":
    parts, report = build()
    write_dxf()
    print(f"Kotak luar: {W + 2 * ACR:.0f} x {H + 2 * ACR:.0f} x {D + 2 * ACR:.0f} mm (L x T x tebal)")
    print(f"Kaset: {LC:.1f} x {DC:.1f} x {ZT + LID_T - ZB:.1f} mm, pitch {PITCH} mm, sel {CELL_X}x{CELL_Y}x{CELL_Z}")
    print(f"Servo A poros x={X_A:.1f}; G2 x={X_G2:.1f}; Servo B poros (x,z)=({X_B:.1f},{Z_B:.1f}); ZR={ZR:.1f}")
    mm_per_rad = (G1_T / G2S_T) * (G2B_T / G3S_T) * R3
    print(f"Rasio rack: {mm_per_rad:.2f} mm/rad = {mm_per_rad * math.pi / 180:.3f} mm/deg")
    tot = 0
    for n, ext, g, wt in report:
        tot += g
        print(f"  {n:28s} {ext[0]:6.1f} x {ext[1]:6.1f} x {ext[2]:6.1f}  ~{g:5.1f} g (solid)  utuh={wt}")
    print(f"  total ~{tot:.0f} g bila padat 100% (dinding 3 mm tercetak ~65% padat, rangka ~45%)")
    for c in clearance_checks() or ["Cek tabrakan: aman"]:
        print(c)
