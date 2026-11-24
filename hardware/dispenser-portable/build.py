"""ARTA-C Portable v2 - konsep "pemanggang roti".

Wadah (bingkai pemegang blister utuh) dimasukkan dari celah atas. Servo 1 menurunkan wadah baris demi baris,
servo 2 menggeser kereta pelatuk kiri-kanan, servo 3 mendorong pelatuk menembus kubah blister sehingga kaplet
keluar lewat foil ke belakang, jatuh ke corong, lalu ke baki depan. Seluruh bagian dicetak 3D.

Koordinat (mm): x kiri->kanan, y depan->belakang (muka dalam dinding depan y=0), z bawah->atas.
Jalankan: python build.py  ->  stl/ + laporan ukuran + cek tabrakan.
"""
import math
import os

import numpy as np
import trimesh

from cadlib import (CrossSection, Manifold, RX, box, cyl_x, cyl_y, cyl_z, gear, manifold3d_op, prism_xz, rack,
                    to_tm, union)

OUT = os.path.dirname(os.path.abspath(__file__))

# ============================================================== PARAMETER
A = 3.0                                    # tebal dinding cetak
DZ = 20.0                                  # +20 mm tinggi untuk blister 180 mm (mekanisme atas ikut naik)
W, D, H = 162.0, 48.0, 200.0 + DZ          # ruang dalam
XC = 100.5                                 # sumbu tengah blister (x); +0.5 agar rack/servo1 tetap di x lama

# --- blister (ukuran user 2026-11): 104 x 180 mm, 4 kolom x 7 baris, kaplet MIRING 45 deg (semua sejajar)
#     celah tepi-ke-tepi antar kaplet: horizontal 7.5 mm, vertikal 7.0 mm (diukur pada garis lewat pusat)
BL_W, BL_H = 104.0, 180.0
CAP_L, CAP_W, CAP_T = 20.5, 10.5, 6.5
TILT = 45.0                                # sudut sumbu panjang kaplet terhadap horizontal
GAP_X, GAP_Z = 7.5, 7.0
NC, NR = 4, 7
PX = CAP_W / math.sin(math.radians(TILT)) + GAP_X          # 22.35 mm pusat-ke-pusat
PZ = CAP_W / math.cos(math.radians(TILT)) + GAP_Z          # 21.85 mm
POC_X, POC_Z, DOME_H = CAP_L + 1.5, CAP_W + 1.5, 7.5        # kantong (dalam bingkai kaplet, sebelum dimiringkan)
BL_MZ = (BL_H - NR * PZ) / 2

# --- lapisan y
Y_F = 28.1                                 # muka belakang blister (foil)
PLATE_T = 2.0                              # pelat belakang wadah
BASE_Y = (Y_F - 0.6, Y_F)                  # alas plastik+foil blister
FR_Y = (BASE_Y[0] - 3.0, BASE_Y[0])        # bingkai depan wadah
BP_Y = (Y_F, Y_F + PLATE_T)                # pelat belakang wadah
DOME_TIP = BASE_Y[0] - DOME_H
CAR_Y = (FR_Y[0], BP_Y[1])

# --- wadah (carrier)
CAR_X = (XC - BL_W / 2 - 6.5, XC + BL_W / 2 + 6.5)   # rel samping 6 mm + celah 0.5 mm
CAR_BOT, CAR_TOP = 7.0, 16.0
CAR_H = BL_H + CAR_BOT + CAR_TOP
Z_P = 168.0 + DZ                           # garis pelatuk (tinggi pusat baris aktif)


def cb_at(k):                              # z dasar wadah saat baris ke-k di garis pelatuk
    return Z_P - CAR_BOT - BL_MZ - (k - 0.5) * PZ


CB_EJ = 165.5 + DZ                         # posisi masuk/keluar (wadah menyembul di atas)


def pocket_xz(c, r, cb):                   # pusat kantong kolom c (1..4), baris r (1..7)
    return XC + (c - (NC + 1) / 2) * PX, cb + CAR_BOT + BL_MZ + (r - 0.5) * PZ


# --- servo 1 (MG90S): rack di sisi kiri wadah + roda gigi majemuk
X_R = CAR_X[0] - 1.25                      # garis pitch rack
RACK_Y = (CAR_Y[0] + 0.5, CAR_Y[1] - 0.5)
G1_T, G2S_T, G2B_T = 40, 12, 36
G2 = (X_R - G2B_T / 2, 176.0 + DZ)
G1 = (G2[0], G2[1] - (G1_T + G2S_T) / 2)
GF_Y = (CAR_Y[0] - 5.9, CAR_Y[0] - 0.9)   # lapisan depan (G1 + G2 kecil)
MM_PER_RAD_1 = (G1_T / G2S_T) * (G2B_T / 2)

# --- servo umum MG90S
SB_L, SB_W, SB_H, SB_FL_Z, SB_FL_T, SB_SPL, SB_OFF, SB_EAR, SB_HOLE = 22.8, 12.2, 22.7, 15.9, 2.5, 4.0, 5.9, 32.2, 27.8

S1_CT = GF_Y[1] + 0.2                      # servo 1 menghadap depan: atas casing (y)
S1_CB = S1_CT + SB_H

# --- servo 2: tuas vertikal di bawah, menggeser kereta
S2 = (XC, 14.0)                            # poros (x, z)
LEVER_Y = (13.6, 16.6)
S2_CT = LEVER_Y[1] + 0.9
LEVER_L = 113.0 + DZ

# --- servo 3 di kereta: scotch-yoke, pelatuk mendorong arah +y
CRANK3 = 6.3                               # langkah 12.6 mm
Y_S3 = 9.5
PAD_LP = 14.3                              # jarak pin engkol -> ujung bantalan
Z_S3_CT = Z_P - 8.0                        # atas casing servo 3

# --- rel kereta
RAIL_Z, RAIL_Y = (Z_P + 9.0, Z_P + 17.0), (1.5, 11.0)

# --- layar CYD (landscape)
PCB = (XC - 43.0, 62.0, 86.0, 50.0)        # x0, z0, panjang, lebar
LCD_T, PCB_T = 4.0, 1.6
ACT_W, ACT_H, ACT_FROM_USB = 57.6, 43.2, 47.6

# --- elektronik tambahan di ruang depan (x, z = pusat; koordinat perangkat)
CAM = (8.0, 35.0, 128.0, 168.5)            # ESP32-CAM 27 x 40.5 mm: x0, x1, z0, z1 (kamera menghadap depan)
CAM_LENS = ((CAM[0] + CAM[1]) / 2, CAM[3] - 11.0)
BUZ = (22.0, 112.0)                        # buzzer 12 mm
FING = (75.0, 46.0)                        # terowongan jari PPG (x, z sumbu lubang) - MAX30102 di lantainya
FING_R, FING_Y = 9.5, (-45.0, -6.0)        # jari-jari lubang, rentang y blok (menonjol keluar dari muka depan)
FING_BOLT = [(61.0, 28.5), (89.0, 28.5), (61.0, 59.0), (89.0, 59.0)]
DHT = (104.0, 46.0)                        # DHT11 (suhu & kelembapan)
USBC = (5.5, 83.0)                         # port cas USB-C modul IP5306 di dinding kiri (y, z)

PILOT, CLEAR = 2.6, 3.4


def holes_y(pts, depth, front=True, back=True, r=PILOT / 2):
    out = []
    for x, z in pts:
        if front:
            out.append(cyl_y(x, z, -1, depth, r, 24))
        if back:
            out.append(cyl_y(x, z, D - depth, D + 1, r, 24))
    return out


def rbox_xz(cx, cz, w, h, y0, y1, r=2.0, ang=0.0):
    """Kotak bersudut bulat (bidang x-z), diekstrusi sepanjang y; ang = putar di bidang x-z (deg, +x ke +z)."""
    cs = CrossSection.square([w - 2 * r, h - 2 * r], True).offset(r, circular_segments=24)
    if ang:
        cs = cs.rotate(ang)
    return cs.extrude(y1 - y0).rotate([90, 0, 0]).translate([cx, y1, cz])


def pocket(x, z, grow, y0, y1, r=4.5):
    """Kantong/lubang kaplet miring (TILT) di pusat (x, z), diperbesar grow mm."""
    return rbox_xz(x, z, POC_X + grow, POC_Z + grow, y0, y1, min(r, (POC_Z + grow) / 2 - 0.1), TILT)


# ============================================================== WADAH (pemegang blister)
def wadah_belakang(cb):
    x0, x1 = CAR_X
    ps = [box(x0, x1, *BP_Y, cb, cb + CAR_H),
          box(x0, x0 + 6, CAR_Y[0], CAR_Y[1], cb, cb + CAR_H),
          box(x1 - 6, x1, CAR_Y[0], CAR_Y[1], cb, cb + CAR_H),
          box(x0, x1, CAR_Y[0], CAR_Y[1], cb, cb + CAR_BOT),
          box(x0, x1, CAR_Y[0], CAR_Y[1], cb + CAR_H - CAR_TOP, cb + CAR_H)]
    m = union(ps)
    # rack vertikal di sisi kiri: lokal (u=z, v=x, w=y), gigi menghadap -x
    rk = rack(cb + 5, cb + CAR_H - 18, X_R, x0 + 3, *RACK_Y).transform([[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0]])
    m = m + rk
    cut = []
    for c in range(1, NC + 1):
        for r in range(1, NR + 1):
            x, z = pocket_xz(c, r, cb)
            cut.append(pocket(x, z, 1.0, BP_Y[0] - 0.01, BP_Y[1] + 1))
    cut.append(rbox_xz(XC, cb + CAR_H - 8, 40, 9, CAR_Y[0] - 1, CAR_Y[1] + 1, 4.4))          # pegangan
    for z in (cb + 25, cb + CAR_H / 2, cb + CAR_H - 30):
        for x in (x0 + 3, x1 - 3):
            cut.append(cyl_y(x, z, CAR_Y[0] - 1, BP_Y[0] - 0.5, 0.9, 16))
    return m - union(cut)


def wadah_depan(cb):
    x0, x1 = CAR_X[0] + 6.2, CAR_X[1] - 6.2
    m = box(x0 - 6.2, x1 + 6.2, *FR_Y, cb + CAR_BOT + 2.0, cb + CAR_H - CAR_TOP - 2.0)   # 176 mm: muat bed 180
    cut = []
    for c in range(1, NC + 1):
        for r in range(1, NR + 1):
            x, z = pocket_xz(c, r, cb)
            cut.append(pocket(x, z, 1.5, FR_Y[0] - 1, FR_Y[1] + 1))
    for z in (cb + 25, cb + CAR_H / 2, cb + CAR_H - 30):
        for x in (CAR_X[0] + 3, CAR_X[1] - 3):
            cut.append(cyl_y(x, z, FR_Y[0] - 1, FR_Y[1] + 1, 1.2, 16))
    return m - union(cut)


def blister_parts(cb, popped=()):
    """Blister (render saja): alas foil, kubah, kaplet."""
    T = CAP_T - 0.4
    base = box(XC - BL_W / 2, XC + BL_W / 2, *BASE_Y, cb + CAR_BOT, cb + CAR_BOT + BL_H)
    domes, caps = [], []
    for c in range(1, NC + 1):
        for r in range(1, NR + 1):
            x, z = pocket_xz(c, r, cb)
            domes.append(((c, r), pocket(x, z, 0.0, DOME_TIP, BASE_Y[0] + 0.01)))
            caps.append(((c, r), caplet().translate([x, BASE_Y[0] - T / 2 - 0.3, z])))
    return base, domes, caps


def caplet():
    T = CAP_T - 0.4
    r = CAP_W / 2
    a = cyl_y(-(CAP_L / 2 - r), 0, -T / 2, T / 2, r, 32)
    b = cyl_y(CAP_L / 2 - r, 0, -T / 2, T / 2, r, 32)
    return (a + b).hull().rotate([0, -TILT, 0])           # Ry(-a): sumbu +x naik ke +z, sama dengan pocket()


# ============================================================== RANGKA
def part_pemandu_kiri():
    x0 = CAR_X[0]
    z0, z1 = 26.0, G1[1] - 22.0
    m = union([box(X_R - 4.2, x0 + 6, CAR_Y[0] - 2.5, CAR_Y[0] - 0.3, z0, z1),
               box(X_R - 4.2, x0 + 6, CAR_Y[1] + 0.3, CAR_Y[1] + 2.0, z0, z1),
               box(X_R - 4.2, X_R - 1.3, CAR_Y[0] - 2.5, CAR_Y[1] + 2.0, z0, z1),
               box(X_R - 4.2, x0 + 6, CAR_Y[1] + 0.3, D - 0.3, z0, z0 + 8),
               box(X_R - 4.2, x0 + 6, CAR_Y[1] + 0.3, D - 0.3, z1 - 8, z1)])
    return m - union(holes_y([(x0 + 1, z0 + 4), (x0 + 1, z1 - 4)], 10, front=False))


def part_pemandu_kanan():
    x1 = CAR_X[1]
    z0, z1 = 26.0, H - 0.2
    m = union([box(x1 - 6, x1 + 0.5, CAR_Y[0] - 2.5, CAR_Y[0] - 0.3, z0, z1),
               box(x1 - 6, x1 + 0.5, CAR_Y[1] + 0.3, CAR_Y[1] + 2.0, z0, z1),
               box(x1 + 0.4, W - 0.3, CAR_Y[0] - 2.5, CAR_Y[1] + 2.0, z0, z1)])
    cut = [cyl_x((CAR_Y[0] + CAR_Y[1]) / 2, z, W - 9, W + 1, PILOT / 2, 24) for z in (40, 110, 180)]
    return m - union(cut)


def part_landasan():
    """Landasan di belakang wadah: pelat penahan dorongan dengan 4 celah miring (TILT) di baris aktif.
    Kaplet menembus foil lewat celah, lalu jatuh di ruang antara pelat dan dinding belakang."""
    x0, x1 = CAR_X[0] + 6, CAR_X[1] - 6
    y0 = CAR_Y[1] + 0.3
    hz = (POC_X + 2.5 + POC_Z + 2.5) * math.sin(math.radians(TILT)) / 2 + 2.5    # setengah tinggi celah + tepi
    plate = box(x0, x1, y0, y0 + 2.4, Z_P - hz, Z_P + hz)
    ps = [plate,
          box(x0, x1, y0, D - 0.3, Z_P + hz, Z_P + hz + 3.5),                      # balok atas (ke dinding belakang)
          box(x0, x0 + 4, y0, D - 0.3, Z_P - hz - 8, Z_P + hz + 3.5),              # tiang kiri
          box(x1 - 4, x1, y0, D - 0.3, Z_P - hz - 8, Z_P + hz + 3.5),              # tiang kanan
          box(x0, x0 + 4, D - 2.3, D - 0.3, Z_P - hz - 8, Z_P + hz + 3.5),
          box(x0, x1, D - 2.3, D - 0.3, Z_P - hz - 8, Z_P - hz - 3)]               # palang bawah belakang
    for i in range(NC - 1):                                                       # sirip penguat di antara celah (miring)
        xr = XC + (i - (NC - 2) / 2) * PX
        ps.append(rbox_xz(xr, Z_P + hz + 1.75, 2.0, 3.5, y0, D - 0.3, 0.5))
    m = union(ps)
    cut = [pocket(XC + (c - (NC + 1) / 2) * PX, Z_P, 2.5, y0 - 1, y0 + 3.5) for c in range(1, NC + 1)]
    pts = [(x0 + 2, Z_P + hz + 1.75), (x1 - 2, Z_P + hz + 1.75), (x0 + 2, Z_P - hz - 5.5), (x1 - 2, Z_P - hz - 5.5)]
    return m - union(cut + holes_y(pts, 10, front=False))


def part_rel():
    m = box(0.3, W - 0.3, *RAIL_Y, *RAIL_Z)
    cut = [cyl_x(sum(RAIL_Y) / 2, sum(RAIL_Z) / 2, -1, 8, PILOT / 2, 24),
           cyl_x(sum(RAIL_Y) / 2, sum(RAIL_Z) / 2, W - 8, W + 1, PILOT / 2, 24)]
    cut += holes_y([(4.0, sum(RAIL_Z) / 2), (W - 4.0, sum(RAIL_Z) / 2)], 8, back=False)
    return m - union(cut)


def ramp_back_z(x):                          # lantai belakang miring ke kanan
    return 80.0 - (x - 44.0) * (50.0 / 106.0)


TRAY_X = (116.0, 150.0)


def ramp_fwd_z(y):                           # papan luncur ke depan
    return 4.0 + y * (20.0 / 47.0)


def part_corong():
    yb0 = CAR_Y[1] + 7.0                     # lantai belakang (di belakang landasan)
    ps = [prism_xz([(44, ramp_back_z(44)), (150, ramp_back_z(150)), (150, ramp_back_z(150) - 3),
                    (44, ramp_back_z(44) - 3)], yb0, D - 0.3)]
    # papan luncur depan: profil y-z diekstrusi x
    prof = CrossSection([[(0.5, ramp_fwd_z(0.5) - 2.5), (D - 0.3, ramp_fwd_z(D - 0.3) - 2.5),
                          (D - 0.3, ramp_fwd_z(D - 0.3)), (0.5, ramp_fwd_z(0.5))]])
    fwd = prof.extrude(TRAY_X[1] - TRAY_X[0]).rotate([90, 0, 90]).translate([TRAY_X[0], 0, 0])
    ps.append(fwd)
    side = [(0.5, 1.0), (D - 0.3, 1.0), (D - 0.3, ramp_fwd_z(D - 0.3) + 4), (0.5, ramp_fwd_z(0.5) + 12)]
    for xw in (TRAY_X[0] - 2, TRAY_X[1]):
        ps.append(CrossSection([side]).extrude(2.0).rotate([90, 0, 90]).translate([xw, 0, 0]))
    ps.append(box(TRAY_X[0] - 2, TRAY_X[1] + 2, D - 2.3, D - 0.3, ramp_fwd_z(D) - 3, ramp_back_z(150) + 4))
    for x in (60.0, 140.0):                  # tiang lantai belakang
        ps.append(box(x - 3, x + 3, D - 6, D - 0.3, 40.0 if x < 100 else ramp_fwd_z(D) - 3, ramp_back_z(x) - 2.5))
    m = union(ps)
    pts = [(60.0, 46.0), (140.0, 38.0), (TRAY_X[0] + 6, ramp_fwd_z(D) - 1), (TRAY_X[1] - 6, ramp_fwd_z(D) - 1)]
    return m - union(holes_y(pts, 8, front=False))


def lever_angle(x_car):
    return math.asin((x_car - S2[0]) / LEVER_L)


def part_tuas(phi=0.0):
    hub = cyl_y(S2[0], S2[1], *LEVER_Y, 5.0)
    tip = cyl_y(S2[0], S2[1] + LEVER_L, *LEVER_Y, 3.5)
    m = (hub + tip).hull()
    m = m + cyl_y(S2[0], S2[1] + LEVER_L, 10.6, LEVER_Y[0] + 0.01, 1.5, 24)
    m = m - cyl_y(S2[0], S2[1], LEVER_Y[0] - 1, LEVER_Y[1] + 1, 4.7 / 2)
    if phi:
        m = m.translate([-S2[0], 0, -S2[1]]).rotate([0, math.degrees(phi), 0]).translate([S2[0], 0, S2[1]])
    return m


def mg90s_y(x_sh, z_sh, y_ct, facing, left=True):
    """Dummy MG90S, poros sejajar y. facing=-1: poros ke depan."""
    yb = y_ct - facing * SB_H
    y0, y1 = sorted((y_ct, yb))
    xb = (x_sh - (SB_L - SB_OFF), x_sh + SB_OFF) if left else (x_sh - SB_OFF, x_sh + SB_L - SB_OFF)
    body = box(*xb, y0, y1, z_sh - SB_W / 2, z_sh + SB_W / 2)
    yf = yb + facing * SB_FL_Z
    fl = box((xb[0] + xb[1]) / 2 - SB_EAR / 2, (xb[0] + xb[1]) / 2 + SB_EAR / 2, *sorted((yf, yf + facing * SB_FL_T)),
             z_sh - SB_W / 2, z_sh + SB_W / 2)
    return body + fl, xb, sorted((yf, yf + facing * SB_FL_T))


def part_braket_s2():
    _, xb, fl = mg90s_y(S2[0], S2[1], S2_CT, -1)
    y0 = fl[1]
    m = box(xb[0] - 7, xb[1] + 7, y0, y0 + 3, 3.0, 23.0)
    m = m - box(xb[0] - 0.4, xb[1] + 0.4, y0 - 1, y0 + 4, S2[1] - SB_W / 2 - 0.4, S2[1] + SB_W / 2 + 0.4)
    xc = (xb[0] + xb[1]) / 2
    m = m - union([cyl_y(xc + s * SB_HOLE / 2, S2[1], y0 - 1, y0 + 4, 0.9, 16) for s in (-1, 1)])
    for x in (xb[0] - 4, xb[1] + 4):
        m = m + box(x - 3, x + 3, y0, D - 0.3, 6.0, 20.0)
    return m - union(holes_y([(xb[0] - 4, 13.0), (xb[1] + 4, 13.0)], 8, front=False))


def part_braket_s1():
    _, xb, fl = mg90s_y(G1[0], G1[1], S1_CT, -1)
    y0 = fl[1]
    m = box(0.5, xb[1] + 7, y0, y0 + 3, G1[1] - 10, G1[1] + 7.5)
    m = m - box(xb[0] - 0.4, xb[1] + 0.4, y0 - 1, y0 + 4, G1[1] - SB_W / 2 - 0.4, G1[1] + SB_W / 2 + 0.4)
    xc = (xb[0] + xb[1]) / 2
    m = m - union([cyl_y(xc + s * SB_HOLE / 2, G1[1], y0 - 1, y0 + 4, 0.9, 16) for s in (-1, 1)])
    for x in (3.0, xb[1] + 4):
        m = m + box(x - 2.5, x + 2.5, y0, D - 0.3, G1[1] - 10, G1[1] - 3)
    return m - union(holes_y([(3.0, G1[1] - 6.5), (xb[1] + 4, G1[1] - 6.5)], 8, front=False))


def _gear_y(teeth, cx, cz, y0, y1, bore=0.0, phase=0.0):
    """Roda gigi di bidang x-z (poros sejajar y), tebal y0..y1."""
    g = gear(teeth, 0, 0, 0, y1 - y0, phase=phase).rotate([-90, 0, 0]).translate([cx, y0, cz])
    if bore:
        g = g - cyl_y(cx, cz, y0 - 1, y1 + 1, bore / 2)
    return g


def part_g1():
    g = _gear_y(G1_T, G1[0], G1[1], *GF_Y, phase=180.0 / G1_T)
    g = g + cyl_y(G1[0], G1[1], GF_Y[1] - 0.01, S1_CT - 0.2, 5.5)
    return g - cyl_y(G1[0], G1[1], GF_Y[0] + 0.8, S1_CT, 4.7 / 2) - cyl_y(G1[0], G1[1], GF_Y[0] - 1, GF_Y[0] + 1, 1.1)


def part_g2():
    big = _gear_y(G2B_T, G2[0], G2[1], *RACK_Y)
    small = _gear_y(G2S_T, G2[0], G2[1], GF_Y[0], RACK_Y[0] + 0.01)
    return union([big, small]) - cyl_y(G2[0], G2[1], GF_Y[0] - 1, D, CLEAR / 2)


def part_spacer_g2():
    y0 = RACK_Y[1] + 0.8
    return cyl_y(G2[0], G2[1], y0, D - 0.3, 3.5) - cyl_y(G2[0], G2[1], y0 - 1, D + 1, CLEAR / 2)


# ---- kereta + pelatuk
def kereta(xs):
    """Kereta pelatuk di posisi x poros servo 3 = xs."""
    zc = Z_P
    ps = [box(xs - 16.6, xs - 14.6, 0.5, 18.4, 118.0 + DZ, RAIL_Z[0] - 0.4),                    # pelat samping
          box(xs - 16.6, xs + 14.6, 0.6, 13.4, RAIL_Z[1] + 0.4, RAIL_Z[1] + 2.4),            # atap kait
          box(xs - 16.6, xs + 14.6, RAIL_Y[1] + 0.4, 13.4, RAIL_Z[0] - 2, RAIL_Z[1] + 2.4),  # punggung kait
          box(xs - 16.6, xs + 14.6, 6.0, 13.4, RAIL_Z[0] - 2, RAIL_Z[0] - 0.4),              # bibir bawah
          box(xs - 16.6, xs + 14.6, 0.5, 18.4, zc + 4.6, zc + 6.6),                          # jembatan atas
          box(xs + 11.6, xs + 14.6, 0.5, 18.4, zc - 4.5, zc + 6.6),                          # dinding alur kanan
          box(xs - 14.7, xs - 11.6, 0.5, 18.4, zc - 4.5, zc + 6.6),                          # dinding alur kiri
          box(xs - 16.6, xs + 24.0, 0.5, 18.4, Z_S3_CT - SB_H + SB_FL_Z - 2.5, Z_S3_CT - SB_H + SB_FL_Z),
          box(xs - 16.6, xs + 6.0, 10.2, 13.3, 118.0 + DZ, 124.0 + DZ),                                # rok (slot tuas)
          box(xs - 6.0, xs + 6.0, 10.2, 13.3, 112.0 + DZ, 124.0 + DZ)]
    m = union(ps)
    cut = [box(xs - 11.7, xs + 11.7, 0, 19, zc - 2.4, zc + 2.4),                            # alur palang yoke
           box(xs - 6.3, xs + 17.3, 3.0, 16.0, Z_S3_CT - SB_H, Z_S3_CT),                    # badan servo 3
           box(xs - 1.8, xs + 1.8, 9.0, 14.0, 113.0 + DZ, 126.0 + DZ)]   # garpu terbuka ke atas                                # slot pin tuas
    xcb = xs - SB_OFF + SB_L / 2
    cut += [cyl_z(xcb + s * SB_HOLE / 2, Y_S3, Z_S3_CT - SB_H + SB_FL_Z - 4, Z_S3_CT - SB_H + SB_FL_Z + 1, 0.9, 16)
            for s in (-1, 1)]
    return m - union(cut)


def pelatuk(xs, theta_deg=0.0):
    s = CRANK3 * (1 - math.cos(math.radians(theta_deg)))
    y0 = Y_S3 - CRANK3 + s                      # posisi pin engkol (arah y)
    zc = Z_P
    yoke = box(xs - 11.3, xs + 11.3, y0 - 2.7, y0 + 2.7, zc - 2.0, zc + 2.0)
    bar = box(xs - 3.0, xs + 3.0, y0, y0 + PAD_LP - 2, zc - 2.0, zc + 3.5)       # dasar rata z-2 (mudah dicetak)
    pad = rbox_xz(xs, zc, CAP_L - 4.0, 7.0, y0 + PAD_LP - 2.5, y0 + PAD_LP, 3.0, TILT)   # miring, sejajar kaplet
    m = union([yoke, bar, pad])
    return m - box(xs - CRANK3 - 1.8, xs + CRANK3 + 1.8, y0 - 1.75, y0 + 1.75, zc - 3, zc + 3)


def engkol3(xs, theta_deg=0.0):
    z0, z1 = Z_S3_CT + 1.0, Z_S3_CT + 4.0
    t = math.radians(theta_deg)
    px, py = xs + CRANK3 * math.sin(t), Y_S3 - CRANK3 * math.cos(t)
    arm = (cyl_z(xs, Y_S3, z0, z1, 4.5) + cyl_z(px, py, z0, z1, 3.0)).hull()
    pin = cyl_z(px, py, z1 - 0.01, Z_P + 1.8, 1.5, 24)
    return arm + pin - cyl_z(xs, Y_S3, z0 - 1, z1 + 1, 4.7 / 2)


def servo3_dummy(xs):
    zb = Z_S3_CT - SB_H
    body = box(xs - SB_OFF, xs + SB_L - SB_OFF, Y_S3 - SB_W / 2, Y_S3 + SB_W / 2, zb, Z_S3_CT)
    xc = xs - SB_OFF + SB_L / 2
    fl = box(xc - SB_EAR / 2, xc + SB_EAR / 2, Y_S3 - SB_W / 2, Y_S3 + SB_W / 2, zb + SB_FL_Z, zb + SB_FL_Z + SB_FL_T)
    return body + fl


# ============================================================== DINDING
CORNERS = {"BL": (0, 10, 0, 10, 0.3, D - 0.3), "BR": (W - 10, W, 0, 10, 0.3, D - 0.3),
           "TL": (0, 10, H - 10, H, 0.3, CAR_Y[0] - 6.5), "TR": (W - 10, W, H - 10, H, 0.3, CAR_Y[0] - 3.0)}


def part_blok(name):
    x0, x1, z0, z1, y0, y1 = CORNERS[name]
    m = box(x0, x1, y0, y1, z0, z1)
    xc, zc = (x0 + x1) / 2, (z0 + z1) / 2
    full = y1 > D - 1
    cut = holes_y([(xc, zc)], 8, front=True, back=full)
    ym = (y0 + y1) / 2
    cut.append(cyl_x(ym - 3, zc, (x1 - 8) if x0 else -1, (W + 1) if x0 else 8, PILOT / 2, 24))
    cut.append(cyl_z(xc, ym + 3, (z1 - 8) if z0 else -1, (H + 1) if z0 else 8, PILOT / 2, 24))
    return m - union(cut)


def corner_holes():
    fr, bk, sd, tb = [], [], {"L": [], "R": []}, {"T": [], "B": []}
    for n, (x0, x1, z0, z1, y0, y1) in CORNERS.items():
        xc, zc, ym = (x0 + x1) / 2, (z0 + z1) / 2, (y0 + y1) / 2
        fr.append((xc, zc))
        if y1 > D - 1:
            bk.append((xc, zc))
        sd["R" if x0 else "L"].append((ym - 3, zc))
        tb["T" if z0 else "B"].append((xc, ym + 3))
    return fr, bk, sd, tb


def wall_specs():
    fr, bk, sd, tb = corner_holes()
    fr += [(4.0, sum(RAIL_Z) / 2), (W - 4.0, sum(RAIL_Z) / 2)]
    bk += [(CAR_X[0] + 1, 30.0), (CAR_X[0] + 1, G1[1] - 26.0)]
    bk += [(CAR_X[0] + 8, Z_P + 10), (CAR_X[1] - 8, Z_P + 10), (CAR_X[0] + 8, Z_P - 19), (CAR_X[1] - 8, Z_P - 19)]
    bk += [(60.0, 46.0), (140.0, 38.0), (TRAY_X[0] + 6, ramp_fwd_z(D) - 1), (TRAY_X[1] - 6, ramp_fwd_z(D) - 1)]
    _, xb2, _ = mg90s_y(S2[0], S2[1], S2_CT, -1)
    bk += [(xb2[0] - 4, 13.0), (xb2[1] + 4, 13.0)]
    _, xb1, _ = mg90s_y(G1[0], G1[1], S1_CT, -1)
    bk += [(3.0, G1[1] - 6.5), (xb1[1] + 4, G1[1] - 6.5)]
    rail_side = [(sum(RAIL_Y) / 2, sum(RAIL_Z) / 2)]
    act_cx = PCB[0] + PCB[2] - ACT_FROM_USB
    act_cz = PCB[1] + PCB[3] / 2
    O = A
    specs = {
        "dinding_depan": dict(size=(W + 2 * A, H + 2 * A), holes=[(x + O, z + O) for x, z in fr],
                              cuts=[("rect", act_cx - 30 + O, act_cz - 23 + O, 60, 46),
                                    ("rect", TRAY_X[0] + 2 + O, 8 + O, TRAY_X[1] - TRAY_X[0] - 4, 22)]),
        "dinding_belakang": dict(size=(W + 2 * A, H + 2 * A), holes=[(x + O, z + O) for x, z in bk],
                                 cuts=[("circle", G2[0] + O, G2[1] + O, CLEAR / 2)]),
        "dinding_atas": dict(size=(W + 2 * A, D), holes=[(x + O, y) for x, y in tb["T"]],
                             cuts=[("rect", CAR_X[0] - 0.6 + O, CAR_Y[0] - 0.5, CAR_X[1] - CAR_X[0] + 1.2,
                                    CAR_Y[1] - CAR_Y[0] + 1.0)]),
        "dinding_bawah": dict(size=(W + 2 * A, D), holes=[(x + O, y) for x, y in tb["B"]], cuts=[]),
        "dinding_kiri": dict(size=(D, H), holes=sd["L"] + rail_side,
                             cuts=[("circle", 8.0, 120.0, 3.1),                              # saklar daya
                                   ("rect", USBC[0] - 5.0, USBC[1] - 2.3, 10.0, 4.6)]),     # port cas USB-C
        "dinding_kanan": dict(size=(D, H), holes=sd["R"] + rail_side +
                              [((CAR_Y[0] + CAR_Y[1]) / 2, z) for z in (40, 110, 180)], cuts=[]),
    }
    return specs


def wall_local(spec):
    w, h = spec["size"]
    cs = CrossSection.square([w, h])
    cuts = [CrossSection.circle(CLEAR / 2, 32).translate([x, y]) for x, y in spec["holes"]]
    for c in spec["cuts"]:
        if c[0] == "rect":
            cuts.append(CrossSection.square([c[3], c[4]]).translate([c[1], c[2]]))
        else:
            cuts.append(CrossSection.circle(c[3], 48).translate([c[1], c[2]]))
    cs = cs - CrossSection.batch_boolean(cuts, manifold3d_op("add"))
    m = cs.extrude(A)
    cones = [Manifold.cylinder(1.8, 3.3, 1.5, 32).translate([x, y, -0.01]) for x, y in spec["holes"]]
    return m - union(cones)


WALL_M = {"dinding_depan": [[1, 0, 0, -A], [0, 0, 1, -A], [0, 1, 0, -A]],
          "dinding_belakang": [[1, 0, 0, -A], [0, 0, -1, D + A], [0, 1, 0, -A]],
          "dinding_atas": [[1, 0, 0, -A], [0, 1, 0, 0], [0, 0, -1, H + A]],
          "dinding_bawah": [[1, 0, 0, -A], [0, 1, 0, 0], [0, 0, 1, -A]],
          "dinding_kiri": [[0, 0, 1, -A], [1, 0, 0, 0], [0, 1, 0, 0]],
          "dinding_kanan": [[0, 0, -1, W + A], [1, 0, 0, 0], [0, 1, 0, 0]]}


def front_extras():
    """Fitur yang menempel di dinding depan (koordinat perangkat): dudukan layar, kantong baterai, modul."""
    x0, z0, L, Wd = PCB
    ps = []
    for x in (x0 - 6, x0 + L + 6):
        for z in (z0 + 6, z0 + Wd - 6):
            ps.append(box(x - 3.5, x + 3.5, 0.0, PCB_T + LCD_T + 0.4, z - 3.5, z + 3.5))
    ps += [box(4, 55.5, 0, 12, 22, 24), box(4, 55.5, 0, 12, 60, 62), box(2, 4, 0, 12, 22, 62),
           box(55.5, 57.5, 0, 12, 22, 62)]                                                 # kantong LiPo
    ps += [box(0.3, 45, 0, 10, 66, 67.5), box(0.3, 45, 0, 10, 98.5, 100), box(45, 46.5, 0, 10, 66, 100)]  # modul IP5306
    cx0, cx1, cz0, cz1 = CAM                                                               # kantong ESP32-CAM
    ps += [box(cx0 - 1.9, cx1 + 1.9, 0, 9, cz0 - 1.9, cz0 - 0.4), box(cx0 - 1.9, cx1 + 1.9, 0, 9, cz1 + 0.4, cz1 + 1.9),
           box(cx0 - 1.9, cx0 - 0.4, 0, 9, cz0 - 1.9, cz1 + 1.9), box(cx1 + 0.4, cx1 + 1.9, 0, 9, cz0 - 1.9, cz1 + 1.9)]
    ps.append(cyl_y(*BUZ, 0, 10, 7.6) - cyl_y(*BUZ, -1, 11, 6.3))                          # cincin buzzer
    dx, dz = DHT                                                                           # kantong DHT11
    ps += [box(dx - 16, dx + 16, 0, 9, dz - 8.5, dz - 7), box(dx - 16, dx + 16, 0, 9, dz + 7, dz + 8.5),
           box(dx - 16, dx - 14.5, 0, 9, dz - 8.5, dz + 8.5), box(dx + 14.5, dx + 16, 0, 9, dz - 8.5, dz + 8.5)]
    m = union(ps)
    hl = [cyl_y(x, z, 2.0, 12.0, 1.3, 16) for x in (x0 - 6, x0 + L + 6) for z in (z0 + 6, z0 + Wd - 6)]
    return m - union(hl)


def part_klem_layar(top):
    x0, z0, L, Wd = PCB
    z = z0 + Wd - 6 if top else z0 + 6
    yb = LCD_T + PCB_T + 0.4
    m = box(x0 - 9.5, x0 + L + 9.5, yb + 0.0, yb + 3.0, z - 3.5, z + 3.5)
    for x in (x0 + 2, x0 + L - 8):
        m = m + box(x, x + 6, yb - 0.01, yb + 3.0, (z0 - 0.2 if not top else z0 + Wd - 5.8), (z0 + 5.8 if not top else z0 + Wd + 0.2))
    m = m - union([cyl_y(x, z, yb - 1, yb + 4, CLEAR / 2, 16) for x in (x0 - 6, x0 + L + 6)])
    return m


def front_cuts():
    """Lubang & cekungan di dinding depan (koordinat perangkat)."""
    c = [cyl_y(*CAM_LENS, -A - 1, 1, 4.5)]                                                 # lensa kamera
    c += [cyl_y(BUZ[0] + ox, BUZ[1] + oz, -A - 1, 1, 1.0, 16) for ox, oz in ((0, 0), (3.5, 0), (-3.5, 0), (0, 3.5), (0, -3.5))]
    fx, fz = FING
    c.append(box(fx - 4, fx + 4, -A - 1, 1, fz - 16.5, fz - 12))                            # lubang kabel sensor jari
    c += [cyl_y(x, z, -A - 1, 1, CLEAR / 2, 16) for x, z in FING_BOLT]                     # baut kantong jari
    dx, dz = DHT
    c += [box(dx + ox - 0.8, dx + ox + 0.8, -A - 1, 1, dz - 5, dz + 5) for ox in (-8, -4, 0, 4, 8)]  # ventilasi
    return union(c)


def part_kantong_jari():
    """Terowongan jari PPG (seperti oksimeter): menutup cahaya luar, MAX30102 di lantai dekat ujung jari."""
    fx, fz = FING
    y0, y1 = FING_Y
    blk = rbox_xz(fx, fz - 2.0, 28.0, 28.0, y0, y1, 5.0)                                     # x 61..89, z 30..58
    fl = rbox_xz(fx, fz - 2.5, 36.0, 35.0, y1 - 0.01, -A, 3.0)                               # flens ke dinding depan
    m = blk + fl
    bore = cyl_y(fx, fz, y0 - 1, -10.0, FING_R)
    lip = Manifold.cylinder(3.0, FING_R + 2.5, FING_R, 48).rotate([-90, 0, 0]).translate([fx, y0 - 0.01, fz])
    win = box(fx - 3.0, fx + 3.0, -20.0, -12.0, fz - 13.0, fz - FING_R + 0.5)               # jendela sensor
    pocket = box(fx - 8.0, fx + 8.0, -24.0, -8.0, fz - 17.5, fz - FING_R - 3.0)              # papan MAX30102
    wire = box(fx - 3.0, fx + 3.0, -9.0, -A + 1, fz - 16.0, fz - FING_R - 3.0)               # jalur kabel
    holes = [cyl_y(x, z, y1 - 1, -A + 1, CLEAR / 2, 16) for x, z in FING_BOLT]
    return m - union([bore, lip, win, pocket, wire] + holes)


def front_wall_device():
    sp = wall_specs()["dinding_depan"]
    return wall_local(sp).transform(WALL_M["dinding_depan"]) + front_extras() - front_cuts()


def walls_placed():
    out = {}
    for n, sp in wall_specs().items():
        out[n] = front_wall_device() if n == "dinding_depan" else wall_local(sp).transform(WALL_M[n])
    return out


# ============================================================== DUMMY
def dummies():
    s1, _, _ = mg90s_y(G1[0], G1[1], S1_CT, -1)
    s2, _, _ = mg90s_y(S2[0], S2[1], S2_CT, -1)
    x0, z0, L, Wd = PCB
    return [("servo", s1), ("servo", s2),
            ("pcb", box(x0, x0 + L, LCD_T + 0.4, LCD_T + 0.4 + PCB_T, z0, z0 + Wd)),
            ("lcd", box(x0 + 8, x0 + L - 9, 0.4, LCD_T + 0.4, z0, z0 + Wd)),
            ("bat", box(5, 55, 1.0, 11.0, 24.5, 58.5)),
            ("pcb", box(1.0, 26.0, 2.0, 3.6, 70.0, 95.0)),                                   # modul IP5306
            ("pcb", box(CAM[0], CAM[1], 5.0, 6.6, CAM[2], CAM[3])),                          # ESP32-CAM
            ("servo", box(CAM_LENS[0] - 4.25, CAM_LENS[0] + 4.25, 0.6, 5.0, CAM_LENS[1] - 4.25, CAM_LENS[1] + 4.25)),
            ("lcd", cyl_y(*CAM_LENS, 0.1, 0.7, 3.5)),
            ("servo", cyl_y(*BUZ, 0.4, 9.9, 6.0)),                                           # buzzer
            ("pcb", box(FING[0] - 7.5, FING[0] + 7.5, -23.5, -8.5, FING[1] - 15.6, FING[1] - 14.0)),   # MAX30102
            ("lcd", box(FING[0] - 2.8, FING[0] + 2.8, -17.6, -14.4, FING[1] - 14.0, FING[1] - 12.4)),
            ("pcb", box(DHT[0] - 14, DHT[0] + 14, 6.0, 7.6, DHT[1] - 6.5, DHT[1] + 6.5)),      # DHT11
            ("dht", box(DHT[0] - 7.8, DHT[0] + 7.8, 0.4, 6.0, DHT[1] - 6.0, DHT[1] + 6.0))]


# ============================================================== EKSPOR
def _print_score(t):
    """(luas overhang >45 derajat yang butuh support, -luas yang menempel di bed)."""
    t = t.copy()
    t.apply_translation(-t.bounds[0])
    n, a, zc = t.face_normals, t.area_faces, t.triangles_center[:, 2]
    over = a[(n[:, 2] < -0.71) & (zc > 0.3)].sum()
    bed = a[(n[:, 2] < -0.99) & (zc < 0.3)].sum()
    return over - 0.25 * bed, over, bed


def auto_orient(t):
    """Pilih dari 6 sisi rebah: overhang paling kecil, bidang tempel paling luas."""
    best = None
    for ax, ang in (((1, 0, 0), 0), ((1, 0, 0), 180), ((1, 0, 0), 90), ((1, 0, 0), -90), ((0, 1, 0), 90), ((0, 1, 0), -90)):
        R = trimesh.transformations.rotation_matrix(math.radians(ang), ax)
        tt = t.copy(); tt.apply_transform(R)
        sc = _print_score(tt)
        if best is None or sc[0] < best[0][0] - 1e-6:
            best = (sc, tt)
    return best[1], best[0]


# ---- belah part panjang untuk printer bed 180 mm (Bambu Lab A1 mini): sambungan ekor burung + lem
BED = 180.0
SPLIT = {"01_dinding_depan": 125.0, "01_dinding_belakang": 125.0,     # y cetak = z perangkat + 3 (di atas layar, di bawah kamera)
         "01_dinding_kiri": 100.0, "01_dinding_kanan": 100.0,         # di antara port USB-C/saklar & baut pemandu
         "19_wadah_belakang": None}                                   # None = di tengah antara baris 3 dan 4
DT_NECK, DT_HEAD, DT_LEN, DT_FIT, DT_GAP = 6.0, 9.5, 6.0, 0.1, 22.0
DT_MINI = {"19_wadah_belakang": (3.5, 5.5, 3.5, 9.0)}                 # leher, kepala, panjang, jarak min (sela kantong sempit)


def _from_tm(t):
    from manifold3d import Mesh
    return Manifold(Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))


def _dovetail(x, yc, z0, z1, d, dim=None):
    """Tonjolan ekor burung di x (leher di y=yc, kepala ke +y); d = offset (+ longgar, - ketat)."""
    nk, hd, ln = dim or (DT_NECK, DT_HEAD, DT_LEN)
    pts = [(x - nk / 2 - d, yc - 1.0), (x + nk / 2 + d, yc - 1.0),
           (x + hd / 2 + d, yc + ln + d), (x - hd / 2 - d, yc + ln + d)]
    return Manifold.extrude(CrossSection([pts]), z1 - z0).translate([0, 0, z0])


def split_y(t, yc, mini=None):
    """Belah mesh posisi cetak t (trimesh) di y = yc -> (bawah, atas, jumlah tonjolan)."""
    dim, gap = (mini[:3], mini[3]) if mini else (None, DT_GAP)
    hd, ln = (dim or (DT_NECK, DT_HEAD, DT_LEN))[1:]
    m = _from_tm(t)
    (x0, y0, z0), (x1, y1, z1) = t.bounds
    zt = min(1.6, z1 - z0)                                         # lapisan dasar yang harus pejal
    base = m ^ box(x0 - 1, x1 + 1, y0 - 1, y1 + 1, z0 - 1, z0 + zt)
    xs, last = [], -1e9
    for x in np.arange(x0 + hd, x1 - hd, 0.5):
        if x - last < gap:
            continue
        probe = (_dovetail(x, yc, z0, z0 + zt, 1.0, dim) + box(x - hd / 2 - 1, x + hd / 2 + 1, yc - ln - 1, yc, z0, z0 + zt))
        if (base ^ probe).volume() >= 0.98 * probe.volume():
            xs.append(x)
            last = x
    def cutter(d):
        c = box(x0 - 1, x1 + 1, y0 - 1, yc + d, z0 - 1, z1 + 1)
        for x in xs:
            c = c + _dovetail(x, yc, z0 - 1, z1 + 1, d, dim)
        return c
    lo, hi = m ^ cutter(-DT_FIT), m - cutter(DT_FIT)
    return to_tm(lo), to_tm(hi), len(xs)


def save(name, m, rot=None):
    t = to_tm(m)
    if not name.startswith("01_"):                 # dinding: muka luar sudah di bed
        t, _ = auto_orient(t)
    t.apply_translation(-t.bounds[0])
    if name in SPLIT:
        yc = SPLIT[name]
        if yc is None:                                             # wadah belakang: sela antara baris 3 dan 4
            yc = CAR_BOT + BL_MZ + 3 * PZ
        lo, hi, n = split_y(t, yc, DT_MINI.get(name))
        for sfx, part in (("_A_bawah", lo), ("_B_atas", hi)):
            part.apply_translation(-part.bounds[0])
            part.export(os.path.join(OUT, "stl", name + sfx + ".stl"))
        print(f"    belah {name} di y={yc:.1f}: {n} ekor burung")
        return t
    t.export(os.path.join(OUT, "stl", name + ".stl"))
    return t


def all_parts():
    cb = cb_at(1)
    p = {}
    for i, (n, sp) in enumerate(wall_specs().items()):
        p[f"01_{n}"] = ((front_wall_device().transform([[1, 0, 0, A], [0, 0, 1, A], [0, 1, 0, A]])
                         if n == "dinding_depan" else wall_local(sp)), None)
    for n in CORNERS:
        p[f"02_blok_sudut_{n}"] = (part_blok(n), None)
    p["03_rel_kereta"] = (part_rel(), None)
    p["04_kereta"] = (kereta(XC), RX(90))
    p["05_pelatuk"] = (pelatuk(XC), None)
    p["06_engkol_servo3"] = (engkol3(XC), None)
    p["07_tuas_servo2"] = (part_tuas(), RX(90))
    p["08_braket_servo2"] = (part_braket_s2(), RX(-90))
    p["09_braket_servo1"] = (part_braket_s1(), RX(-90))
    p["10_gear_G1_40T"] = (part_g1(), RX(90))
    p["11_gear_G2_36T-12T"] = (part_g2(), RX(90))
    p["12_spacer_G2"] = (part_spacer_g2(), RX(90))
    p["13_pemandu_kiri"] = (part_pemandu_kiri(), RX(90))
    p["14_pemandu_kanan"] = (part_pemandu_kanan(), RX(90))
    p["15_landasan"] = (part_landasan(), RX(-90))
    p["16_corong_baki"] = (part_corong(), RX(-90))
    p["17_klem_layar_atas"] = (part_klem_layar(True), RX(90))
    p["18_klem_layar_bawah"] = (part_klem_layar(False), RX(90))
    p["19_wadah_belakang"] = (wadah_belakang(cb), RX(-90))
    p["20_wadah_depan"] = (wadah_depan(cb), RX(90))
    p["21_kantong_jari_ppg"] = (part_kantong_jari(), None)
    return p


def statics():
    s = {"rel": part_rel(), "corong": part_corong(), "landasan": part_landasan(), "pemandu_kiri": part_pemandu_kiri(),
         "pemandu_kanan": part_pemandu_kanan(), "braket_s1": part_braket_s1(), "braket_s2": part_braket_s2(),
         "G1": part_g1(), "spacer": part_spacer_g2(), "klem_a": part_klem_layar(True), "klem_b": part_klem_layar(False),
         "depan_extra": front_extras(), "kantong_jari": part_kantong_jari()}
    s.update({f"blok_{n}": part_blok(n) for n in CORNERS})
    return s


def collisions():
    msg = []
    st = statics()
    dm = dict(enumerate(dummies()))

    def hit(a, b, na, nb, tol=0.05):
        v = (a ^ b).volume()
        if v > tol:
            msg.append(f"TABRAKAN {na} x {nb}: {v:.2f} mm3")

    names = list(st)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            hit(st[a], st[b], a, b)
    for k, (kind, m) in dm.items():
        for n in names:
            if kind != "lcd" and kind != "pcb":
                hit(m, st[n], f"dummy_{kind}{k}", n)
    g2 = part_g2()
    for n in names:
        if n not in ("G1", "spacer"):
            hit(g2, st[n], "G2", n)
    for k in (1, 4, 7):
        cb = cb_at(k)
        car = wadah_belakang(cb) + wadah_depan(cb)
        for n in names + ["G2"]:
            if n in ("G2",):
                continue
            hit(car, st[n], f"wadah@baris{k}", n)
        for c in (1, 4):
            xs = pocket_xz(c, k, cb)[0]
            for th in (0, 180):
                mv = kereta(xs) + engkol3(xs, th) + pelatuk(xs, th) + servo3_dummy(xs)
                hit(mv, car, f"kereta@k{c}/{th}", f"wadah@baris{k}")
                _, domes, _ = blister_parts(cb)
                if th == 0:
                    for (cc, rr), dm_ in domes:
                        hit(mv, dm_, f"kereta@k{c}", f"kubah{cc},{rr}")
                for n in names:
                    hit(mv, st[n], f"kereta@k{c}/{th}", n)
                tu = part_tuas(lever_angle(xs))
                for n in names:
                    if n != "corong":
                        hit(tu, st[n], f"tuas@k{c}", n)
                hit(tu, kereta(xs), f"tuas@k{c}", "kereta", tol=1.0)
    return msg


if __name__ == "__main__":
    os.makedirs(os.path.join(OUT, "stl"), exist_ok=True)
    for f in os.listdir(os.path.join(OUT, "stl")):
        os.remove(os.path.join(OUT, "stl", f))
    tot = 0.0
    for name, (m, rot) in all_parts().items():
        t = save(name, m, rot)
        e = t.bounds[1] - t.bounds[0]
        g = t.volume / 1000 * 1.24
        tot += g
        ok = len(m.decompose()) == 1
        print(f"  {name:26s} {e[0]:6.1f} x {e[1]:6.1f} x {e[2]:6.1f}  ~{g:5.1f} g padat  {'utuh' if ok else 'MULTI-BODY'}")
    print(f"Kotak luar {W + 2 * A:.0f} x {H + 2 * A:.0f} x {D + 2 * A:.0f} mm; total ~{tot:.0f} g padat")
    print(f"Servo1: {MM_PER_RAD_1:.1f} mm/rad; langkah wadah {CB_EJ - cb_at(7):.1f} mm = "
          f"{math.degrees((CB_EJ - cb_at(7)) / MM_PER_RAD_1):.0f} deg")
    for c in range(1, 5):
        print(f"  kolom {c}: x={pocket_xz(c, 1, 0)[0]:.0f}  tuas servo2 = {math.degrees(lever_angle(pocket_xz(c, 1, 0)[0])):+.1f} deg")
    for line in collisions() or ["Cek tabrakan: aman"]:
        print(line)
