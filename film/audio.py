"""Musik orisinal (sintesis numpy), efek suara tersinkron, dan mix narasi untuk film "Day 47".

  python audio.py  ->  audio/music.wav, audio/sfx.wav, audio/vo_track.wav, audio/mix.wav (-17 LUFS)
"""
import json
import os
import subprocess
import wave

import numpy as np
from scipy.signal import fftconvolve, butter, sosfilt

from naskah import ffbin
from timeline import DUR, SFX, VO_START

HERE = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.join(HERE, "audio")
SR = 48000
N = int(DUR * SR)
rng = np.random.default_rng(47)


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def tvec(d):
    return np.arange(int(d * SR)) / SR


def place(buf, x, t0, pan=0.0, gain=1.0):
    """Tempel sinyal mono x ke buffer stereo buf pada detik t0 (pan -1..1, hukum daya konstan)."""
    i = int(t0 * SR)
    if i >= N or i + len(x) <= 0:
        return
    if i < 0:
        x, i = x[-i:], 0
    x = x[:N - i] * gain
    a = (pan + 1) * np.pi / 4
    buf[0, i:i + len(x)] += x * np.cos(a)
    buf[1, i:i + len(x)] += x * np.sin(a)


def env(n, att, rel, sus=None):
    e = np.ones(n)
    a, r = max(1, int(att * SR)), max(1, int(rel * SR))
    e[:a] = np.linspace(0, 1, a) ** 1.5
    e[-r:] *= np.linspace(1, 0, r) ** 1.5
    return e


def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, "low", fs=SR, output="sos"), x)


def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, "high", fs=SR, output="sos"), x)


def bp(x, f1, f2, order=2):
    return sosfilt(butter(order, [f1, f2], "band", fs=SR, output="sos"), x)


def reverb(st, secs=3.2, decay=1.1, wet=0.32, pre=0.02):
    n = int(secs * SR)
    t = np.arange(n) / SR
    out = np.zeros_like(st)
    for ch in range(2):
        ir = rng.standard_normal(n) * np.exp(-t / decay * 3)
        ir = lp(ir, 6500)
        ir[:int(pre * SR)] = 0
        ir /= np.sqrt(np.sum(ir ** 2))
        out[ch] = fftconvolve(st[ch], ir)[:st.shape[1]]
    return st * (1 - wet) + out * wet * 1.6


# ---------------------------------------------------------------- instrumen
def piano(f, d=3.5, vel=0.5):
    t = tvec(d)
    x = np.zeros_like(t)
    B = 0.0004
    for k in range(1, 9):
        fk = f * k * np.sqrt(1 + B * k * k)
        if fk > 12000:
            break
        x += (0.9 / k ** 1.25) * np.sin(2 * np.pi * fk * t + rng.uniform(0, 6)) * np.exp(-t * (0.9 + 0.55 * k))
    x *= env(len(t), 0.004, 0.25)
    x += 0.05 * lp(rng.standard_normal(len(t)), 3000) * np.exp(-t * 60)        # palu
    return lp(x, 2500 + 4000 * vel) * vel


def pad(freqs, d, att=2.0, rel=2.5, bright=4.0):
    t = tvec(d)
    x = np.zeros_like(t)
    for f in freqs:
        for det in (-0.006, 0.0, 0.0065):
            ff = f * (1 + det)
            ph = rng.uniform(0, 6.28)
            for k in range(1, 14):
                if ff * k > 7000:
                    break
                x += np.sin(2 * np.pi * ff * k * t + ph * k) / k * np.exp(-k / bright)
    x *= (1 + 0.12 * np.sin(2 * np.pi * 0.23 * t)) * env(len(t), att, rel)
    return lp(x, 2400) / (len(freqs) * 3)


def pluck(f, d=0.9, vel=0.4):
    t = tvec(d)
    x = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) + 0.12 * np.sin(6 * np.pi * f * t))
    return lp(x * np.exp(-t * 5.5) * env(len(t), 0.003, 0.1), 3500) * vel


def thump(d=0.5, f0=62, f1=38, vel=1.0):
    t = tvec(d)
    f = f1 + (f0 - f1) * np.exp(-t * 18)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 9) * vel


def boom(vel=1.0):
    t = tvec(4.0)
    f = 34 + 40 * np.exp(-t * 6)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.1)
    x += 0.5 * lp(rng.standard_normal(len(t)), 900) * np.exp(-t * 7)
    return x * env(len(t), 0.002, 0.8) * vel


def riser(d):
    t = tvec(d)
    n = rng.standard_normal(len(t))
    out = np.zeros_like(t)
    seg = int(0.05 * SR)
    for i in range(0, len(t), seg):             # band-pass bergeser ke atas
        u = i / len(t)
        fc = 300 * (8000 / 300) ** u
        out[i:i + seg] = bp(n[max(0, i - 2000):i + seg], fc * 0.7, min(fc * 1.4, 20000))[-len(out[i:i + seg]):]
    sweep = np.sin(2 * np.pi * np.cumsum(220 * (4 ** (t / d))) / SR) * 0.25
    return (out * 0.7 + sweep) * (t / d) ** 2.2 * env(len(t), 0.3, 0.03)


# ---------------------------------------------------------------- musik
def music():
    st = np.zeros((2, N))
    D3, F3, A3, C4, D4, E4, F4, G4, A4, Bb3, C5, D5 = (midi(n) for n in (50, 53, 57, 60, 62, 64, 65, 67, 69, 58, 72, 74))
    # A: pagi - Dm(add9) + motif piano
    place(st, pad([midi(38), D3, A3, E4], 18.5, att=3.5, rel=3.0, bright=3.0), 0.0, gain=0.55)
    motif = [(0.9, 69), (2.0, 65), (2.9, 64), (3.6, 62), (5.6, 69), (6.6, 72), (7.4, 69), (8.2, 67),
             (9.6, 65), (10.6, 64), (11.5, 62), (13.6, 69), (14.5, 65), (15.3, 64), (16.2, 62)]
    for t0, n in motif:
        place(st, piano(midi(n), 3.5, 0.42), t0, pan=rng.uniform(-0.3, 0.3))
    for t0 in (0.9, 5.6, 9.6, 13.6):
        place(st, piano(midi(38), 4.0, 0.3), t0, pan=-0.2)
    # B: tegang - Bb, Gm, Dm, A(sus4) + detak jantung yang makin cepat
    prog = [((46, 58, 62, 65), 17.0), ((43, 55, 58, 62), 21.5), ((38, 57, 62, 65), 26.0), ((45, 57, 62, 64), 30.5)]
    for ns, t0 in prog:
        place(st, pad([midi(n) for n in ns], 5.6, att=1.2, rel=1.6, bright=3.5), t0, gain=0.6)
    t, bpm = 17.0, 58.0
    while t < 34.6:
        place(st, thump(vel=0.55), t)
        place(st, thump(vel=0.33), t + 0.2)
        bpm = min(84, bpm + 1.8)
        t += 60 / bpm
    for t0, n in [(18.2, 70), (19.6, 69), (22.6, 67), (24.0, 65), (27.2, 69), (28.6, 70), (31.6, 69), (33.0, 68)]:
        place(st, piano(midi(n), 3.0, 0.32), t0, pan=0.25)
    # C: reveal - hening sejenak, lalu F major terang, pukulan "ARTA-C"
    place(st, pad([midi(n) for n in (41, 53, 57, 60, 67)], 7.0, att=3.0, rel=1.5, bright=5.0), 35.2, gain=0.65)
    place(st, pad([midi(n) for n in (46, 58, 62, 65, 72)], 3.5, att=0.05, rel=2.2, bright=6.0), 39.35, gain=0.7)
    for i, n in enumerate((65, 69, 72, 77, 81)):
        place(st, piano(midi(n), 4.0, 0.38), 39.4 + i * 0.09, pan=-0.4 + i * 0.2)
    # D: teknologi - arpeggio 8-an (100 bpm) F - C - Dm - Bb
    step = 0.3
    chords = [(53, 57, 60, 65), (48, 55, 60, 64), (50, 57, 62, 65), (46, 53, 58, 62)]
    t, ci = 41.5, 0
    while t < 67.8:
        ch = chords[(ci // 16) % 4]
        if ci % 16 == 0:
            place(st, pad([midi(ch[0] - 12)] + [midi(n) for n in ch[1:]], 16 * step + 0.4, att=0.6, rel=0.8, bright=3.0),
                  t, gain=0.42)
        n = ch[[0, 1, 2, 3, 2, 1, 3, 2][ci % 8]] + 12
        place(st, pluck(midi(n), 0.8, 0.26 if ci % 2 else 0.34), t, pan=0.35 if ci % 2 else -0.35)
        if ci % 4 == 0:
            place(st, thump(0.35, 70, 45, 0.28), t)
        t += step
        ci += 1
    # E: resolusi - Bb, F, C, F + melodi piano
    for ns, t0, d in [((46, 58, 62, 65), 68.0, 2.4), ((41, 57, 60, 65), 70.3, 2.4), ((48, 55, 60, 64), 72.6, 2.4),
                      ((41, 57, 60, 65, 69), 74.9, 3.4)]:
        place(st, pad([midi(n) for n in ns], d + 0.8, att=0.4, rel=0.9, bright=4.5), t0, gain=0.6)
    for t0, n in [(68.3, 77), (69.2, 74), (70.4, 72), (71.4, 77), (72.7, 76), (73.6, 72), (75.0, 77)]:
        place(st, piano(midi(n), 3.0, 0.36), t0, pan=0.2)
    # F: hitungan & penutup - motif kembali, akhir F(add9) terbuka
    place(st, pad([midi(n) for n in (41, 53, 60, 67)], 8.0, att=1.0, rel=1.5, bright=3.0), 77.2, gain=0.4)
    for t0, n in [(77.5, 69), (78.5, 65), (79.3, 64), (80.0, 62), (81.2, 65), (82.2, 67)]:
        place(st, piano(midi(n), 3.5, 0.36), t0)
    place(st, pad([midi(n) for n in (29, 41, 57, 60, 67, 72)], 6.0, att=0.03, rel=4.0, bright=5.0), 85.0, gain=0.75)
    for i, n in enumerate((53, 60, 65, 69, 72, 79)):
        place(st, piano(midi(n), 5.0, 0.4), 85.0 + i * 0.12, pan=-0.5 + i * 0.2)
    for t0 in SFX["hit"]:
        place(st, boom(0.85), t0)
    for a, b in SFX["riser"]:
        place(st, riser(b - a), a, gain=0.35)
    st = reverb(st, wet=0.34)
    st *= np.clip(1.0 - np.maximum(0, np.arange(N) / SR - 87.0) / 3.0, 0, 1)        # fade akhir
    return st


# ---------------------------------------------------------------- efek suara
def sfx():
    st = np.zeros((2, N))
    # pagi: ruang sunyi + burung jauh
    for a, b in SFX["birds"]:
        room = lp(np.cumsum(rng.standard_normal(int((b - a + 1) * SR))) * 0.002, 400)
        place(st, room * env(len(room), 1.0, 1.5) * 0.08, a)
        t = a + 0.4
        while t < b - 0.5:
            for k in range(rng.integers(2, 5)):
                d = rng.uniform(0.06, 0.12)
                tt = tvec(d)
                f = rng.uniform(2800, 3600) + 1400 * np.sin(np.pi * tt / d) * rng.uniform(0.5, 1.0)
                ch = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / d) ** 2
                place(st, ch, t + k * rng.uniform(0.11, 0.17), pan=rng.uniform(-0.8, -0.3), gain=0.03)
            t += rng.uniform(1.2, 2.4)
    # layar menyala
    for t0 in SFX["screen_on"]:
        for f, g in ((880, 0.12), (1320, 0.08), (1760, 0.04)):
            tt = tvec(1.2)
            place(st, np.sin(2 * np.pi * f * tt) * np.exp(-tt * 3.5) * env(len(tt), 0.03, 0.2), t0, gain=g)
    # alarm buzzer alat
    for t0 in SFX["alarm"]:
        for k in range(6):
            tt = tvec(0.09)
            b = np.sign(np.sin(2 * np.pi * 2700 * tt)) * 0.3 + np.sin(2 * np.pi * 2700 * tt)
            place(st, lp(b, 6000) * env(len(tt), 0.004, 0.01), t0 + k * 0.16 + (0.25 if k >= 3 else 0), gain=0.07)
    for t0 in SFX["face_ok"]:
        for i, f in enumerate((988, 1319)):
            tt = tvec(0.25)
            place(st, np.sin(2 * np.pi * f * tt) * np.exp(-tt * 14), t0 + i * 0.09, gain=0.1)
    for t0 in SFX["finger_in"]:
        n = bp(rng.standard_normal(int(1.6 * SR)), 300, 2500)
        place(st, n * np.sin(np.linspace(0, np.pi, len(n))) ** 2, t0, pan=-0.3, gain=0.05)
    for a, b in SFX["heart"]:
        t = a
        while t < b:
            place(st, thump(0.4, 58, 40, 0.32), t)
            place(st, thump(0.4, 54, 38, 0.2), t + 0.17)
            tt = tvec(0.08)
            place(st, np.sin(2 * np.pi * 1046 * tt) * np.exp(-tt * 40), t + 0.02, pan=0.3, gain=0.05)
            t += 60 / 78
    # servo: dengung motor + gerigi
    for a, b in SFX["servo"]:
        tt = tvec(b - a)
        f = 150 + 30 * np.sin(np.pi * tt / (b - a))
        ph = 2 * np.pi * np.cumsum(f) / SR
        m = sum(np.sin(k * ph) / k for k in range(1, 12))
        chatter = bp(rng.standard_normal(len(tt)), 1500, 4500) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 34 * tt)))
        x = (lp(m, 2500) * 0.6 + chatter * 0.35) * env(len(tt), 0.05, 0.08)
        place(st, x, a, pan=0.15, gain=0.09)
    for t0 in SFX["foil"]:
        n = int(0.16 * SR)
        x = np.zeros(n)
        for _ in range(40):
            i = rng.integers(0, n - 200)
            x[i:i + 120] += rng.standard_normal(120) * np.exp(-np.arange(120) / 25) * rng.uniform(0.3, 1)
        x = hp(x, 1800)
        x[:300] += np.sin(2 * np.pi * 420 * np.arange(300) / SR) * np.exp(-np.arange(300) / 60) * 2
        place(st, x, t0, gain=0.22)
    for t0 in SFX["land"]:
        for dt, g in ((0, 0.3), (0.085, 0.16), (0.14, 0.07)):
            tt = tvec(0.05)
            c = (np.sin(2 * np.pi * 2300 * tt) + 0.6 * np.sin(2 * np.pi * 3700 * tt)) * np.exp(-tt * 140)
            place(st, c, t0 + dt, pan=0.1, gain=g)
    for t0 in SFX["chime_done"]:
        for i, n in enumerate((84, 88, 91)):
            tt = tvec(1.6)
            f = midi(n)
            bell = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 2.76 * tt) * np.exp(-tt * 6)) * np.exp(-tt * 2.6)
            place(st, bell * env(len(tt), 0.003, 0.3), t0 + i * 0.11, pan=-0.2 + i * 0.2, gain=0.09)
    for t0 in SFX["phone_ping"]:
        for i, f in enumerate((1568, 2093)):
            tt = tvec(0.7)
            place(st, np.sin(2 * np.pi * f * tt) * np.exp(-tt * 7), t0 + i * 0.12, pan=0.6, gain=0.08)
    for a, b in SFX["ticks"]:
        t, k = a, 0
        while t < b:
            tt = tvec(0.02)
            place(st, hp(rng.standard_normal(len(tt)), 3000) * np.exp(-tt * 300), t, gain=0.12)
            t += max(0.05, 0.25 * 0.9 ** k)
            k += 1
    return reverb(st, secs=1.4, decay=0.4, wet=0.15)


# ---------------------------------------------------------------- narasi
def load_mp3(p):
    raw = subprocess.run([ffbin("ffmpeg"), "-v", "error", "-i", p, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def vo_track():
    meta = json.load(open(os.path.join(AUD, "vo.json")))
    st = np.zeros((2, N))
    for m in meta:
        x = load_mp3(os.path.join(AUD, f"vo_{m['id']}.mp3"))
        x = hp(x, 80)
        x = x / (np.max(np.abs(x)) + 1e-9) * 0.7
        place(st, x, VO_START[m["id"]])
    return reverb(st, secs=0.8, decay=0.25, wet=0.06)


def write_wav(p, st):
    st = np.clip(st, -1, 1)
    data = (st.T * 32767).astype("<i2").tobytes()
    with wave.open(p, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data)


def main():
    mu, fx, vo = music(), sfx(), vo_track()
    # ducking musik di bawah narasi (-7 dB, attack 60 ms, release 450 ms)
    lvl = np.abs(vo).max(axis=0)
    k = int(0.03 * SR)
    lvl = np.convolve(lvl, np.ones(k) / k, mode="same")
    gate = (lvl > 0.02).astype(float)
    a, r = np.exp(-1 / (0.06 * SR)), np.exp(-1 / (0.45 * SR))
    g = np.zeros(N)
    from scipy.signal import lfilter
    g = lfilter([1 - r], [1, -r], gate)                      # pelepasan halus
    g = np.maximum(g, lfilter([1 - a], [1, -a], gate))
    duck = 1 - 0.55 * np.clip(g, 0, 1)
    mu *= 0.5 / (np.max(np.abs(mu)) + 1e-9)
    fx *= 1.0
    mix = mu * duck + fx + vo
    mix *= 0.89 / np.max(np.abs(mix))
    for n_, x in (("music", mu), ("sfx", fx), ("vo_track", vo), ("mix_raw", mix)):
        write_wav(os.path.join(AUD, f"{n_}.wav"), x)
    # loudnorm dua lintasan ke -17 LUFS
    ff = ffbin("ffmpeg")
    src = os.path.join(AUD, "mix_raw.wav")
    r1 = subprocess.run([ff, "-hide_banner", "-i", src, "-af", "loudnorm=I=-17:TP=-1.5:LRA=11:print_format=json",
                         "-f", "null", "-"], capture_output=True, text=True).stderr
    js = json.loads(r1[r1.rindex("{"):r1.rindex("}") + 1])
    af = (f"loudnorm=I=-17:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
          f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    subprocess.run([ff, "-y", "-v", "error", "-i", src, "-af", af, "-ar", str(SR), os.path.join(AUD, "mix.wav")], check=True)
    print("audio selesai; input", js["input_i"], "LUFS ->", "-17")


if __name__ == "__main__":
    main()
