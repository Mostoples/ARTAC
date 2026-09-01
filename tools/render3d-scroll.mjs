/* ============================================================
   ARTA-C — 3D showcase with in-screen scrolling
   The phone is real Three.js geometry; each beat pans the tall
   full-page capture vertically inside the display by animating
   the texture's UV offset, so the app appears to scroll.
   Frames are driven deterministically from Playwright.
   ============================================================ */
import { chromium } from "playwright";
import { spawn } from "node:child_process";
import { mkdir, rm, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const THEME = process.argv[2] === "glass" ? "glass" : "neu";
const LABEL = THEME === "glass" ? "Glass" : "Neumorph";
const OUT = `video/ARTA-C-3D-Scroll-${LABEL}-1080x1920.mp4`;
const WORK = `tools/wscroll-${THEME}`;
const PORT = 5182;

const W = 1080, H = 1920, FPS = 30;
const BEAT_SEC = 5.0;                     // longer beats: the scroll needs room
const BEAT_FRAMES = Math.round(BEAT_SEC * FPS);

const BEATS = [
  { f: "01-ringkasan.png", t: "Dasbor Ringkasan",
    d: "Kepatuhan, dosis berikutnya,\nsisa obat, dan kondisi kotak" },
  { f: "02-pasien.png", t: "Daftar Pasien",
    d: "Kohort pasien dengan kepatuhan\nper orang dan status kotak" },
  { f: "03-jadwal.png", t: "Jadwal & Ceklist Dosis",
    d: "Dokter menetapkan dosis,\ntersinkron ke dispenser" },
  { f: "04-perangkat.png", t: "Kotak Obat IoT",
    d: "Suhu, baterai, sisa obat,\ndan sensor gerak" },
  { f: "05-peringatan.png", t: "Alarm Eskalasi",
    d: "Kotak, pasien, PMO, dokter\nbertingkat lima tahap" },
  { f: "06-laporan.png", t: "Laporan Evaluasi",
    d: "Rekap kepatuhan dan\nkesimpulan otomatis" },
];

await rm(WORK, { recursive: true, force: true });
await mkdir(WORK, { recursive: true });
await mkdir("video", { recursive: true });

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

/* Scroll curve: hold at the top so the viewer reads the header, scroll
   through the body, then hold at the bottom before the cut. */
function scrollAt(p) {
  const HOLD_IN = 0.18, HOLD_OUT = 0.14;
  if (p <= HOLD_IN) return 0;
  if (p >= 1 - HOLD_OUT) return 1;
  const t = (p - HOLD_IN) / (1 - HOLD_IN - HOLD_OUT);
  // ease in and out so the scroll starts and stops smoothly
  return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
}

const { startServer } = await import("./httpserve.mjs");
const server = await startServer(PORT);

const browser = await chromium.launch({
  args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
});

/* ---------- caption overlays ---------- */
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
      .top{position:absolute;top:104px;left:0;right:0;text-align:center;
           font-family:'Plus Jakarta Sans',sans-serif}
      .kicker{display:inline-flex;align-items:center;gap:12px;padding:14px 34px;border-radius:999px;
           font-size:29px;font-weight:800;
           background:${dark ? "rgba(103,232,249,.16)" : "rgba(12,62,78,.9)"};
           color:${dark ? "#a5f3fc" : "#d4f1fa"};
           border:2px solid rgba(103,232,249,.45)}
      .dot{width:14px;height:14px;border-radius:50%;background:#10b981}
      .bot{position:absolute;bottom:118px;left:0;right:0;display:flex;justify-content:center;
           font-family:'Plus Jakarta Sans',sans-serif}
      /* deep cyan card in both themes: a white card would vanish into the
         light theme's near-white backdrop */
      .card{max-width:${Math.round(W * 0.82)}px;padding:34px 50px;border-radius:36px;text-align:center;
           background:${dark ? "rgba(4,26,34,.86)" : "rgba(12,62,78,.93)"};
           border:2px solid rgba(103,232,249,.5);
           box-shadow:0 26px 70px rgba(2,20,26,${dark ? ".55" : ".38"})}
      .t{font-size:58px;font-weight:800;letter-spacing:-.02em;line-height:1.16;
           background:linear-gradient(90deg,#a5f3fc,#ffffff);
           -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
      .d{margin-top:12px;font-size:36px;font-weight:600;line-height:1.34;
           color:#d4f1fa;white-space:pre-line}
      .step{margin-top:18px;font-size:25px;font-weight:700;letter-spacing:.16em;color:#8cc4d4}
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

/* ---------- scene ---------- */
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
const errs = [];
page.on("pageerror", (e) => errs.push(String(e).slice(0, 200)));
page.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 200)); });

await page.goto(`http://127.0.0.1:${PORT}/tools/scene3d.html`, { waitUntil: "load" });
await page.waitForFunction(() => window.__sceneLoaded === true, { timeout: 30000 });
await page.evaluate((t) => window.ARTAC.init(t), THEME);
const info = await page.evaluate(() => window.ARTAC.info());
console.log(`scene: webgl=${info.webgl} shadows=${info.shadows} parts=${info.phoneParts}`);

/* ---------- render frames into ffmpeg ---------- */
const raw = resolve(WORK, "scene.mp4");
const ff = spawn("ffmpeg", [
  "-v", "error", "-y",
  "-f", "image2pipe", "-framerate", String(FPS), "-i", "-",
  "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", raw,
], { stdio: ["pipe", "ignore", "pipe"] });
let ffErr = "";
ff.stderr.on("data", (d) => { ffErr += d; });
const ffDone = new Promise((ok, no) =>
  ff.on("close", (c) => (c === 0 ? ok() : no(new Error(`ffmpeg pipe exit ${c}\n${ffErr.slice(-1200)}`)))));
const write = (b) => (ff.stdin.write(b) ? Promise.resolve() : new Promise((r) => ff.stdin.once("drain", r)));

const ranges = [];
for (let beat = 0; beat < BEATS.length; beat++) {
  await page.evaluate(
    (s) => window.ARTAC.setScreen(s),
    `http://127.0.0.1:${PORT}/shots-tall/${THEME}/${BEATS[beat].f}`
  );
  const range = await page.evaluate(() => window.ARTAC.scrollRange());
  ranges.push(range);

  for (let f = 0; f < BEAT_FRAMES; f++) {
    const p = f / (BEAT_FRAMES - 1);
    await page.evaluate(([b, pp, sc]) => {
      window.ARTAC.applyPose(b, pp);
      window.ARTAC.setScroll(sc);
      window.ARTAC.redraw();
    }, [beat, p, scrollAt(p)]);
    await write(await page.screenshot({ type: "png" }));
  }
  process.stdout.write(`\r  beats: ${beat + 1}/${BEATS.length} (scroll range ${range.toFixed(2)})`);
}
console.log();

ff.stdin.end();
await ffDone;
if (errs.length) console.log("scene warnings:", errs.slice(0, 4));

/* ---------- composite captions ---------- */
const run = (args) => new Promise((ok, no) => {
  const p = spawn("ffmpeg", args, { stdio: ["ignore", "ignore", "pipe"] });
  let e = ""; p.stderr.on("data", (d) => { e += d; });
  p.on("close", (c) => (c === 0 ? ok() : no(new Error(`ffmpeg exit ${c}\n${e.slice(-1500)}`))));
});

const inputs = ["-i", raw];
overlays.forEach((o) => inputs.push("-loop", "1", "-t", String(BEAT_SEC), "-i", o));

let fc = "", prev = "0:v";
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
  "-pix_fmt", "yuv420p", "-r", String(FPS), "-movflags", "+faststart", OUT,
]);

const totalFrames = BEATS.length * BEAT_FRAMES;
await writeFile(`${WORK}/manifest.json`, JSON.stringify({
  theme: THEME, beats: BEATS.map((b) => b.f), scrollRanges: ranges,
  frames: totalFrames, seconds: totalFrames / FPS,
}, null, 2));

await browser.close();
server.close();
console.log(`done: ${OUT} (${(totalFrames / FPS).toFixed(1)}s, ${totalFrames} frames)`);
console.log(`scroll ranges: ${ranges.map((r) => r.toFixed(2)).join(", ")}`);
