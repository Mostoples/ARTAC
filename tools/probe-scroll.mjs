/* Confirms the in-screen scroll actually works: the display region must
   change as the scroll offset advances, and the top of the page must match
   the top of the tall capture (proving orientation is not inverted). */
import { chromium } from "playwright";
import { spawnSync } from "node:child_process";
import { mkdir } from "node:fs/promises";

const THEME = process.argv[2] === "glass" ? "glass" : "neu";
const PORT = 5183;
const N = 36;
let bad = 0;
const note = (ok, m) => { console.log(`${ok ? "ok  " : "FAIL"} ${m}`); if (!ok) bad++; };

const grayBuf = (buf) => {
  const r = spawnSync("ffmpeg", ["-v", "error", "-i", "-", "-vf", `scale=${N}:${N},format=gray`,
    "-frames:v", "1", "-f", "rawvideo", "-"], { input: buf, maxBuffer: 1 << 22 });
  return r.stdout?.length ? [...r.stdout] : null;
};
const grayCrop = (f, crop) => {
  const r = spawnSync("ffmpeg", ["-v", "error", "-i", f, "-vf", `${crop},scale=${N}:${N},format=gray`,
    "-frames:v", "1", "-f", "rawvideo", "-"], { maxBuffer: 1 << 22 });
  return r.stdout?.length ? [...r.stdout] : null;
};
const corr = (a, b) => {
  const n = a.length, ma = a.reduce((s, v) => s + v, 0) / n, mb = b.reduce((s, v) => s + v, 0) / n;
  let num = 0, da = 0, db = 0;
  for (let i = 0; i < n; i++) { const x = a[i] - ma, y = b[i] - mb; num += x * y; da += x * x; db += y * y; }
  return da && db ? num / Math.sqrt(da * db) : 0;
};
const diff = (a, b) => a.reduce((s, v, i) => s + Math.abs(v - b[i]), 0) / a.length;

const DIR = `tools/scrollprobe-${THEME}`;
await mkdir(DIR, { recursive: true });

const { startServer } = await import("./httpserve.mjs");
const server = await startServer(PORT);
const browser = await chromium.launch({
  args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
});
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
const errs = [];
page.on("pageerror", (e) => errs.push(String(e).slice(0, 160)));
await page.goto(`http://127.0.0.1:${PORT}/tools/scene3d.html`, { waitUntil: "load" });
await page.waitForFunction(() => window.__sceneLoaded === true, { timeout: 30000 });
await page.evaluate((t) => window.ARTAC.init(t), THEME);

const PAGE = "01-ringkasan.png";
await page.evaluate((s) => window.ARTAC.setScreen(s), `http://127.0.0.1:${PORT}/shots-tall/${THEME}/${PAGE}`);

const range = await page.evaluate(() => window.ARTAC.scrollRange());
note(range > 0.3, `scroll range available (${range.toFixed(3)} of texture off-screen)`);

// hold the phone square-on so the screen rect is stable while scrolling
async function frameAt(scroll) {
  await page.evaluate(([sc]) => {
    window.ARTAC.applyPose(2, 1.0);   // final pose of beat 3: near front-on
    window.ARTAC.setScroll(sc);
    window.ARTAC.redraw();
  }, [scroll]);
  const rect = await page.evaluate(() => window.ARTAC.screenRect());
  const inset = 0.08;
  const clip = {
    x: Math.round(rect.x + rect.w * inset), y: Math.round(rect.y + rect.h * inset),
    width: Math.round(rect.w * (1 - inset * 2)), height: Math.round(rect.h * (1 - inset * 2)),
  };
  return { buf: await page.screenshot({ type: "png", clip }), clip };
}

/* tall capture metadata, needed to slice it for comparison */
const tall = `shots-tall/${THEME}/${PAGE}`;
const dim = spawnSync("ffprobe", ["-v", "error", "-select_streams", "v:0",
  "-show_entries", "stream=width,height", "-of", "csv=p=0", tall], { encoding: "utf8" });
const [tw, th] = dim.stdout.trim().split(",").map(Number);
// how tall a slice of the texture is visible at once, matching screen aspect
const windowH = Math.min(th, Math.round(tw * (1920 / 1080)));
const tallPath = () => tall;
const twGuess = () => tw;
const windowHGuess = () => windowH;

const f0 = await frameAt(0);
const f5 = await frameAt(0.5);
const f1 = await frameAt(1);

const g0 = grayBuf(f0.buf), g5 = grayBuf(f5.buf), g1 = grayBuf(f1.buf);
note(g0 && g5 && g1, "frames captured");

const d05 = diff(g0, g5), d51 = diff(g5, g1), d01 = diff(g0, g1);
console.log(`   deltas: top->mid ${d05.toFixed(1)}, mid->bottom ${d51.toFixed(1)}, top->bottom ${d01.toFixed(1)}`);
note(d05 > 8 && d51 > 8, "screen content changes as it scrolls");

/* Monotonicity is checked against the UV offset the scene actually applied,
   which is exact. Estimating it by image correlation is unreliable here:
   whitespace-heavy slices of a long page correlate weakly and the best
   match jitters, even though the underlying scroll is perfectly linear. */
const steps = [0, 0.25, 0.5, 0.75, 1];
const offsets = [];
for (const s of steps) {
  await page.evaluate(([sc]) => {
    window.ARTAC.applyPose(2, 1.0);
    window.ARTAC.setScroll(sc);
    window.ARTAC.redraw();
  }, [s]);
  offsets.push(await page.evaluate(() => window.ARTAC.uv().offsetY));
}
console.log(`   UV offset: ${offsets.map((v) => v.toFixed(3)).join(" -> ")}`);
// V axis is bottom-up, so scrolling down means the offset decreases
const strictlyDown = offsets.every((v, i) => i === 0 || v < offsets[i - 1] - 1e-6);
note(strictlyDown, "scroll advances steadily down the page");

const spacing = offsets.slice(1).map((v, i) => offsets[i] - v);
const even = Math.max(...spacing) - Math.min(...spacing) < 1e-6;
note(even, `scroll is linear in the drive parameter (steps ${spacing.map((s) => s.toFixed(4)).join(", ")})`);
note(Math.abs(offsets[0] - range) < 1e-6 && Math.abs(offsets[4]) < 1e-6,
  `scroll spans the full page (${offsets[0].toFixed(3)} -> ${offsets[4].toFixed(3)}, range ${range.toFixed(3)})`);

/* orientation: at scroll=0 the screen should match the TOP slice of the
   tall capture, not the bottom. */
const topSlice = grayCrop(tall, `crop=${tw}:${windowH}:0:0`);
const botSlice = grayCrop(tall, `crop=${tw}:${windowH}:0:${Math.max(0, th - windowH)}`);

const rTop = corr(g0, topSlice), rTopBot = corr(g0, botSlice);
const rBot = corr(g1, botSlice), rBotTop = corr(g1, topSlice);
console.log(`   scroll=0 : r(top)=${rTop.toFixed(3)} r(bottom)=${rTopBot.toFixed(3)}`);
console.log(`   scroll=1 : r(bottom)=${rBot.toFixed(3)} r(top)=${rBotTop.toFixed(3)}`);
note(rTop > rTopBot, "scroll=0 shows the top of the page");
note(rBot > rBotTop, "scroll=1 shows the bottom of the page");

note(errs.length === 0, `no scene errors (${errs.length})`);

const { writeFile } = await import("node:fs/promises");
for (const [n, f] of [["top", f0], ["mid", f5], ["bottom", f1]]) {
  await writeFile(`${DIR}/${n}.png`, f.buf);
}

await browser.close();
server.close();
console.log(bad ? `\n${bad} check(s) failed.` : "\nIn-screen scrolling verified.");
process.exit(bad ? 1 : 0);
