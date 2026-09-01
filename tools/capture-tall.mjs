/* ============================================================
   ARTA-C — full-page (tall) captures for the scrolling 3D showcase.
   The 3D scene pans these vertically inside the phone screen, so
   each capture must contain the WHOLE page, not just the viewport.
   ============================================================ */
import { chromium } from "playwright";
import { mkdir, rm } from "node:fs/promises";
import { spawnSync } from "node:child_process";

const BASE = process.argv[2] || "http://127.0.0.1:5099";
const OUT = "shots-tall";

// CSS viewport is phone-shaped; 2x scale keeps text crisp in the texture.
const CSS_W = 540, CSS_H = 960, DSF = 2;
const MAX_TEX = 8192; // WebGL limit reported by this machine

/* View and patient chosen by measurement (tools/pick-views.mjs), not by
   guesswork: these six are the tallest screens in the app, so each one has
   real travel to scroll. VOT and Konsultasi are excluded because both size
   themselves to the viewport and are exactly one screen tall. */
const PAGES = [
  { id: "01-ringkasan", view: "ringkasan", role: "dokter", patient: "Bayu" },
  { id: "02-pasien", view: "pasien", role: "dokter", patient: "Bayu" },
  { id: "03-jadwal", view: "jadwal", role: "dokter", patient: "Siti" },
  { id: "04-perangkat", view: "perangkat", role: "dokter", patient: "Siti" },
  { id: "05-peringatan", view: "peringatan", role: "dokter", patient: "Siti" },
  { id: "06-laporan", view: "laporan", role: "dokter", patient: "Siti" },
];

await rm(OUT, { recursive: true, force: true });
await mkdir(OUT, { recursive: true });

const SETTLE = `
  *, *::before, *::after {
    animation-duration: .001ms !important;
    animation-delay: 0ms !important;
    transition-duration: .001ms !important;
  }
  [data-reveal] { opacity: 1 !important; }
  /* the sticky app bar would otherwise repeat down a full-page capture */
  .appbar { position: static !important; }
  .sidebar { position: fixed !important; }
`;

const browser = await chromium.launch();
const results = [];

for (const theme of ["neu", "glass"]) {
  const ctx = await browser.newContext({
    viewport: { width: CSS_W, height: CSS_H },
    deviceScaleFactor: DSF,
    isMobile: true,
    hasTouch: true,
  });
  await ctx.addInitScript((t) => {
    localStorage.setItem("artac.theme", t);
    localStorage.setItem("artac.demo", "1");
  }, theme);

  await mkdir(`${OUT}/${theme}`, { recursive: true });

  // one page per role, reused across its views
  for (const role of ["dokter"]) {
    const jobs = PAGES.filter((p) => p.role === role);
    if (!jobs.length) continue;

    const page = await ctx.newPage();
    page.on("pageerror", (e) => console.log("  ! ", String(e).slice(0, 120)));
    await page.goto(`${BASE}/app.html?demo=1`, { waitUntil: "networkidle" });
    // the demo session survives in this context, so sign out before
    // picking the next role or the login buttons stay hidden
    await page.evaluate(() => localStorage.removeItem("artac.demo.session"));
    await page.reload({ waitUntil: "networkidle" });
    await page.waitForSelector(`[data-demo-role="${role}"]`, { state: "visible", timeout: 15000 });
    await page.click(`[data-demo-role="${role}"]`);
    await page.waitForSelector("#shell:not(.hidden)", { timeout: 15000 });
    await page.waitForTimeout(1200);

    for (const job of jobs) {
      if (job.patient) {
        const picked = await page.evaluate((want) => {
          const sel = document.getElementById("patientPick");
          const opt = [...sel.options].find((o) => o.textContent.includes(want));
          if (!opt) return null;
          sel.value = opt.value;
          sel.dispatchEvent(new Event("change"));
          return opt.textContent;
        }, job.patient);
        if (!picked) console.log(`  ! patient "${job.patient}" not found for ${job.id}`);
        await page.waitForTimeout(900);
      }
      await page.evaluate((v) => { location.hash = v; }, job.view);
      await page.waitForTimeout(900);
      await page.addStyleTag({ content: SETTLE });
      await page.waitForTimeout(400);

      const h = await page.evaluate(() =>
        Math.max(document.body.scrollHeight, document.documentElement.scrollHeight));

      const file = `${OUT}/${theme}/${job.id}.png`;
      await page.screenshot({ path: file, fullPage: true });

      // clamp anything taller than the GPU texture limit
      const probe = spawnSync("ffprobe", ["-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "csv=p=0", file], { encoding: "utf8" });
      let [w, ph] = probe.stdout.trim().split(",").map(Number);

      if (ph > MAX_TEX) {
        spawnSync("ffmpeg", ["-v", "error", "-y", "-i", file,
          "-vf", `crop=${w}:${MAX_TEX}:0:0`, `${file}.tmp.png`]);
        spawnSync("cmd", ["/c", "move", "/y", `${file}.tmp.png`.replace(/\//g, "\\"), file.replace(/\//g, "\\")]);
        ph = MAX_TEX;
        console.log(`  clamped ${job.id} to ${MAX_TEX}px`);
      }

      const screens = (ph / (CSS_H * DSF)).toFixed(2);
      results.push({ theme, id: job.id, w, h: ph, screens: Number(screens) });
      console.log(`  ${theme}/${job.id}: ${w}x${ph} (css height ${h}px, ${screens} screens)`);
    }
    await page.close();
  }
  await ctx.close();
}

await browser.close();

console.log("\nsummary:");
for (const r of results) {
  const scrollable = r.screens > 1.08;
  console.log(`  ${r.theme}/${r.id}  ${r.w}x${r.h}  ${r.screens} screens  ${scrollable ? "scrollable" : "SHORT — little to scroll"}`);
}
