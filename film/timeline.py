"""Lini waktu film "Day 47" (detik). Dipakai bersama oleh audio.py dan edit.py."""

DUR = 90.0
FPS = 24

# segmen gambar: (mulai, selesai, sumber) - sumber 3D = nama shot film.py, 2D = digambar edit.py
SEGMENTS = [
    (0.0, 8.5, "3d:dawn"),
    (8.5, 17.0, "2d:days"),
    (17.0, 24.0, "2d:slip"),
    (24.0, 35.0, "2d:pmo"),
    (35.0, 41.5, "3d:reveal"),
    (41.5, 46.0, "3d:face"),
    (46.0, 52.5, "3d:ppg"),
    (52.5, 59.5, "3d:inside"),
    (59.5, 68.0, "3d:peck"),
    (68.0, 77.0, "3d:notify"),
    (77.0, 82.5, "2d:count"),
    (82.5, 90.0, "3d:end"),
]
# transisi lewat hitam (detik batas, durasi total)
DIPS = {8.5: 0.5, 35.0: 0.7, 77.0: 0.5, 82.5: 0.6}

# mulai tiap baris narasi (id di audio/vo.json)
VO_START = {"01": 1.2, "02": 4.6, "03": 9.0, "04": 17.3, "05": 24.3, "06": 35.4, "07": 39.4, "08": 42.0,
            "09": 46.8, "10": 52.8, "11": 59.9, "12": 68.6, "13": 77.6, "14": 85.0}

# efek suara (detik global) - sinkron dengan state() di film.py
SFX = {
    "birds": [(0.0, 8.5)],
    "screen_on": [38.4],
    "alarm": [41.6],
    "face_ok": [43.3],
    "finger_in": [46.4],
    "heart": [(49.0, 52.4)],
    "servo": [(53.9, 54.8), (55.4, 56.3), (56.8, 57.7), (57.5, 59.1), (60.1, 61.9), (64.1, 65.1)],
    "foil": [61.85],
    "land": [64.14],
    "chime_done": [68.5],
    "phone_ping": [70.2],
    "ticks": [(77.4, 80.2)],
    "hit": [39.35, 85.0],
    "riser": [(32.6, 35.0)],
}
