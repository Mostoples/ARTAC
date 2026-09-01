/* Verifies the 3D showcase videos: continuous motion (not a slideshow),
   caption band present, and each beat showing its intended screenshot. */
import { spawnSync } from "node:child_process";

let bad = 0;
const note = (ok, m) => { console.log(`${ok ? "ok  " : "FAIL"} ${m}`); if (!ok) bad++; };

function gray(file, n, at, crop) {
  const args = ["-v", "error"];
  if (at !== undefined) args.push("-ss", String(at));
  args.push("-i", file, "-vf", [crop, `scale=${n}:${n}`, "format=gray"].filter(Boolean).join(","),
    "-frames:v", "1", "-f", "rawvideo", "-");
  const r = spawnSync("ffmpeg", args, { encoding: "buffer", maxBuffer: 1 << 22 });
  return r.stdout && r.stdout.length ? [...r.stdout] : null;
}

const corr = (a, b) => {
  const n = a.length;
  const ma = a.reduce((s, v) => s + v, 0) / n, mb = b.reduce((s, v) => s + v, 0) / n;
  let num = 0, da = 0, db = 0;
  for (let i = 0; i < n; i++) { const x = a[i] - ma, y = b[i] - mb; num += x * y; da += x * x; db += y * y; }
  return da && db ? num / Math.sqrt(da * db) : 0;
};
const diff = (a, b) => a.reduce((s, v, i) => s + Math.abs(v - b[i]), 0) / a.length;

const BEATS = [
  "app-dokter-01-ringkasan.png", "app-dokter-03-jadwal.png",
  "app-dokter-04-perangkat.png", "app-dokter-05-peringatan.png",
  "app-pasien-05-vot.png", "app-dokter-09-laporan.png",
];
const BEAT_SEC = 4.0;

for (const [theme, label] of [["neu", "Neumorph"], ["glass", "Glass"]]) {
  const vid = `video/ARTA-C-3D-${label}-1080x1920.mp4`;
  console.log(`\n--- ${label} ---`);

  const meta = spawnSync("ffprobe", ["-v", "error", "-select_streams", "v:0",
    "-show_entries", "stream=width,height,nb_read_frames,codec_name:format=duration",
    "-count_frames", "-of", "json", vid], { encoding: "utf8" });
  const j = JSON.parse(meta.stdout);
  const s = j.streams[0];
  note(s.width === 1080 && s.height === 1920, `${label}: 1080x1920 portrait (${s.width}x${s.height})`);
  note(Number(s.nb_read_frames) === 720, `${label}: 720 frames (${s.nb_read_frames})`);
  note(Math.abs(Number(j.format.duration) - 24) < 0.5, `${label}: ~24s (${Number(j.format.duration).toFixed(1)}s)`);

  const dec = spawnSync("ffmpeg", ["-v", "error", "-i", vid, "-f", "null", "-"], { encoding: "utf8" });
  note(!dec.stderr.trim(), `${label}: decodes clean`);

  /* Motion: the camera eases in and out, so it is nearly still at the
     start and end of a beat. Sample across the whole beat and require
     that the busiest stretch shows clear movement. */
  const times = [0.2, 0.6, 1.0, 1.4, 1.8, 2.2, 2.6, 3.0, 3.4, 3.8];
  const seq = times.map((t) => gray(vid, 24, t));
  const deltas = [];
  for (let i = 1; i < seq.length; i++) deltas.push(diff(seq[i], seq[i - 1]));
  const peak = Math.max(...deltas);
  const moved = deltas.filter((d) => d > 0.8).length;
  note(peak > 1.8 && moved >= 5,
    `${label}: camera moves within a beat (peak delta ${peak.toFixed(2)}, ${moved}/9 samples moving)`);

  /* Across beats the whole composition should change too. */
  const acrossBeats = diff(gray(vid, 24, 2.0), gray(vid, 24, 6.0));
  note(acrossBeats > 3, `${label}: composition changes between beats (delta ${acrossBeats.toFixed(2)})`);

  /* Caption card: compare mid-beat (card fully faded in) against the very
     start of the beat, where the card is still transparent. Same crop, so
     any difference is the overlay itself. */
  const CAP_CROP = "crop=1080:430:0:1340";
  const withCard = gray(vid, 20, 2.0, CAP_CROP);
  const noCard = gray(vid, 20, 0.03, CAP_CROP);
  note(withCard && noCard, `${label}: caption bands readable`);
  const capDelta = diff(withCard, noCard);
  const mean = (a) => a.reduce((x, y) => x + y, 0) / a.length;
  note(capDelta > 12,
    `${label}: caption card composited (delta ${capDelta.toFixed(1)}; ${mean(noCard).toFixed(0)} -> ${mean(withCard).toFixed(0)})`);

  /* Which page each beat shows is checked by tools/verify-beats.mjs, which
     re-renders the pose so the comparison uses the same projection. A flat
     screenshot cannot be correlated against a perspective-warped one. */
  void corr; void theme; void BEATS; void BEAT_SEC;
}

console.log(bad ? `\n${bad} check(s) failed.` : "\n3D videos verified.");
process.exit(bad ? 1 : 0);
