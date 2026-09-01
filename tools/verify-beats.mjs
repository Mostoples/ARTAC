/* Confirms each beat of the 3D video shows its intended page.

   Correlating against the flat screenshot fails because the on-screen
   image is perspective-projected, rotated and lit — geometrically it is
   not the source image. Instead, re-render each beat's pose in the live
   scene twice (once per candidate texture) and check the video frame
   matches the render made with the *intended* texture more closely than
   the others. Same projection on both sides, so the comparison is fair. */
import { chromium } from "playwright";
import { spawnSync } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";

const BEATS = [
  "app-dokter-01-ringkasan.png", "app-dokter-03-jadwal.png",
  "app-dokter-04-perangkat.png", "app-dokter-05-peringatan.png",
  "app-pasien-05-vot.png", "app-dokter-09-laporan.png",
];
const BEAT_SEC = 4.0;
const N = 40;

let bad = 0;
const note = (ok, m) => { console.log(`${ok ? "ok  " : "FAIL"} ${m}`); if (!ok) bad++; };

const grayOf = (buf) => {
  const r = spawnSync("ffmpeg", ["-v", "error", "-i", "-", "-vf", `scale=${N}:${N},format=gray`,
    "-frames:v", "1", "-f", "rawvideo", "-"], { input: buf, maxBuffer: 1 << 22 });
  return r.stdout && r.stdout.length ? [...r.stdout] : null;
};
const grayFileCrop = (f, at, crop) => {
  const r = spawnSync("ffmpeg", ["-v", "error", "-ss", String(at), "-i", f,
    "-vf", `${crop},scale=${N}:${N},format=gray`, "-frames:v", "1", "-f", "rawvideo", "-"],
    { maxBuffer: 1 << 22 });
  return r.stdout && r.stdout.length ? [...r.stdout] : null;
};
const corr = (a, b) => {
  const n = a.length;
  const ma = a.reduce((s, v) => s + v, 0) / n, mb = b.reduce((s, v) => s + v, 0) / n;
  let num = 0, da = 0, db = 0;
  for (let i = 0; i < n; i++) { const x = a[i] - ma, y = b[i] - mb; num += x * y; da += x * x; db += y * y; }
  return da && db ? num / Math.sqrt(da * db) : 0;
};

const { startServer } = await import("./httpserve.mjs");
const server = await startServer(5181);
const browser = await chromium.launch({
  args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
});

for (const [theme, label] of [["neu", "Neumorph"], ["glass", "Glass"]]) {
  console.log(`\n--- ${label} ---`);
  const vid = `video/ARTA-C-3D-${label}-1080x1920.mp4`;

  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto("http://127.0.0.1:5181/tools/scene3d.html", { waitUntil: "load" });
  await page.waitForFunction(() => window.__sceneLoaded === true, { timeout: 30000 });
  await page.evaluate((t) => window.ARTAC.init(t), theme);

  let hits = 0;
  for (let i = 0; i < BEATS.length; i++) {
    // mid-beat frame from the finished video (before the caption fades up
    // fully we still get the card, so crop it away by comparing top 2/3)
    const t = i * BEAT_SEC + BEAT_SEC / 2;
    const p = 0.5; // applyPose progress at mid-beat

    /* Ask the scene where the display actually is for this pose, then
       compare only those pixels. Comparing whole frames fails: the
       chassis and backdrop are identical across candidates and swamp
       the small screen region that actually differs. */
    await page.evaluate(([b, pp]) => window.ARTAC.applyPose(b, pp), [i, p]);
    const rect = await page.evaluate(() => window.ARTAC.screenRect());
    // inset to stay clear of the bezel edge
    const inset = 0.1;
    const clip = {
      x: Math.round(rect.x + rect.w * inset),
      y: Math.round(rect.y + rect.h * inset),
      width: Math.round(rect.w * (1 - inset * 2)),
      height: Math.round(rect.h * (1 - inset * 2)),
    };
    const vidCrop = `crop=${clip.width}:${clip.height}:${clip.x}:${clip.y}`;
    const target = grayFileCrop(vid, t, vidCrop);

    const scores = [];
    for (let c = 0; c < BEATS.length; c++) {
      await page.evaluate((s) => window.ARTAC.setScreen(s), `http://127.0.0.1:5181/shots/${theme}/${BEATS[c]}`);
      await page.evaluate(([b, pp]) => window.ARTAC.applyPose(b, pp), [i, p]);
      const shot = await page.screenshot({ type: "png", clip });
      scores.push(corr(grayOf(shot), target));
    }
    const best = scores.indexOf(Math.max(...scores));
    const ok = best === i;
    if (ok) hits++;
    console.log(`   beat ${i + 1} (${BEATS[i].replace(/^app-/, "")}): own r=${scores[i].toFixed(3)}, best=#${best + 1} r=${scores[best].toFixed(3)} ${ok ? "" : "<-- mismatch"}`);
  }
  note(hits === BEATS.length, `${label}: all 6 beats show their intended page (${hits}/6)`);
  await page.close();
}

await browser.close();
server.close();
console.log(bad ? `\n${bad} check(s) failed.` : "\nEvery beat verified against its intended page.");
process.exit(bad ? 1 : 0);
