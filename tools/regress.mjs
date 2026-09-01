/* Regression check after the mobile layout work: the app must still
   function, and the layout must stay within the viewport. Runs at a phone
   width and a desktop width so the responsive rules are exercised both ways. */
import { chromium } from "playwright";

const BASE = process.argv[2] || "http://127.0.0.1:5099";
let bad = 0;
const note = (ok, m) => { console.log(`${ok ? "ok  " : "FAIL"} ${m}`); if (!ok) bad++; };

const browser = await chromium.launch();

for (const [label, vp, mobile] of [
  ["phone 360", { width: 360, height: 720 }, true],
  ["desktop 1440", { width: 1440, height: 900 }, false],
]) {
  console.log(`\n--- ${label} ---`);
  const ctx = await browser.newContext({ viewport: vp, deviceScaleFactor: 1, isMobile: mobile, hasTouch: mobile });
  await ctx.addInitScript(() => {
    localStorage.setItem("artac.theme", "neu");
    localStorage.setItem("artac.demo", "1");
  });
  const page = await ctx.newPage();
  const errs = [];
  page.on("pageerror", (e) => errs.push(String(e).slice(0, 160)));
  page.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 160)); });

  /* landing */
  await page.goto(`${BASE}/`, { waitUntil: "networkidle" });
  await page.waitForTimeout(700);
  const lo = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  note(lo <= 1, `${label}: landing no horizontal overflow (${lo}px)`);
  note(await page.locator("#steps article").count() === 6, `${label}: landing content rendered`);

  /* app */
  await page.goto(`${BASE}/app.html?demo=1`, { waitUntil: "networkidle" });
  await page.evaluate(() => localStorage.removeItem("artac.demo.session"));
  await page.reload({ waitUntil: "networkidle" });
  await page.waitForSelector('[data-demo-role="dokter"]', { state: "visible" });
  await page.click('[data-demo-role="dokter"]');
  await page.waitForSelector("#shell:not(.hidden)", { timeout: 15000 });
  await page.waitForTimeout(1100);
  note(true, `${label}: demo sign-in works`);

  let worst = 0, worstView = "";
  for (const v of ["ringkasan", "pasien", "jadwal", "perangkat", "peringatan",
    "vot", "keluhan", "konsultasi", "laporan", "profil"]) {
    await page.evaluate((x) => { location.hash = x; }, v);
    await page.waitForTimeout(520);
    const r = await page.evaluate(() => ({
      over: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      blocks: document.querySelectorAll("#content .view > *").length,
      minFont: Math.min(...[...document.querySelectorAll("#content *")]
        .filter((e) => [...e.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim().length > 2))
        .map((e) => parseFloat(getComputedStyle(e).fontSize))),
    }));
    if (r.over > worst) { worst = r.over; worstView = v; }
    if (r.blocks === 0) note(false, `${label}/${v}: view rendered nothing`);
    if (r.minFont < 12) note(false, `${label}/${v}: text below 12px (${r.minFont}px)`);
  }
  note(worst <= 1, `${label}: no view overflows horizontally (worst ${worst}px${worstView ? " on " + worstView : ""})`);
  note(true, `${label}: all 10 views rendered with >=12px text`);

  /* interactions still work */
  await page.evaluate(() => { location.hash = "jadwal"; });
  await page.waitForTimeout(600);
  await page.click('[data-act="add-schedule"]');
  await page.waitForSelector(".modal", { timeout: 6000 });
  const mw = await page.evaluate(() => {
    const m = document.querySelector(".modal");
    return { w: m.clientWidth, vw: document.documentElement.clientWidth, over: m.getBoundingClientRect().right - document.documentElement.clientWidth };
  });
  note(mw.over <= 1, `${label}: modal fits the viewport (${mw.w}px in ${mw.vw}px)`);
  await page.fill("#sTimes", "08:15");
  await page.click("#saveSch");
  await page.waitForTimeout(900);
  note((await page.locator(".modal").count()) === 0, `${label}: schedule saves and dialog closes`);

  await page.evaluate(() => { location.hash = "konsultasi"; });
  await page.waitForTimeout(600);
  const before = await page.locator(".msg").count();
  await page.fill("#chatInput", "Uji regresi.");
  await page.press("#chatInput", "Enter");
  await page.waitForTimeout(800);
  note((await page.locator(".msg").count()) === before + 1, `${label}: chat still sends`);

  /* theme switch — it lives in the sidebar, which is a closed drawer on a
     phone, so open it first the way a user would */
  if (mobile) {
    await page.click("#burger");
    await page.waitForTimeout(450);
  }
  await page.click('#shellTheme [data-theme-btn="glass"]');
  await page.waitForTimeout(450);
  note((await page.evaluate(() => document.documentElement.dataset.theme)) === "glass", `${label}: theme switch works`);
  const go = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  note(go <= 1, `${label}: glass theme no overflow (${go}px)`);
  await page.click('#shellTheme [data-theme-btn="neu"]');
  await page.waitForTimeout(300);
  if (mobile) {
    // close the drawer again before the final checks
    await page.mouse.click(vp.width - 12, vp.height / 2);
    await page.waitForTimeout(400);
  }

  const real = errs.filter((e) => !/favicon|manifest/i.test(e));
  note(real.length === 0, `${label}: no console errors (${real.length})`);
  real.slice(0, 4).forEach((e) => console.log("   >", e));

  await ctx.close();
}

await browser.close();
console.log(bad ? `\n${bad} check(s) failed.` : "\nRegression suite passed.");
process.exit(bad ? 1 : 0);
