/* ============================================================
   ARTA-C — theme controller
   Two visual languages: "neu" (neumorphism) and "glass"
   (glassmorphism). Choice is stored per-browser.
   ============================================================ */

const KEY = "artac.theme";
const THEMES = ["neu", "glass"];
const DEFAULT = "neu";

export function getTheme() {
  const t = localStorage.getItem(KEY);
  return THEMES.includes(t) ? t : DEFAULT;
}

export function setTheme(name) {
  const t = THEMES.includes(name) ? name : DEFAULT;
  document.documentElement.setAttribute("data-theme", t);
  localStorage.setItem(KEY, t);

  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute("content", t === "glass" ? "#04212b" : "#e8f3f6");

  document.querySelectorAll("[data-theme-btn]").forEach((b) => {
    b.setAttribute("aria-selected", String(b.dataset.themeBtn === t));
  });
  document.dispatchEvent(new CustomEvent("themechange", { detail: { theme: t } }));
  return t;
}

export function toggleTheme() {
  return setTheme(getTheme() === "neu" ? "glass" : "neu");
}

/** Applies the stored theme as early as possible to avoid a flash. */
export function initTheme() {
  return setTheme(getTheme());
}

/**
 * Renders a segmented control for switching themes into `host`.
 * @param {HTMLElement} host
 */
export function mountThemeSwitch(host) {
  if (!host) return;
  host.classList.add("theme-switch");
  host.innerHTML = `
    <div class="seg" role="tablist" aria-label="Pilih tema tampilan">
      <button type="button" role="tab" data-theme-btn="neu" aria-selected="false" title="Tema Neumorphism">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="3.5"/>
        </svg><span>Neumorf</span>
      </button>
      <button type="button" role="tab" data-theme-btn="glass" aria-selected="false" title="Tema Glassmorphism">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <path d="M5 4h14l-2 6a5 5 0 0 1-10 0Z"/><path d="M12 16v4"/><path d="M8 20h8"/>
        </svg><span>Glass</span>
      </button>
    </div>`;
  host.querySelectorAll("[data-theme-btn]").forEach((btn) => {
    btn.addEventListener("click", () => setTheme(btn.dataset.themeBtn));
  });
  setTheme(getTheme());
}
