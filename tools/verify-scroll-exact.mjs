/* Measures scrolling inside the EXACT projected screen rectangle for each
   beat, asking the scene where the display is rather than assuming a fixed
   crop. Also reports contrast, because a light low-contrast page produces a
   small luma delta even when it scrolls a long way. */
import { chromium } from "playwright";
import { spawnSync } from "node:child_process";

const BEAT_SEC = 5.0, BEATS = 6;
const PORT = 5185;
const N = 32;
let bad = 0;
const note = (ok, m) => { console.log(`${ok ? "ok  " : "FAIL"} ${m}`); if (!ok) bad++; };

const grayCrop = (file, at, crop) => {
  const r = spawnSync("ffmpeg", ["-v", "error", "-ss", String(at), "-i", file,
    "-vf", `${crop},scale=${N}:${N},format=gray`, "-frames:v", "1", "-f", "rawvideo", "-"],
    { maxBuffer: 1 << 22 });
  return r.stdout?.length ? [...r.stdout] : null;
};
const diff = (a, b) => a.reduce((s, v, i) => s + Math.abs(v - b[i]), 0) / a.length;
const sd = (a) => {
  const m = a.reduce((x, y) => x + y, 0) / a.length;
  return Math.sqrt(a.reduce((x, y) => x + (y - m) ** 2, 0) / a.length);
};

/* Reproduce the render's scroll curve so we sample where motion happens. */
function scrollAt(p) {
  const HI = 0.18, HO = 0.14;
  if (p <= HI) return 0;
  if (p >= 1 - HO) return 1;
  const t = (p - HI) / (1 - HI - HO);
  return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
}

const { startServer } = await import("./httpserve.mjs");
const server = await startServer(PORT);
const browser = await chromium.launch({
  args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
});

const FILES = ["01-ringkasan.png", "02-pasien.png", "03-jadwal.png",
  "04-perangkat.png", "05-peringatan.png", "06-laporan.png"];

for (const [theme, label] of [["neu", "Neumorph"], ["glass", "Glass"]]) {
  const vid = `video/ARTA-C-3D-Scroll-${label}-1080x1920.mp4`;
  console.log(`\n--- ${label} ---`);

  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto(`http://127.0.0.1:${PORT}/tools/scene3d.html`, { waitUntil: "load" });
  await page.waitForFunction(() => window.__sceneLoaded === true, { timeout: 30000 });
  await page.evaluate((t) => window.ARTAC.init(t), theme);

  let moving = 0;
  for (let b = 0; b < BEATS; b++) {
    await page.evaluate((s) => window.ARTAC.setScreen(s),
      `http://127.0.0.1:${PORT}/shots-tall/${theme}/${FILES[b]}`);
    const range = await page.evaluate(() => window.ARTAC.scrollRange());

    // two moments well inside the scrolling stretch
    const pA = 0.32, pB = 0.78;
    const tA = b * BEAT_SEC + pA * BEAT_SEC;
    const tB = b * BEAT_SEC + pB * BEAT_SEC;

    // screen rect at each moment (camera also drifts, so recompute)
    const rectAt = async (p) => {
      await page.evaluate(([bb, pp]) => window.ARTAC.applyPose(bb, pp), [b, p]);
      return page.evaluate(() => window.ARTAC.screenRect());
    };
    const rA = await rectAt(pA), rB = await rectAt(pB);
    // intersect the two rects so the same pixels are compared
    const x = Math.max(rA.x, rB.x), y = Math.max(rA.y, rB.y);
    const w = Math.min(rA.x + rA.w, rB.x + rB.w) - x;
    const h = Math.min(rA.y + rA.h, rB.y + rB.h) - y;
    const ins = 0.1;
    const crop = `crop=${Math.round(w * (1 - ins * 2))}:${Math.round(h * (1 - ins * 2))}:${Math.round(x + w * ins)}:${Math.round(y + h * ins)}`;

    const gA = grayCrop(vid, tA, crop), gB = grayCrop(vid, tB, crop);
    const d = diff(gA, gB);
    const contrast = (sd(gA) + sd(gB)) / 2;
    // normalise: a low-contrast page cannot produce a big absolute delta
    const rel = contrast > 0 ? d / contrast : 0;
    const ok = rel > 0.18;
    if (ok) moving++;
    console.log(`   beat ${b + 1} (${FILES[b].replace(".png", "")}): range ${range.toFixed(2)}  delta ${d.toFixed(1)}  contrast ${contrast.toFixed(1)}  ratio ${rel.toFixed(2)} ${ok ? "" : "<-- weak"}`);
  }
  note(moving === BEATS, `${label}: content visibly scrolls in all ${BEATS} beats (${moving}/${BEATS})`);
  await page.close();
}

await browser.close();
server.close();
console.log(bad ? `\n${bad} check(s) failed.` : "\nIn-screen scrolling confirmed for every beat.");
process.exit(bad ? 1 : 0);
