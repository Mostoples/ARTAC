/* ============================================================
   ARTA-C — portrait screenshot capture
   Walks every page in both themes and all three roles, writing
   1080x1920 portrait PNGs ready for a vertical video edit.
   ============================================================ */
import { chromium } from "playwright";
import { mkdir, rm } from "node:fs/promises";

const BASE = process.argv[2] || "http://127.0.0.1:5099";
const OUT = "shots";
const W = 1080, H = 1920;

// Portrait at 1080x1920 with a 0.5 scale factor gives a 540x960 CSS
// viewport: a phone-shaped layout rendered at 2x for crisp output.
const DSF = 2;
const CSS_W = W / DSF, CSS_H = H / DSF;

await rm(OUT, { recursive: true, force: true });
await mkdir(OUT, { recursive: true });

const browser = await chromium.launch();
const shots = [];

/** Freezes animation so captures are deterministic, not mid-flight. */
const SETTLE_CSS = `
  *, *::before, *::after {
    animation-duration: .001ms !important;
    animation-delay: 0ms !important;
    transition-duration: .001ms !important;
  }
  [data-reveal] { opacity: 1 !important; }
`;

async function newPage(theme) {
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
  const page = await ctx.newPage();
  page.on("pageerror", (e) => console.log("  ! page error:", String(e).slice(0, 120)));
  return { ctx, page };
}

async function shoot(page, name, { full = false } = {}) {
  await page.addStyleTag({ content: SETTLE_CSS });
  await page.waitForTimeout(450);
  const file = `${OUT}/${name}.png`;
  await page.screenshot({ path: file, fullPage: full });
  shots.push(file);
  console.log(`  captured ${file}`);
}

/* ---------------- landing pages ---------------- */
for (const theme of ["neu", "glass"]) {
  console.log(`\n[${theme}] landing`);
  const { ctx, page } = await newPage(theme);
  await page.goto(`${BASE}/`, { waitUntil: "networkidle" });
  await page.waitForTimeout(700);

  const sections = [
    ["01-hero", null],
    ["02-cara-kerja", "#cara-kerja"],
    ["03-perangkat", "#perangkat"],
    ["04-aplikasi", "#aplikasi"],
    ["05-eskalasi-vot", "#escWrap"],
    ["06-kemitraan", "#kemitraan"],
    ["07-keterbatasan", "#catatan"],
  ];

  for (const [name, sel] of sections) {
    if (sel) {
      await page.evaluate((s) => {
        const el = document.querySelector(s);
        if (el) window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY - 70, behavior: "instant" });
      }, sel);
      await page.waitForTimeout(500);
    }
    await shoot(page, `${theme}-landing-${name}`);
  }
  await ctx.close();
}

/* ---------------- dashboard, per role ---------------- */
const VIEWS = [
  ["ringkasan", "Ringkasan"],
  ["pasien", "Pasien"],
  ["jadwal", "Jadwal"],
  ["perangkat", "Kotak Obat"],
  ["peringatan", "Peringatan"],
  ["vot", "VOT"],
  ["keluhan", "Keluhan"],
  ["konsultasi", "Konsultasi"],
  ["laporan", "Laporan"],
  ["profil", "Profil"],
];

for (const theme of ["neu", "glass"]) {
  for (const role of ["dokter", "pmo", "pasien"]) {
    console.log(`\n[${theme}] dashboard as ${role}`);
    const { ctx, page } = await newPage(theme);
    await page.goto(`${BASE}/app.html?demo=1`, { waitUntil: "networkidle" });
    await page.waitForTimeout(800);

    // capture the sign-in screen once per theme
    if (role === "dokter") await shoot(page, `${theme}-app-00-masuk`);

    await page.click(`[data-demo-role="${role}"]`);
    await page.waitForSelector("#shell:not(.hidden)", { timeout: 15000 });
    await page.waitForTimeout(1100);

    let n = 1;
    for (const [view, label] of VIEWS) {
      const link = page.locator(`#sideNav a[data-nav="${view}"]`);
      if (!(await link.count())) continue; // role does not have this view
      await page.evaluate((v) => { location.hash = v; }, view);
      await page.waitForTimeout(700);
      await shoot(page, `${theme}-app-${role}-${String(n).padStart(2, "0")}-${view}`);
      void label;
      n++;
    }

    // the mobile drawer, shown once per theme
    if (role === "dokter") {
      await page.evaluate(() => { location.hash = "ringkasan"; });
      await page.waitForTimeout(500);
      await page.click("#burger");
      await page.waitForTimeout(600);
      await shoot(page, `${theme}-app-${role}-99-menu`);
    }
    await ctx.close();
  }
}

await browser.close();
console.log(`\n${shots.length} screenshots written to ${OUT}/`);
