/* ============================================================
   ARTA-C — 3D showcase video renderer
   Drives tools/scene3d.html frame by frame through Playwright,
   pipes the PNG frames straight into ffmpeg, and overlays a
   caption card per beat. Deterministic: frame N always renders
   the same pose, independent of machine speed.
   ============================================================ */
import { chromium } from "playwright";
import { spawn } from "node:child_process";
import { mkdir, rm, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const THEME = process.argv[2] === "glass" ? "glass" : "neu";
const LABEL = THEME === "glass" ? "Glass" : "Neumorph";
const OUT = `video/ARTA-C-3D-${LABEL}-1080x1920.mp4`;
const WORK = `tools/work3d-${THEME}`;

const W = 1080, H = 1920, FPS = 30;
const BEAT_SEC = 4.0;                 // seconds per page
const BEAT_FRAMES = BEAT_SEC * FPS;

/* The six pages that carry the product story. */
const BEATS = [
  { f: "app-dokter-01-ringkasan.png", t: "Dasbor Ringkasan",
    d: "Kepatuhan, dosis berikutnya,\ndan sisa obat dalam satu layar" },
  { f: "app-dokter-03-jadwal.png", t: "Jadwal Dosis",
    d: "Dokter menetapkan dosis,\ntersinkron ke dispenser" },
  { f: "app-dokter-04-perangkat.png", t: "Kotak Obat IoT",
    d: "Telemetri suhu, baterai,\nsensor gerak saat ambil obat" },
  { f: "app-dokter-05-peringatan.png", t: "Alarm Eskalasi",
    d: "Kotak, pasien, PMO, dokter\nbertingkat lima tahap" },
  { f: "app-pasien-05-vot.png", t: "Video Observed Therapy",
    d: "Bukti obat benar diminum,\nditinjau PMO dan dokter" },
  { f: "app-dokter-09-laporan.png", t: "Laporan Evaluasi",
    d: "Rekap kepatuhan dan\nkesimpulan otomatis" },
];

await rm(WORK, { recursive: true, force: true });
await mkdir(WORK, { recursive: true });
await mkdir("video", { recursive: true });

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

/* ---------- caption overlays (transparent PNG) ----------
   Pre-rendered rather than drawn with ffmpeg's drawtext, which
   crashes on this machine's ffmpeg build (fontconfig fault). */
const browser = await chromium.launch({
  args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
});

const capPage = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
const overlays = [];
for (let i = 0; i < BEATS.length; i++) {
  const b = BEATS[i];
  const file = resolve(WORK, `cap${i}.png`);
  const dark = THEME === "glass";
  await capPage.setContent(`<!DOCTYPE html><html><head><meta charset="utf-8">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;800&display=swap" rel="stylesheet">
    <style>
      html,body{margin:0;width:${W}px;height:${H}px;background:transparent;overflow:hidden}
      .top{position:absolute;top:118px;left:0;right:0;text-align:center;
           font-family:'Plus Jakarta Sans',sans-serif}
      .kicker{display:inline-flex;align-items:center;gap:12px;
           padding:14px 34px;border-radius:999px;font-size:30px;font-weight:800;
           background:${dark ? "rgba(103,232,249,.16)" : "rgba(6,182,212,.14)"};
           color:${dark ? "#a5f3fc" : "#0e7490"};
           border:2px solid ${dark ? "rgba(103,232,249,.4)" : "rgba(6,182,212,.3)"}}
      .dot{width:14px;height:14px;border-radius:50%;background:#10b981}
      .bot{position:absolute;bottom:132px;left:0;right:0;display:flex;justify-content:center;
           font-family:'Plus Jakarta Sans',sans-serif}
      /* The light theme's backdrop is already near-white, so a white card
         would vanish into it. Use a deep cyan card in both themes and keep
         the text light: that reads cleanly over either background. */
      .card{max-width:${Math.round(W * 0.82)}px;padding:36px 52px;border-radius:36px;text-align:center;
           background:${dark ? "rgba(4,26,34,.86)" : "rgba(12,62,78,.93)"};
           border:2px solid ${dark ? "rgba(103,232,249,.45)" : "rgba(103,232,249,.55)"};
           box-shadow:0 26px 70px rgba(2,20,26,${dark ? ".55" : ".38"})}
      .t{font-size:62px;font-weight:800;letter-spacing:-.02em;line-height:1.15;
           background:linear-gradient(90deg,#a5f3fc,#ffffff);
           -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
      .d{margin-top:12px;font-size:38px;font-weight:600;line-height:1.34;
           color:#d4f1fa;white-space:pre-line}
      .step{margin-top:20px;font-size:26px;font-weight:700;letter-spacing:.16em;
           color:#8cc4d4}
    </style></head><body>
      <div class="top"><span class="kicker"><span class="dot"></span>ARTA-C · Aplikasi PMO TBC</span></div>
      <div class="bot"><div class="card">
        <div class="t">${esc(b.t)}</div>
        <div class="d">${esc(b.d)}</div>
        <div class="step">${i + 1} / ${BEATS.length}</div>
      </div></div>
    </body></html>`, { waitUntil: "networkidle" });
  await capPage.waitForTimeout(240);
  await capPage.screenshot({ path: file, omitBackground: true });
  overlays.push(file);
}
await capPage.close();
console.log(`caption overlays: ${overlays.length}`);

/* ---------- 3D scene ---------- */
// ES module imports and texture loads are blocked under file://, so the
// scene is served over local HTTP.
const { startServer } = await import("./httpserve.mjs");
const server = await startServer(5178);

const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
const errs = [];
page.on("pageerror", (e) => errs.push(String(e).slice(0, 200)));
page.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 200)); });

await page.goto("http://127.0.0.1:5178/tools/scene3d.html", { waitUntil: "load" });
await page.waitForFunction(() => window.__sceneLoaded === true, { timeout: 30000 });
await page.evaluate((t) => window.ARTAC.init(t), THEME);

const info = await page.evaluate(() => window.ARTAC.info());
console.log(`scene: webgl=${info.webgl} shadows=${info.shadows} objects=${info.objects}`);
if (!info.webgl) throw new Error("WebGL unavailable in the render browser");

/* ---------- render every frame straight into ffmpeg ---------- */
const totalFrames = BEATS.length * BEAT_FRAMES;
const raw = resolve(WORK, "scene.mp4");

const ff = spawn("ffmpeg", [
  "-v", "error", "-y",
  "-f", "image2pipe", "-framerate", String(FPS), "-i", "-",
  "-c:v", "libx264", "-preset", "medium", "-crf", "18",
  "-pix_fmt", "yuv420p", raw,
], { stdio: ["pipe", "ignore", "pipe"] });
let ffErr = "";
ff.stderr.on("data", (d) => { ffErr += d; });

const ffDone = new Promise((ok, no) => {
  ff.on("close", (c) => (c === 0 ? ok() : no(new Error(`ffmpeg pipe exit ${c}\n${ffErr.slice(-1200)}`))));
});

const write = (buf) =>
  ff.stdin.write(buf) ? Promise.resolve() : new Promise((r) => ff.stdin.once("drain", r));

for (let beat = 0; beat < BEATS.length; beat++) {
  const src = `http://127.0.0.1:5178/shots/${THEME}/${BEATS[beat].f}`;
  await page.evaluate((s) => window.ARTAC.setScreen(s), src);

  for (let f = 0; f < BEAT_FRAMES; f++) {
    const p = f / (BEAT_FRAMES - 1);
    await page.evaluate(([b, pp]) => window.ARTAC.applyPose(b, pp), [beat, p]);
    const shot = await page.screenshot({ type: "png" });
    await write(shot);
  }
  process.stdout.write(`\r  beats: ${beat + 1}/${BEATS.length}`);
}
console.log();

ff.stdin.end();
await ffDone;
if (errs.length) console.log("scene warnings:", errs.slice(0, 4));

/* ---------- composite caption overlays over the 3D footage ---------- */
const run = (args) =>
  new Promise((ok, no) => {
    const p = spawn("ffmpeg", args, { stdio: ["ignore", "ignore", "pipe"] });
    let e = "";
    p.stderr.on("data", (d) => { e += d; });
    p.on("close", (c) => (c === 0 ? ok() : no(new Error(`ffmpeg exit ${c}\n${e.slice(-1500)}`))));
  });

const inputs = ["-i", raw];
overlays.forEach((o) => inputs.push("-loop", "1", "-t", String(BEAT_SEC), "-i", o));

let fc = "";
let prev = "0:v";
overlays.forEach((_, i) => {
  const from = i * BEAT_SEC, to = from + BEAT_SEC;
  const lbl = i === overlays.length - 1 ? "vout" : `o${i}`;
  fc += `[${i + 1}:v]format=rgba,fade=t=in:st=0:d=0.4:alpha=1,` +
        `fade=t=out:st=${(BEAT_SEC - 0.45).toFixed(2)}:d=0.4:alpha=1,` +
        `setpts=PTS-STARTPTS+${from}/TB[c${i}];` +
        `[${prev}][c${i}]overlay=0:0:enable='between(t,${from},${to})':format=auto[${lbl}];`;
  prev = lbl;
});
fc = fc.replace(/;$/, "");

console.log("compositing captions…");
await run([
  "-v", "error", "-y", ...inputs,
  "-filter_complex", fc, "-map", "[vout]",
  "-c:v", "libx264", "-preset", "slow", "-crf", "19",
  "-pix_fmt", "yuv420p", "-r", String(FPS),
  "-movflags", "+faststart", OUT,
]);

await writeFile(`${WORK}/manifest.json`, JSON.stringify({
  theme: THEME, beats: BEATS.map((b) => b.f), frames: totalFrames, seconds: totalFrames / FPS,
}, null, 2));

await browser.close();
server.close();
console.log(`done: ${OUT} (${(totalFrames / FPS).toFixed(1)}s, ${totalFrames} frames)`);
