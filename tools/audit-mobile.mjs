/* ============================================================
   Mobile layout audit: finds elements that overflow their container
   or the viewport, text below a legible size, and touch targets that
   are too small. Reports facts, no fixes.
   ============================================================ */
import { chromium } from "playwright";

const BASE = process.argv[2] || "http://127.0.0.1:5099";

const DEVICES = [
  { name: "small  360x640", w: 360, h: 640 },
  { name: "mid    390x844", w: 390, h: 844 },
  { name: "large  430x932", w: 430, h: 932 },
];

const VIEWS = ["ringkasan", "pasien", "jadwal", "perangkat", "peringatan",
  "vot", "keluhan", "konsultasi", "laporan", "profil"];

const AUDIT = `(() => {
  const out = { hOverflow: 0, wide: [], tiny: [], smallTap: [], clipped: [] };
  const vw = document.documentElement.clientWidth;
  out.hOverflow = document.documentElement.scrollWidth - vw;

  const seen = new Set();
  for (const el of document.querySelectorAll("#content *, .appbar *, .sidebar *")) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === "hidden" || cs.display === "none") continue;

    const tag = el.tagName.toLowerCase() + (el.className && typeof el.className === "string"
      ? "." + el.className.trim().split(/\\s+/).slice(0, 2).join(".") : "");

    // spills past the right edge of the viewport
    if (r.right > vw + 1 && !seen.has("w" + tag)) {
      seen.add("w" + tag);
      out.wide.push({ tag, right: Math.round(r.right), vw, over: Math.round(r.right - vw) });
    }

    // content wider than its own scroll container (horizontal clipping).
    // .sr-only is deliberately clipped to 1px for screen readers.
    if (el.scrollWidth > el.clientWidth + 2 && el.clientWidth > 0 && !el.classList.contains("sr-only")) {
      const oxHidden = cs.overflowX === "hidden";
      if (oxHidden && !seen.has("c" + tag)) {
        seen.add("c" + tag);
        out.clipped.push({ tag, scrollW: el.scrollWidth, clientW: el.clientWidth });
      }
    }

    // font size below 12px is hard to read on a phone
    const fs = parseFloat(cs.fontSize);
    const hasText = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim().length > 2);
    if (hasText && fs < 12 && !seen.has("f" + tag)) {
      seen.add("f" + tag);
      out.tiny.push({ tag, fontSize: +fs.toFixed(1), text: el.textContent.trim().slice(0, 34) });
    }

    // interactive targets under 40px in either direction
    if (el.matches("button, a, input, select, textarea, label.switch")) {
      if ((r.height > 0 && r.height < 40) || (r.width > 0 && r.width < 40)) {
        if (!seen.has("t" + tag)) {
          seen.add("t" + tag);
          out.smallTap.push({ tag, w: Math.round(r.width), h: Math.round(r.height) });
        }
      }
    }
  }
  return out;
})()`;

const browser = await chromium.launch();
const findings = [];

for (const dev of DEVICES) {
  const ctx = await browser.newContext({
    viewport: { width: dev.w, height: dev.h },
    deviceScaleFactor: 2, isMobile: true, hasTouch: true,
  });
  await ctx.addInitScript(() => {
    localStorage.setItem("artac.theme", "neu");
    localStorage.setItem("artac.demo", "1");
  });
  const page = await ctx.newPage();

  await page.goto(`${BASE}/app.html?demo=1`, { waitUntil: "networkidle" });
  await page.evaluate(() => localStorage.removeItem("artac.demo.session"));
  await page.reload({ waitUntil: "networkidle" });
  await page.waitForSelector('[data-demo-role="dokter"]', { state: "visible" });
  await page.click('[data-demo-role="dokter"]');
  await page.waitForSelector("#shell:not(.hidden)");
  await page.waitForTimeout(1100);

  console.log(`\n=== ${dev.name} ===`);

  // landing page too
  const lp = await ctx.newPage();
  await lp.goto(`${BASE}/`, { waitUntil: "networkidle" });
  await lp.waitForTimeout(600);
  const landing = await lp.evaluate(`(() => {
    const vw = document.documentElement.clientWidth;
    const over = document.documentElement.scrollWidth - vw;
    const wide = [];
    for (const el of document.querySelectorAll("body *")) {
      const r = el.getBoundingClientRect();
      if (r.width && r.right > vw + 1) {
        wide.push(el.tagName.toLowerCase() + "." + String(el.className).trim().split(/\\s+/)[0] + " +" + Math.round(r.right - vw));
      }
    }
    return { over, wide: [...new Set(wide)].slice(0, 6) };
  })()`);
  console.log(`landing: hOverflow=${landing.over}px ${landing.wide.length ? "| wide: " + landing.wide.join(", ") : ""}`);
  if (landing.over > 1) findings.push({ dev: dev.name, view: "landing", kind: "hOverflow", detail: `${landing.over}px` });
  await lp.close();

  for (const v of VIEWS) {
    const link = page.locator(`#sideNav a[data-nav="${v}"]`);
    if (!(await link.count())) continue;
    await page.evaluate((x) => { location.hash = x; }, v);
    await page.waitForTimeout(650);

    const r = await page.evaluate(AUDIT);
    const bits = [];
    if (r.hOverflow > 1) { bits.push(`hOverflow ${r.hOverflow}px`); findings.push({ dev: dev.name, view: v, kind: "hOverflow", detail: `${r.hOverflow}px` }); }
    if (r.wide.length) { bits.push(`${r.wide.length} spill`); findings.push({ dev: dev.name, view: v, kind: "spill", detail: r.wide.map((x) => `${x.tag}+${x.over}px`).join(" | ") }); }
    if (r.clipped.length) { bits.push(`${r.clipped.length} clipped`); findings.push({ dev: dev.name, view: v, kind: "clipped", detail: r.clipped.map((x) => `${x.tag} ${x.scrollW}>${x.clientW}`).join(" | ") }); }
    if (r.tiny.length) { bits.push(`${r.tiny.length} tiny-font`); findings.push({ dev: dev.name, view: v, kind: "tinyFont", detail: r.tiny.map((x) => `${x.tag} ${x.fontSize}px`).join(" | ") }); }
    if (r.smallTap.length) { bits.push(`${r.smallTap.length} small-tap`); findings.push({ dev: dev.name, view: v, kind: "smallTap", detail: r.smallTap.map((x) => `${x.tag} ${x.w}x${x.h}`).join(" | ") }); }

    console.log(`  ${v.padEnd(11)} ${bits.length ? bits.join(", ") : "clean"}`);
  }
  await ctx.close();
}

await browser.close();

console.log("\n================ DETAIL ================");
const byKind = new Map();
for (const f of findings) {
  if (!byKind.has(f.kind)) byKind.set(f.kind, []);
  byKind.get(f.kind).push(f);
}
for (const [kind, list] of byKind) {
  console.log(`\n## ${kind} (${list.length})`);
  const shown = new Set();
  for (const f of list) {
    const key = f.detail.slice(0, 90);
    if (shown.has(key)) continue;
    shown.add(key);
    console.log(`  [${f.dev} / ${f.view}] ${f.detail.slice(0, 200)}`);
  }
}
console.log(`\ntotal findings: ${findings.length}`);
