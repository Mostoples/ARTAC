"""Konversi ikon 3D + latar gradien ke array C LVGL 8 (RGB565 byte-swapped + alpha, sesuai LV_COLOR_16_SWAP=1).

  python buat_aset_lvgl.py   ->  firmware/ARTA-C_CYD_UI/ui_img.c / ui_img.h
"""
import math
import pathlib

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parent / "firmware" / "ARTA-C_CYD_UI"
IKON = HERE / "ikon"
SWAP = True

# nama_c : (file ikon, sisi px)
ICONS = {"pil_100": ("pil", 100), "pil_58": ("pil", 58), "jantung_92": ("jantung", 92), "tetes_34": ("tetes", 34),
         "blister_58": ("blister", 58), "centang_44": ("centang", 44), "centang_84": ("centang", 84),
         "lonceng_100": ("lonceng", 100), "wadah_96": ("wadah", 96), "baterai_14": ("baterai", 14),
         "termometer_14": ("termometer", 14)}
BGS = {"bg_blue": [(0.8, -0.1, (47, 123, 255)), (0.28, (22, 70, 214)), (0.7, (11, 30, 74))],
       "bg_red": [(0.8, -0.1, (255, 90, 114)), (0.32, (142, 31, 74)), (0.75, (26, 14, 46))],
       "bg_green": [(0.5, -0.1, (60, 227, 160)), (0.32, (14, 122, 94)), (0.75, (6, 35, 58))]}


def rgb565(r, g, b):
    c = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
    return [(c >> 8) & 0xFF, c & 0xFF] if SWAP else [c & 0xFF, (c >> 8) & 0xFF]


def radial(w, h, spec):
    (cx, cy, c0), (s1, c1), (s2, c2) = spec[0], spec[1], spec[2]
    im = Image.new("RGB", (w, h))
    px = im.load()
    for y in range(h):
        for x in range(w):
            dx, dy = (x / w - cx) / 1.1, (y / h - cy) / 0.9
            t = math.hypot(dx, dy)
            if t <= s1:
                k = t / s1; a, b = c0, c1
            else:
                k = min(1, (t - s1) / (s2 - s1)); a, b = c1, c2
            k = k * k * (3 - 2 * k)
            px[x, y] = tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))
    return im


def emit(name, im, alpha):
    w, h = im.size
    data = []
    if alpha:
        im = im.convert("RGBA")
        for r, g, b, a in im.getdata():
            data += rgb565(r, g, b) + [a]
    else:
        for r, g, b in im.convert("RGB").getdata():
            data += rgb565(r, g, b)
    rows = ",\n".join("  " + ",".join(f"0x{v:02X}" for v in data[i:i + 24]) for i in range(0, len(data), 24))
    cf = "LV_IMG_CF_TRUE_COLOR_ALPHA" if alpha else "LV_IMG_CF_TRUE_COLOR"
    return (f"static const uint8_t {name}_map[] = {{\n{rows}\n}};\n"
            f"const lv_img_dsc_t {name} = {{ .header.always_zero = 0, .header.w = {w}, .header.h = {h},\n"
            f"  .header.cf = {cf}, .data_size = {len(data)}, .data = {name}_map }};\n\n"), len(data)


def main():
    out_c = ['/* Dibuat otomatis oleh ui3d/buat_aset_lvgl.py - jangan diedit manual */\n#include "lvgl.h"\n\n']
    names, total = [], 0
    for n, (f, s) in ICONS.items():
        im = Image.open(IKON / f"{f}.png").convert("RGBA")
        im.thumbnail((s, s), Image.LANCZOS)
        c, sz = emit(n, im, True); out_c.append(c); names.append(n); total += sz
    for n, spec in BGS.items():
        c, sz = emit(n, radial(160, 120, spec), False); out_c.append(c); names.append(n); total += sz
    (OUT / "ui_img.c").write_text("".join(out_c), encoding="utf-8")
    h = ["#pragma once\n#include \"lvgl.h\"\n"] + [f"extern const lv_img_dsc_t {n};\n" for n in names]
    (OUT / "ui_img.h").write_text("".join(h), encoding="utf-8")
    print(f"{len(names)} gambar, {total / 1024:.0f} KB data")


if __name__ == "__main__":
    main()
