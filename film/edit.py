"""Edit akhir film "Day 47": grafis 2D, overlay judul/label, subtitle, letterbox 2.35:1, grade, encode.

  python edit.py [--only T0-T1] [--still t1,t2,..]  ->  ARTA-C_Day47_documentary.mp4  (atau _qa/still_*.png)
"""
import json
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from naskah import ffbin
from timeline import DIPS, DUR, FPS, SEGMENTS, VO_START

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FR = os.path.join(HERE, "_frames")
W, H, PH = 1920, 1080, 816
TOP = (H - PH) // 2
FONT = os.path.join(ROOT, "ui3d", "font", "pj{}.ttf")
IKON = os.path.join(ROOT, "ui3d", "ikon")
OUT = os.path.join(HERE, "ARTA-C_Day47_documentary.mp4")

BLUE, SKY, DEEP, INK = (47, 123, 255), (95, 162, 255), (22, 70, 214), (11, 30, 74)
WHITE, MUTE, RED, GREEN, AMBER = (243, 247, 255), (134, 162, 214), (232, 54, 78), (25, 185, 122), (245, 165, 36)

_fc = {}


def font(w, s):
    k = (w, s)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FONT.format(w), s)
    return _fc[k]


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def seg(t, a, b):
    return clamp((t - a) / (b - a))


def ease(t):
    t = clamp(t)
    return t * t * t * (t * (6 * t - 15) + 10)


def out_cubic(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


class BD:
    """ImageDraw yang mencampur alpha juga untuk teks (blend RGBA bawaan Pillow hanya untuk bentuk)."""

    def __init__(self, im):
        self.im, self.d = im, ImageDraw.Draw(im, "RGBA")

    def __getattr__(self, k):
        return getattr(self.d, k)

    def text(self, xy, s, font=None, fill=None, anchor="la", **kw):
        if fill is None or len(fill) == 3 or fill[3] >= 255:
            return self.d.text(xy, s, font=font, fill=fill, anchor=anchor, **kw)
        if fill[3] <= 0:
            return
        x0, y0, x1, y1 = self.d.textbbox(xy, s, font=font, anchor=anchor)
        x0, y0 = int(x0) - 3, int(y0) - 3
        lay = Image.new("RGBA", (int(x1) - x0 + 6, int(y1) - y0 + 6), (0, 0, 0, 0))
        ImageDraw.Draw(lay).text((xy[0] - x0, xy[1] - y0), s, font=font, fill=fill, anchor=anchor, **kw)
        self.im.paste(lay, (x0, y0), lay)


# ---------------------------------------------------------------- aset
def sprite_dot(r, fill, ring=None, glow=None, ss=4):
    s = int((r + 14) * 2)
    im = Image.new("RGBA", (s * ss, s * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = s * ss / 2
    if glow:
        g = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(g).ellipse([c - r * ss * 1.6, c - r * ss * 1.6, c + r * ss * 1.6, c + r * ss * 1.6], fill=glow)
        im = Image.alpha_composite(im, g.filter(ImageFilter.GaussianBlur(5 * ss)))
        d = ImageDraw.Draw(im)
    if fill:
        d.ellipse([c - r * ss, c - r * ss, c + r * ss, c + r * ss], fill=fill)
    if ring:
        d.ellipse([c - r * ss, c - r * ss, c + r * ss, c + r * ss], outline=ring, width=int(1.6 * ss))
    return im.resize((s, s), Image.LANCZOS)


DOT_R = 11
DOTS = {
    "lit": sprite_dot(DOT_R, BLUE + (255,), glow=SKY + (150,)),
    "lit2": sprite_dot(DOT_R, SKY + (255,), glow=SKY + (200,)),
    "dim": sprite_dot(DOT_R, None, ring=(70, 98, 160, 200)),
    "miss": sprite_dot(DOT_R, (90, 24, 40, 150), ring=RED + (230,)),
    "green": sprite_dot(DOT_R, GREEN + (255,), glow=(25, 185, 122, 120)),
}


def icon(name, size):
    k = ("ico", name, size)
    if k not in _fc:
        _fc[k] = Image.open(os.path.join(IKON, f"{name}.png")).convert("RGBA").resize((size, size), Image.LANCZOS)
    return _fc[k]


def background():
    y, x = np.mgrid[0:PH, 0:W].astype(np.float32)
    d = np.sqrt(((x - W * 0.5) / (W * 0.7)) ** 2 + ((y - PH * 0.42) / (PH * 0.9)) ** 2)
    k = np.clip(1 - d, 0, 1)[..., None]
    c0, c1 = np.array([5, 11, 28], np.float32), np.array([16, 40, 96], np.float32)
    return Image.fromarray((c0 + (c1 - c0) * k ** 1.6).astype(np.uint8), "RGB")


BG = background()
yy, xx = np.mgrid[0:PH, 0:W].astype(np.float32)
VIG = np.clip(1.0 - 0.38 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - PH / 2) / (PH / 2)) ** 2) ** 1.4, 0.45, 1)[..., None]
RNG = np.random.default_rng(7)
GRAIN = [RNG.normal(0, 3.2, (PH, W, 1)).astype(np.float32) for _ in range(6)]


def text_c(d, xy, s, f, fill, anchor="mm", spacing=0):
    if spacing:
        # huruf berjarak (tracking) manual
        total = sum(f.getlength(ch) + spacing for ch in s) - spacing
        x = xy[0] - total / 2 if anchor[0] == "m" else xy[0]
        for ch in s:
            d.text((x, xy[1]), ch, font=f, fill=fill, anchor="l" + anchor[1])
            x += f.getlength(ch) + spacing
        return
    d.text(xy, s, font=f, fill=fill, anchor=anchor)


def alpha(c, a):
    return tuple(c[:3]) + (int(255 * clamp(a)),)


# ---------------------------------------------------------------- grid 180 hari
GC, GR, GS = 30, 6, 46
GX0, GY0 = (W - (GC - 1) * GS) / 2, 360


def dot_xy(i):
    return GX0 + (i % GC) * GS, GY0 + (i // GC) * GS


MISSED = sorted(set(int(x) for x in np.random.default_rng(3).choice(np.arange(24, 180), 52, replace=False)))


def draw_grid(im, states):
    for i, st in enumerate(states):
        if st is None:
            continue
        name, a = st
        sp = DOTS[name]
        x, y = dot_xy(i)
        if a < 1:
            sp = sp.copy()
            sp.putalpha(sp.getchannel("A").point(lambda v: int(v * a)))
        im.paste(sp, (int(x - sp.width / 2), int(y - sp.height / 2)), sp)


def seg_days(t):
    im = BG.copy()
    d = BD(im)
    a1 = ease(seg(t, 0.3, 1.0)) * (1 - ease(seg(t, 1.9, 2.4)))
    if a1 > 0:
        text_c(d, (W / 2, PH / 2 - 10 - 20 * ease(seg(t, 1.9, 2.4))), "SIX MONTHS", font(800, 120), alpha(WHITE, a1), spacing=14)
    if t > 1.9:
        n = int(clamp((t - 2.0) / 4.4) * 180)
        draw_grid(im, [("lit2" if n - 3 <= i < n else "lit", 1.0) if i < n else ("dim", ease(seg(t, 1.9, 2.6)))
                       for i in range(180)])
        a = ease(seg(t, 2.1, 2.8))
        text_c(d, (W / 2, 210), f"{n:3d}", font(800, 96), alpha(WHITE, a))
        text_c(d, (W / 2, 280), "MORNINGS", font(700, 26), alpha(SKY, a), spacing=10)
        a2 = ease(seg(t, 5.2, 6.0))
        text_c(d, (W / 2, 690), "Every single dose.", font(700, 40), alpha(WHITE, a2))
    return im


def seg_slip(t):
    im = BG.copy()
    d = BD(im)
    # sorot minggu ke-3, lalu titik-titik mulai bolong
    k = ease(seg(t, 2.8, 6.4))
    states = []
    for i in range(180):
        if i in MISSED and MISSED.index(i) < k * len(MISSED):
            states.append(("miss", 1.0))
        else:
            states.append(("lit", 1.0 - 0.45 * k if i >= 21 else 1.0))
    draw_grid(im, states)
    x21 = dot_xy(21)[0] - GS / 2
    a = ease(seg(t, 0.3, 1.0))
    d.line([(x21, GY0 - 40), (x21, GY0 + 5 * GS + 30)], fill=alpha(GREEN, a), width=2)
    text_c(d, (x21 + 14, GY0 - 58), "WEEK 3", font(800, 22), alpha(GREEN, a), anchor="lm", spacing=4)
    a1 = ease(seg(t, 0.8, 1.6)) * (1 - 0.5 * ease(seg(t, 3.0, 3.6)))
    text_c(d, (W / 2 - 230, 200), "feel better", font(800, 64), alpha(GREEN, a1))
    a2 = ease(seg(t, 3.1, 3.8))
    text_c(d, (W / 2 + 250, 200), "doses slip", font(800, 64), alpha(RED, a2))
    if a2 > 0:
        text_c(d, (W / 2, 690), "Missed doses:  relapse  ·  drug resistance", font(600, 30), alpha(MUTE, ease(seg(t, 4.4, 5.2))))
    return im


PAT = [(math.cos(a) * 520, math.sin(a) * 250) for a in np.linspace(0, 2 * math.pi, 11)[:-1] + 0.3]


def seg_pmo(t):
    # digambar 2x lalu diperkecil (garis halus)
    S = 2
    im = BG.resize((W * S, PH * S))
    d = BD(im)
    cx, cy = W / 2 * S, (PH / 2 + 20) * S
    fade = 1 - ease(seg(t, 4.6, 8.0))
    for i, (px, py) in enumerate(PAT):
        x, y = cx + px * S, cy + py * S
        dl = ease(seg(t, 1.0 + i * 0.12, 1.8 + i * 0.12))
        flick = 1.0
        if t > 4.6:
            flick = fade * (0.6 + 0.4 * math.sin(t * 13 + i * 2.1)) if (i % 3) else fade * 0.5
        if dl > 0:
            ex, ey = cx + (x - cx) * dl, cy + (y - cy) * dl
            d.line([(cx, cy), (ex, ey)], fill=alpha(SKY, 0.65 * flick), width=3 * S)
        a = ease(seg(t, 1.6 + i * 0.12, 2.2 + i * 0.12))
        r = 18 * S
        d.ellipse([x - r, y - r, x + r, y + r], fill=alpha((34, 56, 110), a), outline=alpha(SKY, a), width=2 * S)
        if t > 6.0:                                         # alarm pagi berbunyi, tanpa pengawas
            ph = ((t - 6.0) * 1.3 + i * 0.37) % 1.0
            rr = r + ph * 46 * S
            d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=alpha(AMBER, (1 - ph) * 0.8), width=2 * S)
    a = ease(seg(t, 0.2, 0.9))
    r = 70 * S
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=alpha(DEEP, a), outline=alpha(SKY, a), width=3 * S)
    text_c(d, (cx, cy - 4 * S), "PMO", font(800, 46 * S), alpha(WHITE, a))
    im = im.resize((W, PH), Image.LANCZOS)
    d = BD(im)
    a = ease(seg(t, 0.5, 1.2)) * (1 - ease(seg(t, 4.2, 4.8)))
    text_c(d, (W / 2, 70), "Pengawas Menelan Obat  ·  treatment supervisor", font(700, 30), alpha(SKY, a))
    a = ease(seg(t, 4.8, 5.4))
    hh = 6 + clamp((t - 4.8) / 6.0) * 1.0
    text_c(d, (W / 2, 70), f"{int(hh):02d}:{int((hh % 1) * 60):02d}", font(800, 44), alpha(WHITE, a))
    text_c(d, (W / 2, 745), "One supervisor.  Many mornings.  Many patients.", font(600, 30), alpha(MUTE, ease(seg(t, 6.6, 7.4))))
    return im


def seg_count(t):
    im = BG.copy()
    d = BD(im)
    n = int(round(47 * out_cubic(seg(t, 0.2, 2.8))))
    states = []
    for i in range(180):
        if i < n:
            states.append(("green" if i == n - 1 and t < 3.0 else "lit", 1.0))
        else:
            states.append(("dim", 0.55 + 0.45 * math.sin(t * 3 - i * 0.15) ** 2 if t > 3.0 else 0.7))
    draw_grid(im, states)
    text_c(d, (W / 2, 205), f"DAY {max(1, n)}", font(800, 110), alpha(WHITE, ease(seg(t, 0.0, 0.5))), spacing=6)
    a = ease(seg(t, 2.9, 3.6))
    text_c(d, (W / 2, 690), "133 to go", font(800, 52), alpha(SKY, a))
    text_c(d, (W / 2, 745), "zero missed", font(700, 26), alpha(GREEN, ease(seg(t, 3.6, 4.2))), spacing=6)
    return im


# ---------------------------------------------------------------- overlay 3D
def wordmark(d, x, y, size, a):
    f = font(800, size)
    d.text((x, y), "ARTA", font=f, fill=alpha(WHITE, a), anchor="ls")
    d.text((x + f.getlength("ARTA"), y), "-C", font=f, fill=alpha(SKY, a), anchor="ls")


def label(im, t, a0, a1, title, sub, x=110, y=110, ico=None):
    a = ease(seg(t, a0, a0 + 0.5)) * (1 - ease(seg(t, a1 - 0.5, a1)))
    if a <= 0:
        return
    d = BD(im)
    off = 24 * (1 - out_cubic(seg(t, a0, a0 + 0.6)))
    xx = x - off
    tw = max(font(800, 30).getlength(title), font(600, 21).getlength(sub)) + (80 if ico else 0) + 44
    d.rounded_rectangle([xx - 22, y - 22, xx + tw, y + 86], 18, fill=(5, 11, 28, int(170 * a)))
    if ico:
        ic = icon(ico, 64).copy()
        ic.putalpha(ic.getchannel("A").point(lambda v: int(v * a)))
        im.paste(ic, (int(xx), int(y - 8)), ic)
        xx += 80
    d.line([(xx, y + 4), (xx, y + 58)], fill=alpha(SKY, a), width=3)
    d.text((xx + 18, y + 2), title, font=font(800, 30), fill=alpha(WHITE, a), anchor="lt")
    d.text((xx + 18, y + 40), sub, font=font(600, 21), fill=alpha(MUTE, a), anchor="lt")


def phone(im, t):
    """Ponsel PMO di kanan: notifikasi 'Dose taken - verified' meluncur masuk."""
    k = out_cubic(seg(t, 1.2, 2.2))
    if k <= 0:
        return
    pw, ph_ = 330, 640
    x0, y0 = 1420, int(PH - 60 - ph_ * k * 0.92)
    S = 2
    L = Image.new("RGBA", (pw * S + 40, ph_ * S + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    d.rounded_rectangle([20, 20, 20 + pw * S, 20 + ph_ * S], 52 * S // 2, fill=(9, 14, 30, 255), outline=(70, 90, 130, 255), width=3 * S)
    d.rounded_rectangle([20 + 12 * S, 20 + 12 * S, 20 + (pw - 12) * S, 20 + (ph_ - 12) * S], 40 * S // 2, fill=(14, 28, 66, 255))
    d.rounded_rectangle([20 + (pw / 2 - 45) * S, 20 + 24 * S, 20 + (pw / 2 + 45) * S, 20 + 46 * S], 22, fill=(0, 0, 0, 255))
    d.text((20 + pw / 2 * S, 20 + 110 * S), "07:01", font=font(800, 64 * S), fill=WHITE, anchor="mm")
    d.text((20 + pw / 2 * S, 20 + 160 * S), "Thursday · Day 47", font=font(600, 16 * S), fill=MUTE, anchor="mm")
    # kartu notifikasi
    c = out_cubic(seg(t, 2.1, 2.7))
    if c > 0:
        cy = 20 + (215 + 30 * (1 - c)) * S
        card = [20 + 26 * S, cy, 20 + (pw - 26) * S, cy + 190 * S]
        d.rounded_rectangle(card, 22 * S, fill=(236, 242, 252, 255))
        d.rounded_rectangle([card[0] + 16 * S, cy + 16 * S, card[0] + 52 * S, cy + 52 * S], 10 * S, fill=BLUE + (255,))
        d.text((card[0] + 34 * S, cy + 34 * S), "A", font=font(800, 20 * S), fill=(255, 255, 255, 255), anchor="mm")
        d.text((card[0] + 64 * S, cy + 22 * S), "ARTA-C  ·  now", font=font(700, 14 * S), fill=(80, 96, 128, 255))
        d.text((card[0] + 16 * S, cy + 70 * S), "Dose taken", font=font(800, 26 * S), fill=(18, 35, 63, 255))
        d.text((card[0] + 16 * S, cy + 108 * S), "Patient #047 · 3 caplets FDC", font=font(600, 14 * S), fill=(74, 90, 122, 255))
        d.text((card[0] + 16 * S, cy + 134 * S), "Face match · HR 78 · SpO2 98%", font=font(700, 14 * S), fill=(25, 140, 95, 255))
        d.text((card[0] + 16 * S, cy + 158 * S), "Verified 07:01 · streak 12 days", font=font(600, 13 * S), fill=(74, 90, 122, 255))
    L = L.resize((L.width // S, L.height // S), Image.LANCZOS)
    sh = Image.new("RGBA", (L.width + 80, L.height + 80), (0, 0, 0, 0))
    sh.paste((0, 0, 0, 150), (40, 60, 40 + L.width, 60 + L.height), L.getchannel("A"))
    sh = sh.filter(ImageFilter.GaussianBlur(22))
    im.paste(sh, (x0 - 40, y0 - 30), sh)
    im.paste(L, (x0, y0), L)
    if c > 0:
        ic = icon("centang", 92).copy()
        ic.putalpha(ic.getchannel("A").point(lambda v: int(v * c)))
        im.paste(ic, (x0 + pw - 70, y0 + 205), ic)


_gx = np.clip(1.0 - (np.arange(W) - 260) / 700.0, 0, 1) ** 1.3
END_SHADE = Image.fromarray((np.tile(_gx, (PH, 1)) * 255).astype(np.uint8), "L")


def overlay(name, im, t):
    d = BD(im)
    if name == "dawn":
        a = ease(seg(t, 1.0, 1.8)) * (1 - ease(seg(t, 7.2, 8.0)))
        n = int(clamp((t - 1.0) / 1.0) * 16)
        s = "DAY 47  ·  06:52  ·  AT HOME"[:n + 12]
        d.text((110, 96), s, font=font(800, 24), fill=alpha(WHITE, a * 0.92), anchor="lt")
        d.line([(110, 136), (110 + 90 * ease(seg(t, 1.4, 2.4)), 136)], fill=alpha(SKY, a), width=3)
    elif name == "reveal":
        a = ease(seg(t, 4.35, 5.0))
        wordmark(d, 90, 470, 112, a)
        d.text((94, 510), "SMART TB MEDICATION COMPANION", font=font(700, 20), fill=alpha(SKY, ease(seg(t, 4.9, 5.6))), anchor="lt")
    elif name == "face":
        label(im, t, 0.5, 4.4, "Who is taking it?", "ESP32-CAM face check · on-device", ico="wajah")
    elif name == "ppg":
        label(im, t, 2.6, 6.4, "Pulse & SpO2", "MAX30102 · light-sealed finger tunnel", ico="jantung")
    elif name == "inside":
        label(im, t, 0.8, 6.9, "The original blister", "Lowered row by row · servo + rack", ico="blister")
    elif name == "peck":
        label(im, t, 0.4, 8.4, "One caplet. Through the foil.", "Servo crank · plunger · chute to tray", ico="pil")
    elif name == "notify":
        phone(im, t)
        label(im, t, 0.6, 8.9, "Verified intake", "Face match  ·  PPG check  ·  caplet released", x=110, y=110, ico="centang")
    elif name == "end":
        g = ease(seg(t, 0.0, 1.0)) * 0.82
        im.paste((3, 7, 18), (0, 0), END_SHADE.point(lambda v: int(v * g)))
        a = ease(seg(t, 0.4, 1.3))
        wordmark(d, 150, 380, 160, a)
        d.text((156, 428), "SMART TB MEDICATION COMPANION", font=font(700, 24), fill=alpha(SKY, a), anchor="lt")
        a2 = ease(seg(t, 2.5, 3.3))
        d.text((152, 540), "No dose goes unseen.", font=font(800, 54), fill=alpha(WHITE, a2), anchor="ls")
        a3 = ease(seg(t, 3.6, 4.4))
        d.text((154, 600), "Concept prototype · 3D visualisation of the ARTA-C design", font=font(600, 18), fill=alpha(MUTE, a3), anchor="ls")
    return im


# ---------------------------------------------------------------- perakitan frame
VO = {m["id"]: m for m in json.load(open(os.path.join(HERE, "audio", "vo.json")))}
SUBS = [(VO_START[i], VO_START[i] + VO[i]["dur"] + 0.25, VO[i]["text"].replace("P.M.O.", "PMO.")) for i in VO]


def frame(i):
    t = i / FPS
    for a, b, src in SEGMENTS:
        if a <= t < b or (b == SEGMENTS[-1][1] and t >= a):
            break
    kind, name = src.split(":")
    lt = t - a
    if kind == "3d":
        n = len([f for f in os.listdir(os.path.join(FR, name)) if f.startswith("f_")]) if name not in _fc else _fc[name]
        _fc[name] = n
        k = min(n, int(round(lt * FPS)) + 1)
        p = os.path.join(FR, name, f"f_{k:04d}.png")
        im = Image.open(p).convert("RGB") if os.path.exists(p) else Image.new("RGB", (W, PH), (40, 0, 0))
        im = overlay(name, im, lt)
    else:
        im = {"days": seg_days, "slip": seg_slip, "pmo": seg_pmo, "count": seg_count}[name](lt)
    # grade: vignette + grain + sedikit split-tone
    x = np.asarray(im.convert("RGB"), dtype=np.float32)
    x = x * VIG + GRAIN[i % 6]
    x[..., 2] += 2.0
    # transisi lewat hitam + fade awal/akhir
    g = 1.0
    for tb, dd in DIPS.items():
        g = min(g, clamp(abs(t - tb) / (dd / 2)))
    g = min(g, ease(seg(t, 0.0, 1.2)), 1 - ease(seg(t, DUR - 2.2, DUR - 0.2)))
    x *= g
    canvas = Image.new("RGB", (W, H), (0, 0, 0))
    canvas.paste(Image.fromarray(np.clip(x, 0, 255).astype(np.uint8)), (0, TOP))
    d = ImageDraw.Draw(canvas)
    for s0, s1, txt in SUBS:
        if s0 <= t < s1:
            a = min(seg(t, s0, s0 + 0.2), 1 - seg(t, s1 - 0.2, s1))
            d.text((W / 2, TOP + PH + 66), txt, font=font(600, 31), fill=tuple(int(c * a) for c in (222, 230, 245)), anchor="mm")
    return canvas


def main():
    os.makedirs(os.path.join(HERE, "_qa"), exist_ok=True)
    if "--still" in sys.argv:
        for t in [float(v) for v in sys.argv[sys.argv.index("--still") + 1].split(",")]:
            frame(int(t * FPS)).save(os.path.join(HERE, "_qa", f"still_{t:05.1f}.png"))
        return
    t0, t1 = 0.0, DUR
    if "--only" in sys.argv:
        t0, t1 = (float(v) for v in sys.argv[sys.argv.index("--only") + 1].split("-"))
    out = OUT if (t0, t1) == (0.0, DUR) else os.path.join(HERE, "_qa", f"preview_{t0:g}-{t1:g}.mp4")
    ff = ffbin("ffmpeg")
    cmd = [ff, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-ss", f"{t0}", "-t", f"{t1 - t0}", "-i", os.path.join(HERE, "audio", "mix.wav"),
           "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "17", "-preset", "slow", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(t0 * FPS), int(t1 * FPS)):
        p.stdin.write(frame(i).tobytes())
        if i % 240 == 0:
            print("frame", i, flush=True)
    p.stdin.close()
    p.wait()
    print("OK", out)


if __name__ == "__main__":
    main()
