/* Verifies the finished videos: format, motion, captions, and that the
   content visibly scrolls inside the screen during every beat. */
import { spawnSync } from "node:child_process";

const BEAT_SEC = 5.0, BEATS = 6, FPS = 30;
let bad = 0;
const note = (ok, m) => { console.log(`${ok ? "ok  " : "FAIL"} ${m}`); if (!ok) bad++; };

function gray(file, n, at, crop) {
  const args = ["-v", "error"];
  if (at !== undefined) args.push("-ss", String(at));
  args.push("-i", file, "-vf", [crop, `scale=${n}:${n}`, "format=gray"].filter(Boolean).join(","),
    "-frames:v", "1", "-f", "rawvideo", "-");
  const r = spawnSync("ffmpeg", args, { maxBuffer: 1 << 22 });
  return r.stdout?.length ? [...r.stdout] : null;
}
const diff = (a, b) => a.reduce((s, v, i) => s + Math.abs(v - b[i]), 0) / a.length;

for (const label of ["Neumorph", "Glass"]) {
  const vid = `video/ARTA-C-3D-Scroll-${label}-1080x1920.mp4`;
  console.log(`\n--- ${label} ---`);

  const meta = JSON.parse(spawnSync("ffprobe", ["-v", "error", "-select_streams", "v:0",
    "-show_entries", "stream=width,height,nb_read_frames:format=duration",
    "-count_frames", "-of", "json", vid], { encoding: "utf8" }).stdout);
  const s = meta.streams[0];
  note(s.width === 1080 && s.height === 1920, `${label}: 1080x1920 (${s.width}x${s.height})`);
  note(Number(s.nb_read_frames) === BEATS * BEAT_SEC * FPS,
    `${label}: ${BEATS * BEAT_SEC * FPS} frames (${s.nb_read_frames})`);
  note(Math.abs(Number(meta.format.duration) - 30) < 0.5,
    `${label}: ~30s (${Number(meta.format.duration).toFixed(1)}s)`);

  const dec = spawnSync("ffmpeg", ["-v", "error", "-i", vid, "-f", "null", "-"], { encoding: "utf8" });
  note(!dec.stderr.trim(), `${label}: decodes clean`);

  /* Scroll happens mid-beat (the curve holds at each end), so sample the
     middle stretch. Crop to the centre of the frame, which is where the
     handset screen sits in these restrained poses. */
  const CENTRE = "crop=420:760:330:520";
  let scrolled = 0;
  for (let b = 0; b < BEATS; b++) {
    const t0 = b * BEAT_SEC + 1.4;
    const t1 = b * BEAT_SEC + 3.4;
    const a = gray(vid, 28, t0, CENTRE);
    const c = gray(vid, 28, t1, CENTRE);
    const d = diff(a, c);
    if (d > 6) scrolled++;
    console.log(`   beat ${b + 1}: screen delta ${d.toFixed(1)} ${d > 6 ? "" : "(little movement)"}`);
  }
  note(scrolled >= 4, `${label}: content scrolls in at least 4 of 6 beats (${scrolled}/6)`);

  /* caption card composited */
  const CAP = "crop=1080:430:0:1330";
  const withCard = gray(vid, 20, 2.5, CAP);
  const noCard = gray(vid, 20, 0.03, CAP);
  note(diff(withCard, noCard) > 12,
    `${label}: caption card composited (delta ${diff(withCard, noCard).toFixed(1)})`);

  /* camera still moves */
  const m = [0.3, 1.2, 2.5, 3.8, 4.7].map((t) => gray(vid, 24, t));
  const peak = Math.max(...m.slice(1).map((g, i) => diff(g, m[i])));
  note(peak > 1.5, `${label}: camera moves (peak frame delta ${peak.toFixed(2)})`);
}

console.log(bad ? `\n${bad} check(s) failed.` : "\nScrolling 3D videos verified.");
process.exit(bad ? 1 : 0);
