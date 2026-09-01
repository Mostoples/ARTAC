/* ============================================================
   ARTA-C — motion helpers
   Scroll reveal, counters, gauge/scroll progress, pointer tilt.
   Everything degrades safely: if this module never runs, the CSS
   keeps all content visible because the hiding rule is gated on
   the .js-anim class added here.
   ============================================================ */

const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/** Marks the document as animation-capable, enabling reveal rules. */
export function enableAnim() {
  if (reduced) return;
  document.documentElement.classList.add("js-anim");

  // Failsafe: content must never stay hidden because of a motion bug.
  // If anything is still un-revealed a few seconds in, show it.
  setTimeout(() => {
    document.querySelectorAll("[data-reveal]:not(.in)").forEach((n) => n.classList.add("in", "instant"));
  }, 4000);
}

/* ---------------- scroll reveal ---------------- */
let io = null;
const watched = new Set();
let sweepQueued = false;

/**
 * Reveals anything at or above the fold.
 *
 * An IntersectionObserver only reports elements whose intersection
 * state actually changes. Jumping down the page instantly (anchor
 * link, End key, a restored scroll position) moves elements from
 * "below the viewport" to "above the viewport" without ever
 * intersecting it, so they would stay hidden forever. This sweep
 * closes that gap.
 */
function sweep() {
  sweepQueued = false;
  const h = window.innerHeight;
  for (const n of [...watched]) {
    const r = n.getBoundingClientRect();
    if (r.top < h * 0.92) reveal(n);
  }
}

function reveal(n) {
  n.classList.add("in");
  watched.delete(n);
  io?.unobserve(n);
  if (!watched.size) removeEventListener("scroll", onScroll);
}

function onScroll() {
  if (sweepQueued) return;
  sweepQueued = true;
  requestAnimationFrame(sweep);
}

/**
 * Observes [data-reveal] elements inside `root` and plays them in
 * as they enter the viewport.
 */
export function observeReveal(root = document) {
  const items = root.querySelectorAll("[data-reveal]:not(.in)");
  if (!items.length) return;

  if (reduced) {
    items.forEach((n) => n.classList.add("in", "instant"));
    return;
  }

  if (!io) {
    io = new IntersectionObserver((entries) => {
      for (const e of entries) {
        // reveal on entry, and also once the element has passed above
        if (e.isIntersecting || e.boundingClientRect.bottom < 0) reveal(e.target);
      }
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
  }

  items.forEach((n, i) => {
    // stagger siblings that share a parent
    if (!n.style.getPropertyValue("--i")) n.style.setProperty("--i", String(i % 8));
    watched.add(n);
    io.observe(n);
  });

  addEventListener("scroll", onScroll, { passive: true });
  onScroll();
}

/** Reveals immediately, without waiting for scroll (above-the-fold). */
export function revealNow(root = document) {
  root.querySelectorAll("[data-reveal]").forEach((n) => n.classList.add("in"));
}

/* ---------------- number counters ---------------- */
/**
 * Animates elements carrying data-count="<number>" from 0 to target.
 * Honors an optional data-suffix.
 */
export function countUp(root = document, ms = 900) {
  root.querySelectorAll("[data-count]").forEach((n) => {
    const target = parseFloat(n.dataset.count);
    if (!isFinite(target)) return;
    const suffix = n.dataset.suffix || "";
    const dec = (n.dataset.count.split(".")[1] || "").length;

    if (reduced) { n.textContent = target.toFixed(dec) + suffix; return; }

    const t0 = performance.now();
    const step = (t) => {
      const p = Math.min(1, (t - t0) / ms);
      const eased = 1 - Math.pow(1 - p, 3);
      n.textContent = (target * eased).toFixed(dec) + suffix;
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  });
}

/* ---------------- scroll progress bar ---------------- */
export function scrollProgress() {
  if (reduced) return;
  const bar = document.createElement("div");
  bar.className = "scroll-prog";
  document.body.appendChild(bar);

  let queued = false;
  const update = () => {
    const h = document.documentElement;
    const max = h.scrollHeight - h.clientHeight;
    bar.style.transform = `scaleX(${max > 0 ? h.scrollTop / max : 0})`;
    queued = false;
  };
  addEventListener("scroll", () => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(update);
  }, { passive: true });
  update();
}

/* ---------------- pointer tilt ---------------- */
/** Subtle 3D tilt following the cursor. Skipped on touch devices. */
export function tilt(node, max = 7) {
  if (!node || reduced || !matchMedia("(hover: hover)").matches) return;

  const onMove = (e) => {
    const r = node.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width - 0.5;
    const y = (e.clientY - r.top) / r.height - 0.5;
    node.style.transform =
      `perspective(900px) rotateY(${x * max}deg) rotateX(${-y * max}deg) translateZ(0)`;
  };
  const onLeave = () => {
    node.style.transform = "";
  };

  node.addEventListener("pointermove", onMove);
  node.addEventListener("pointerleave", onLeave);
}

/* ---------------- gauge / bar replay ---------------- */
/**
 * Restarts CSS animations inside a freshly injected subtree.
 * Needed because re-setting innerHTML does not always retrigger
 * animations for identical markup.
 */
export function replay(root) {
  if (reduced || !root) return;
  root.querySelectorAll(".bars .b i, .bar > i, .spark path").forEach((n) => {
    n.style.animation = "none";
    // reading offsetWidth forces a reflow so the animation can restart
    void n.offsetWidth;
    n.style.animation = "";
  });
}

/** Animates a gauge's stroke from empty to its final offset. */
export function animateGauge(root) {
  const c = root?.querySelector(".gauge .val-c");
  if (!c) return;
  const to = c.getAttribute("stroke-dashoffset");
  const total = c.getAttribute("stroke-dasharray");
  if (reduced) return;
  c.setAttribute("stroke-dashoffset", total);
  requestAnimationFrame(() => {
    requestAnimationFrame(() => c.setAttribute("stroke-dashoffset", to));
  });
}

/** Shakes a node to signal a rejected input. */
export function shake(node) {
  if (!node || reduced) return;
  node.classList.remove("shake");
  void node.offsetWidth;
  node.classList.add("shake");
  setTimeout(() => node.classList.remove("shake"), 420);
}
