"""Naskah narasi film dokumenter ARTA-C "Day 47" (English) + pembuat audio TTS per baris.

  python naskah.py   ->  audio/vo_XX.mp3 + audio/vo.json (durasi tiap baris)
"""
import json
import os
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
VOICE, RATE = "en-US-ChristopherNeural", "-8%"

# (id, shot, kalimat) - shot = adegan tempat kalimat diucapkan
LINES = [
    ("01", "dawn", "Tuberculosis is curable."),
    ("02", "dawn", "But only if you finish the treatment."),
    ("03", "days", "Six months. One hundred and eighty mornings. Every single dose."),
    ("04", "slip", "Patients often feel better within weeks, and that is when doses start to slip."),
    ("05", "pmo", "In Indonesia, every patient has a treatment supervisor, a P.M.O. But no supervisor can be there every morning."),
    ("06", "reveal", "So we built a companion that is."),
    ("07", "reveal", "ARTA-C."),
    ("08", "face", "It knows who is taking the medicine."),
    ("09", "ppg", "It reads the pulse and oxygen level through a light-sealed finger sensor."),
    ("10", "inside", "Inside, the original blister moves down, row by row, like bread in a toaster."),
    ("11", "peck", "A small plunger presses one caplet through the foil. Never more. Never less."),
    ("12", "notify", "Seconds later, the supervisor knows. Dose taken. Verified."),
    ("13", "end", "Day forty-seven. One hundred and thirty-three to go."),
    ("14", "end", "No dose goes unseen."),
]


def ffbin(name):
    import glob
    import shutil
    hit = shutil.which(name) or glob.glob(os.path.expandvars(
        rf"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\*\bin\{name}.exe"))
    return hit if isinstance(hit, str) else hit[0]


def dur(path):
    out = subprocess.run([ffbin("ffprobe"),"-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.strip()
    return float(out)


def main():
    os.makedirs(os.path.join(HERE, "audio"), exist_ok=True)
    meta = []
    for i, shot, text in LINES:
        p = os.path.join(HERE, "audio", f"vo_{i}.mp3")
        for attempt in range(4):
            if os.path.exists(p) and os.path.getsize(p) > 1000:
                break
            r = subprocess.run(["python", "-m", "edge_tts", "--voice", VOICE, f"--rate={RATE}", "--text", text,
                                "--write-media", p], capture_output=True, text=True)
            if r.returncode:
                print("  coba ulang", i, r.stderr.strip().splitlines()[-1:])
                time.sleep(3 * (attempt + 1))
        else:
            raise SystemExit(f"TTS gagal untuk baris {i}")
        meta.append(dict(id=i, shot=shot, text=text, dur=round(dur(p), 2)))
        print(i, meta[-1]["dur"], text)
    json.dump(meta, open(os.path.join(HERE, "audio", "vo.json"), "w"), indent=1)
    print("total suara:", round(sum(m["dur"] for m in meta), 1), "detik")


if __name__ == "__main__":
    main()
