/* ============================================================
   ARTA-C — render the vertical showcase video.

   Why not `capcut render --burn-captions`? That path relies on
   ffmpeg's drawtext resolving a font through fontconfig, and this
   machine's ffmpeg build crashes (access violation) when it does.
   Captions are instead pre-rendered to transparent PNG overlays
   and composited, which avoids drawtext entirely and gives us
   full control over typography.
   ============================================================ */
import { readFile, writeFile, mkdir, rm } from "node:fs/promises";
import { spawn } from "node:child_process";
import { resolve, basename } from "node:path";

const THEME = process.argv[2] === "glass" ? "glass" : "neu";
const SPEC = `tools/artac-${THEME}.json`;
const WORK = `tools/work-${THEME}`;
const OUT = `video/ARTA-C-${THEME === "glass" ? "Glass" : "Neumorph"}-1080x1920.mp4`;

const W = 1080, H = 1920, FPS = 30;
const XFADE = 0.45;

const spec = JSON.parse(await readFile(SPEC, "utf8"));
const shots = spec.tracks.find((t) => t.type === "video").items;
const caps = spec.tracks.find((t) => t.type === "text").items;

await rm(WORK, { recursive: true, force: true });
await mkdir(WORK, { recursive: true });
await mkdir("video", { recursive: true });

const run = (cmd, args) =>
  new Promise((ok, no) => {
    const p = spawn(cmd, args, { stdio: ["ignore", "ignore", "pipe"] });
    let err = "";
    p.stderr.on("data", (d) => { err += d; });
    p.on("close", (code) => (code === 0 ? ok() : no(new Error(`${cmd} exit ${code}\n${err.slice(-1500)}`))));
  });

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

/* ---------- caption overlays as SVG -> PNG ----------
   Rendered by the browser (already a dependency for the
   screenshots), so typography matches the app exactly. */
const { chromium } = await import("playwright");
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });

const overlays = [];
for (let i = 0; i < caps.length; i++) {
  const lines = String(caps[i].text).split("\n");
  const file = resolve(WORK, `cap${String(i).padStart(2, "0")}.png`);

  // caption card pinned to the lower third
  const html = `<!DOCTYPE html><html><head><meta charset="utf-8">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;800&display=swap" rel="stylesheet">
  <style>
    html,body{margin:0;width:${W}px;height:${H}px;background:transparent;overflow:hidden}
    .wrap{position:absolute;left:0;right:0;bottom:150px;display:flex;justify-content:center}
    .card{
      max-width:${Math.round(W * 0.84)}px;
      padding:34px 46px;border-radius:34px;
      background:rgba(6,32,41,.82);
      border:2px solid rgba(103,232,249,.45);
      box-shadow:0 24px 70px rgba(0,0,0,.5);
      font-family:'Plus Jakarta Sans',sans-serif;color:#fff;text-align:center;
    }
    .l0{font-size:60px;font-weight:800;letter-spacing:-.02em;line-height:1.18;
        background:linear-gradient(90deg,#a5f3fc,#ffffff);-webkit-background-clip:text;
        -webkit-text-fill-color:transparent}
    .ln{font-size:42px;font-weight:600;line-height:1.3;color:#dff6fd;margin-top:8px}
  </style></head><body>
    <div class="wrap"><div class="card">
      ${lines.map((l, k) => `<div class="${k === 0 ? "l0" : "ln"}">${esc(l)}</div>`).join("")}
    </div></div>
  </body></html>`;

  await page.setContent(html, { waitUntil: "networkidle" });
  await page.waitForTimeout(220);
  await page.screenshot({ path: file, omitBackground: true });
  overlays.push(file);
}
await browser.close();
console.log(`caption overlays: ${overlays.length}`);

/* ---------- per-shot clips: Ken Burns + caption ---------- */
const clips = [];
for (let i = 0; i < shots.length; i++) {
  const dur = shots[i].duration;
  const clip = resolve(WORK, `clip${String(i).padStart(2, "0")}.mp4`);
  const frames = Math.round(dur * FPS);

  // slow zoom, alternating direction so consecutive shots differ
  const zStart = i % 2 === 0 ? 1.0 : 1.06;
  const zEnd = i % 2 === 0 ? 1.06 : 1.0;
  const zoom = `${zStart}+(${(zEnd - zStart).toFixed(4)})*on/${frames}`;

  const filter = [
    `[0:v]scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},`,
    `zoompan=z='${zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=${W}x${H}:fps=${FPS},`,
    `trim=duration=${dur},setpts=PTS-STARTPTS[bg];`,
    `[1:v]format=rgba,fade=t=in:st=0.25:d=0.35:alpha=1,`,
    `fade=t=out:st=${(dur - 0.5).toFixed(2)}:d=0.35:alpha=1[cap];`,
    `[bg][cap]overlay=0:0:format=auto,format=yuv420p[v]`,
  ].join("");

  await run("ffmpeg", [
    "-v", "error", "-y",
    "-loop", "1", "-t", String(dur), "-i", shots[i].path,
    "-loop", "1", "-t", String(dur), "-i", overlays[i],
    "-filter_complex", filter, "-map", "[v]",
    "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-pix_fmt", "yuv420p", "-r", String(FPS), clip,
  ]);
  clips.push(clip);
  process.stdout.write(`\r  clips: ${i + 1}/${shots.length}`);
}
console.log();

/* ---------- crossfade the clips together ---------- */
const inputs = clips.flatMap((c) => ["-i", c]);
let fc = "";
let prev = "0:v";
let acc = shots[0].duration;
for (let i = 1; i < clips.length; i++) {
  const out = i === clips.length - 1 ? "vout" : `x${i}`;
  const offset = (acc - XFADE).toFixed(3);
  fc += `[${prev}][${i}:v]xfade=transition=fade:duration=${XFADE}:offset=${offset}[${out}];`;
  prev = out;
  acc += shots[i].duration - XFADE;
}
fc = fc.replace(/;$/, "");

const total = acc;
console.log(`stitching ${clips.length} clips -> ${total.toFixed(1)}s`);

await run("ffmpeg", [
  "-v", "error", "-y", ...inputs,
  "-filter_complex", fc, "-map", clips.length > 1 ? "[vout]" : "0:v",
  "-c:v", "libx264", "-preset", "slow", "-crf", "20",
  "-pix_fmt", "yuv420p", "-r", String(FPS),
  "-movflags", "+faststart", OUT,
]);

await writeFile(
  `${WORK}/manifest.json`,
  JSON.stringify({ theme: THEME, clips: clips.map((c) => basename(c)), seconds: total }, null, 2)
);
console.log(`done: ${OUT}`);
