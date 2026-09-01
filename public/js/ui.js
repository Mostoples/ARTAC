/* ============================================================
   ARTA-C — shared UI helpers (no framework)
   ============================================================ */

/** Escapes text before it is placed into innerHTML. */
export function esc(v) {
  return String(v ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

export const $ = (sel, root = document) => root.querySelector(sel);
export const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

export function el(tag, attrs = {}, html = "") {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") n.className = v;
    else if (k === "dataset") Object.assign(n.dataset, v);
    else if (k.startsWith("on") && typeof v === "function") n.addEventListener(k.slice(2), v);
    else if (v !== null && v !== undefined) n.setAttribute(k, v);
  }
  if (html) n.innerHTML = html;
  return n;
}

/* ---------------- icons (inline, currentColor) ---------------- */
const ICONS = {
  dashboard: '<path d="M3 3h8v8H3zM13 3h8v5h-8zM13 10h8v11h-8zM3 13h8v8H3z"/>',
  pill: '<path d="M10.5 3.5a5 5 0 0 1 7 7l-7 7a5 5 0 0 1-7-7Z"/><path d="M7 7l10 10"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  bell: '<path d="M18 8a6 6 0 1 0-12 0c0 7-3 8-3 8h18s-3-1-3-8"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/>',
  video: '<path d="m22 8-6 4 6 4V8Z"/><rect x="2" y="6" width="14" height="12" rx="2"/>',
  chat: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2Z"/>',
  chart: '<path d="M3 3v18h18"/><path d="M7 15l4-5 3 3 4-6"/>',
  users: '<path d="M16 21v-2a4 4 0 0 0-8 0v2"/><circle cx="12" cy="7" r="4"/>',
  box: '<path d="M21 8 12 3 3 8v8l9 5 9-5Z"/><path d="M3 8l9 5 9-5"/><path d="M12 13v8"/>',
  thermo: '<path d="M14 14.8V4a2 2 0 1 0-4 0v10.8a4 4 0 1 0 4 0Z"/>',
  motion: '<circle cx="12" cy="4.5" r="2"/><path d="M12 8v5l4 3"/><path d="M12 13l-3 3-1 4"/><path d="M9 10 5 9"/>',
  alert: '<path d="M12 3 2 20h20L12 3Z"/><path d="M12 9v5"/><path d="M12 17h.01"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  x: '<path d="M18 6 6 18"/><path d="M6 6l12 12"/>',
  plus: '<path d="M12 5v14"/><path d="M5 12h14"/>',
  logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5"/><path d="M21 12H9"/>',
  refresh: '<path d="M21 12a9 9 0 1 1-3-6.7L21 8"/><path d="M21 3v5h-5"/>',
  send: '<path d="m22 2-7 20-4-9-9-4Z"/>',
  doc: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8Z"/><path d="M14 3v5h5"/>',
  stetho: '<path d="M6 3v6a5 5 0 0 0 10 0V3"/><path d="M11 14v3a4 4 0 0 0 8 0v-2"/><circle cx="19" cy="12" r="2"/>',
  shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/>',
  wifi: '<path d="M5 12.5a10 10 0 0 1 14 0"/><path d="M8.5 16a5.5 5.5 0 0 1 7 0"/><path d="M12 20h.01"/>',
  battery: '<rect x="2" y="7" width="17" height="10" rx="2"/><path d="M22 11v2"/>',
  menu: '<path d="M4 6h16"/><path d="M4 12h16"/><path d="M4 18h16"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-2.7 1.1V21a2 2 0 1 1-4 0v-.1A1.6 1.6 0 0 0 7.5 19l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1A1.6 1.6 0 0 0 3 13.6H3a2 2 0 1 1 0-4h.1A1.6 1.6 0 0 0 4.7 7l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1A1.6 1.6 0 0 0 10 4.6V4a2 2 0 1 1 4 0v.1a1.6 1.6 0 0 0 2.7 1.1l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0 1.1 2.7H21a2 2 0 1 1 0 4h-.1a1.6 1.6 0 0 0-1.5 1"/>',
  temp: '<path d="M14 14.8V4a2 2 0 1 0-4 0v10.8a4 4 0 1 0 4 0Z"/>',
  phone: '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.2a2 2 0 0 1 2.1-.5c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2Z"/>',
  eye: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>',
};

/**
 * Inline SVG icon.
 * @param {keyof typeof ICONS} name
 * @param {number} size
 */
export function icon(name, size = 18) {
  const body = ICONS[name] || ICONS.box;
  return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
    aria-hidden="true" focusable="false">${body}</svg>`;
}

/* ---------------- toasts ---------------- */
function toastHost() {
  let h = document.getElementById("toasts");
  if (!h) {
    h = el("div", { id: "toasts", class: "toasts", role: "status", "aria-live": "polite" });
    document.body.appendChild(h);
  }
  return h;
}

/**
 * @param {string} msg
 * @param {"info"|"ok"|"err"|"warn"} kind
 */
export function toast(msg, kind = "info", ms = 3800) {
  const t = el("div", { class: `toast ${kind}` }, `<div>${esc(msg)}</div>`);
  toastHost().appendChild(t);
  setTimeout(() => {
    t.classList.add("out");
    setTimeout(() => t.remove(), 280);
  }, ms);
  return t;
}

/* ---------------- modal ---------------- */
/**
 * Opens a modal dialog. Returns a close() function.
 * @param {{title:string, body:string, footer?:string, wide?:boolean, onMount?:(root:HTMLElement, close:()=>void)=>void}} opts
 */
export function modal({ title, body, footer = "", wide = false, onMount }) {
  const prevFocus = document.activeElement;
  const back = el("div", { class: "backdrop", role: "presentation" });
  const box = el("div", {
    class: `modal${wide ? " wide" : ""}`,
    role: "dialog",
    "aria-modal": "true",
    "aria-label": title,
  }, `
    <div class="card-head">
      <h3>${esc(title)}</h3>
      <button class="btn btn-icon btn-ghost" data-close aria-label="Tutup dialog">${icon("x", 16)}</button>
    </div>
    <div data-body>${body}</div>
    ${footer ? `<div class="row between mt-4" data-footer>${footer}</div>` : ""}
  `);
  back.appendChild(box);
  document.body.appendChild(back);
  document.body.style.overflow = "hidden";

  const close = () => {
    back.remove();
    document.body.style.overflow = "";
    document.removeEventListener("keydown", onKey);
    if (prevFocus instanceof HTMLElement) prevFocus.focus();
  };
  function onKey(e) {
    if (e.key === "Escape") close();
    if (e.key === "Tab") trapFocus(e, box);
  }
  document.addEventListener("keydown", onKey);
  back.addEventListener("mousedown", (e) => { if (e.target === back) close(); });
  box.querySelectorAll("[data-close]").forEach((b) => b.addEventListener("click", close));

  onMount?.(box, close);
  const first = box.querySelector("input, select, textarea, button:not([data-close])");
  (first instanceof HTMLElement ? first : box.querySelector("[data-close]"))?.focus();
  return close;
}

function trapFocus(e, root) {
  const f = $$(
    'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
    root
  ).filter((n) => n.offsetParent !== null);
  if (!f.length) return;
  const first = f[0], last = f[f.length - 1];
  if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
  else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
}

/** Confirmation dialog resolving to a boolean. */
export function confirmDialog(title, message, confirmLabel = "Ya, lanjutkan") {
  return new Promise((resolve) => {
    let settled = false;
    const finish = (v, close) => { if (settled) return; settled = true; close(); resolve(v); };
    modal({
      title,
      body: `<p class="soft mb-0">${esc(message)}</p>`,
      footer: `
        <button class="btn btn-ghost" data-no>Batal</button>
        <button class="btn btn-primary" data-yes>${esc(confirmLabel)}</button>`,
      onMount(root, close) {
        root.querySelector("[data-no]").addEventListener("click", () => finish(false, close));
        root.querySelector("[data-yes]").addEventListener("click", () => finish(true, close));
        // dismissal via Escape or backdrop click resolves as "cancel"
        const back = root.parentElement;
        new MutationObserver((_, obs) => {
          if (!document.body.contains(back)) { obs.disconnect(); if (!settled) { settled = true; resolve(false); } }
        }).observe(document.body, { childList: true });
      },
    });
  });
}

/* ---------------- charts ---------------- */
/** Radial adherence gauge markup. `pct` 0..100 */
export function gauge(pct) {
  const p = Math.max(0, Math.min(100, Number(pct) || 0));
  const r = 62, c = 2 * Math.PI * r;
  const off = c * (1 - p / 100);
  return `
    <div class="gauge" role="img" aria-label="Kepatuhan ${p} persen">
      <svg viewBox="0 0 148 148">
        <defs>
          <linearGradient id="gaugeGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#67e8f9"/><stop offset="100%" stop-color="#0891b2"/>
          </linearGradient>
        </defs>
        <circle class="track-c" cx="74" cy="74" r="${r}"/>
        <circle class="val-c" cx="74" cy="74" r="${r}"
          stroke-dasharray="${c.toFixed(1)}" stroke-dashoffset="${off.toFixed(1)}"/>
      </svg>
      <div class="cap"><b>${p}%</b><span>Kepatuhan</span></div>
    </div>`;
}

/** 7-day bar chart. `data` = [{label, pct, miss}] */
export function bars(data) {
  return `<div class="bars" role="img" aria-label="Grafik kepatuhan harian">
    ${data.map((d) => `
      <div class="b ${d.miss ? "miss" : ""}">
        <i style="height:${Math.max(4, d.pct)}%"></i>
        <span>${esc(d.label)}</span>
      </div>`).join("")}
  </div>`;
}

/** Sparkline from an array of numbers. */
export function spark(values, w = 260, h = 56) {
  const v = values.length ? values : [0, 0];
  const max = Math.max(...v), min = Math.min(...v);
  const span = max - min || 1;
  const step = w / Math.max(1, v.length - 1);
  const pts = v.map((n, i) => [i * step, h - 4 - ((n - min) / span) * (h - 12)]);
  const line = pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(" ");
  const area = `${line} L${w} ${h} L0 ${h} Z`;
  return `<svg class="spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true">
    <path class="area" d="${area}"/><path class="line" d="${line}"/></svg>`;
}

/* ---------------- formatting ---------------- */
const DAYS = ["Min", "Sen", "Sel", "Rab", "Kam", "Jum", "Sab"];
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"];

export function toDate(v) {
  if (!v) return null;
  if (v instanceof Date) return v;
  if (typeof v?.toDate === "function") return v.toDate();
  if (typeof v === "number") return new Date(v);
  const d = new Date(v);
  return isNaN(d) ? null : d;
}

export function fmtTime(v) {
  const d = toDate(v);
  return d ? `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}` : "--:--";
}

export function fmtDate(v) {
  const d = toDate(v);
  return d ? `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}` : "-";
}

export function fmtDateTime(v) {
  const d = toDate(v);
  return d ? `${DAYS[d.getDay()]}, ${fmtDate(d)} · ${fmtTime(d)}` : "-";
}

export function relTime(v) {
  const d = toDate(v);
  if (!d) return "-";
  const s = Math.round((Date.now() - d.getTime()) / 1000);
  if (Math.abs(s) < 60) return "baru saja";
  const m = Math.round(s / 60);
  if (Math.abs(m) < 60) return m > 0 ? `${m} menit lalu` : `dalam ${-m} menit`;
  const h = Math.round(m / 60);
  if (Math.abs(h) < 24) return h > 0 ? `${h} jam lalu` : `dalam ${-h} jam`;
  const dy = Math.round(h / 24);
  if (Math.abs(dy) < 30) return dy > 0 ? `${dy} hari lalu` : `dalam ${-dy} hari`;
  return fmtDate(d);
}

export function initials(name) {
  return String(name || "?")
    .trim().split(/\s+/).slice(0, 2)
    .map((w) => w[0]?.toUpperCase() || "")
    .join("") || "?";
}

/** Renders an empty-state block. */
export function emptyState(text, iconName = "doc") {
  return `<div class="empty">${icon(iconName, 28)}<div>${esc(text)}</div></div>`;
}

/** Small inline loading row. */
export function skeletonRows(n = 3) {
  return `<div class="col">${Array.from({ length: n }, () =>
    '<div class="skel" style="height:46px"></div>').join("")}</div>`;
}
