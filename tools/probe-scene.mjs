/* Renders a handful of poses from scene3d.html and checks the result
   really is a lit 3D phone: screenshot texture visible, background
   distinct from the device, and the pose actually changing per beat. */
import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import { resolve } from "node:path";

const THEME = process.argv[2] === "glass" ? "glass" : "neu";
const DIR = `tools/probe-${THEME}`;
await mkdir(DIR, { recursive: true });

let bad = 0;
const note = (ok, m) => { console.log(`${ok ? "ok  " : "FAIL"} ${m}`); if (!ok) bad++; };

// ES modules are blocked over file:// by CORS, so the scene is served over HTTP.
const { startServer } = await import("./httpserve.mjs");
const server = await startServer(5177);

const browser = await chromium.launch({
  args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
});
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
const errs = [];
page.on("pageerror", (e) => errs.push(String(e).slice(0, 200)));
page.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 200)); });

await page.goto("http://127.0.0.1:5177/tools/scene3d.html", { waitUntil: "load" });
await page.waitForFunction(() => window.__sceneLoaded === true, { timeout: 30000 });
await page.evaluate((t) => window.ARTAC.init(t), THEME);

const info = await page.evaluate(() => window.ARTAC.info());
note(info.webgl === true, `webgl active (${info.renderer})`);
note(info.shadows === true, "shadow map enabled");
// root children: phone group, floor, 4 lights = 6 minimum
note(info.objects >= 6, `scene populated (${info.objects} root objects)`);
note(info.phoneParts >= 10, `phone assembled (${info.phoneParts} meshes)`);
note(info.screenLit === true, `screen plane in front of chassis (faceZ=${info.faceZ})`);

const src = `http://127.0.0.1:5177/shots/${THEME}/app-dokter-01-ringkasan.png`;
await page.evaluate((s) => window.ARTAC.setScreen(s), src);
note(await page.evaluate(() => window.ARTAC.ready()), "screen texture bound");

/* sample pixels: centre should be the phone screen, corner the backdrop */
async function sample(beat, p) {
  await page.evaluate(([b, pp]) => window.ARTAC.applyPose(b, pp), [beat, p]);
  return page.evaluate(() => {
    const c = document.querySelector("canvas");
    const g = document.createElement("canvas");
    g.width = c.width; g.height = c.height;
    g.getContext("2d").drawImage(c, 0, 0);
    const ctx = g.getContext("2d");
    const at = (x, y) => [...ctx.getImageData(x, y, 1, 1).data].slice(0, 3);
    // average a small block to resist single-pixel noise
    const block = (cx, cy, n = 16) => {
      const d = ctx.getImageData(cx - n / 2, cy - n / 2, n, n).data;
      let r = 0, gg = 0, b = 0;
      for (let i = 0; i < d.length; i += 4) { r += d[i]; gg += d[i + 1]; b += d[i + 2]; }
      const px = d.length / 4;
      return [Math.round(r / px), Math.round(gg / px), Math.round(b / px)];
    };
    /* Scan a horizontal line through the middle for the darkest run: that
       is the chassis frame, wherever the current pose puts it. */
    const row = ctx.getImageData(0, Math.round(c.height / 2), c.width, 1).data;
    let edge = [255, 255, 255];
    for (let x = 0; x < c.width; x++) {
      const p = [row[x * 4], row[x * 4 + 1], row[x * 4 + 2]];
      if (p[0] + p[1] + p[2] < edge[0] + edge[1] + edge[2]) edge = p;
    }
    return {
      centre: block(c.width / 2, c.height / 2),
      corner: at(12, 12),
      lower: block(c.width / 2, c.height * 0.78),
      edge,
    };
  });
}

const a = await sample(0, 0.5);
const b = await sample(2, 0.5);
const c = await sample(5, 1.0);

console.log(`   beat0 centre=${a.centre} corner=${a.corner}`);
console.log(`   beat2 centre=${b.centre} corner=${b.corner}`);

const dist = (p, q) => Math.abs(p[0] - q[0]) + Math.abs(p[1] - q[1]) + Math.abs(p[2] - q[2]);

/* The light theme's app screen is nearly as bright as the backdrop, so
   comparing screen-vs-backdrop proves nothing. Compare the dark chassis
   edge instead, which must stand apart from the background. */
note(dist(a.edge, a.corner) > 60,
  `device edge distinct from backdrop (edge ${a.edge} vs bg ${a.corner}, delta ${dist(a.edge, a.corner)})`);
note(dist(a.centre, b.centre) > 8 || dist(a.lower, b.lower) > 8,
  `pose changes between beats (centre delta ${dist(a.centre, b.centre)}, lower delta ${dist(a.lower, b.lower)})`);
note(a.centre.some((v) => v > 25), `frame is not black (${a.centre})`);

/* The screen shows the app UI, so the centre must be bright and colourful
   rather than the near-black of an unlit chassis. */
const bright = Math.max(...a.centre);
note(bright > 70, `screen texture visible on device (peak channel ${bright}, rgb ${a.centre})`);
void c;
note(errs.length === 0, `no scene errors (${errs.length})`);
errs.slice(0, 3).forEach((e) => console.log("   >", e));

/* save contact sheets for eyeballing */
for (let i = 0; i < 6; i++) {
  await page.evaluate(([bt, pp]) => window.ARTAC.applyPose(bt, pp), [i, 0.55]);
  await page.screenshot({ path: `${DIR}/pose${i}.png` });
}
console.log(`   wrote 6 probe frames to ${DIR}/`);

await browser.close();
server.close();
console.log(bad ? `\n${bad} check(s) failed.` : "\n3D scene verified.");
process.exit(bad ? 1 : 0);
