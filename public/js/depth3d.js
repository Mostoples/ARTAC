/* ============================================================
   ARTA-C - lapisan "Depth 3D"
   - kartu miring 3D mengikuti pointer
   - digital twin three.js (model asli artac.glb) di elemen .twin3d
     dan di layar login; satu renderer dipakai ulang (app me-render
     ulang innerHTML, jadi kanvas dipindahkan, bukan dibuat ulang)
   ============================================================ */
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";

const BASE = "showcase/";
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;

/* ---------- kemiringan kartu ---------- */
let hot = null;
addEventListener("pointermove", (e) => {
  const c = e.target.closest?.(".card");
  if (hot && hot !== c) { hot.style.removeProperty("--rx"); hot.style.removeProperty("--ry"); hot.classList.remove("d3-hot"); hot = null; }
  if (!c || reduce || e.target.closest("input,select,textarea,table,.twin3d,canvas")) return;
  const r = c.getBoundingClientRect();
  if (r.width > 900) return;                            // kartu lebar dibiarkan tenang
  const x = (e.clientX - r.left) / r.width - 0.5, y = (e.clientY - r.top) / r.height - 0.5;
  c.style.setProperty("--ry", `${(x * 7).toFixed(2)}deg`);
  c.style.setProperty("--rx", `${(-y * 7).toFixed(2)}deg`);
  c.classList.add("d3-hot"); hot = c;
}, { passive: true });

/* ---------- digital twin ---------- */
let T = null, loading = null;

async function ensureTwin() {
  if (T) return T;
  if (loading) return loading;
  loading = (async () => {
    const M = await (await fetch(BASE + "artac.json")).json();
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.shadowMap.enabled = true;
    const scene = new THREE.Scene();
    scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;
    const cam = new THREE.PerspectiveCamera(30, 1, 0.05, 50);
    const key = new THREE.DirectionalLight(0xffffff, 2.1); key.position.set(-2.5, 4, 3.5); key.castShadow = true;
    key.shadow.mapSize.set(1024, 1024); scene.add(key);
    const rim = new THREE.DirectionalLight(0x8cc6ff, 1.5); rim.position.set(3, 1.5, -3); scene.add(rim);
    const ground = new THREE.Mesh(new THREE.PlaneGeometry(20, 20), new THREE.ShadowMaterial({ opacity: 0.14 }));
    ground.rotation.x = -Math.PI / 2; ground.position.y = -1.0; ground.receiveShadow = true; scene.add(ground);
    const root = new THREE.Group();
    root.rotation.x = -Math.PI / 2; root.scale.setScalar(0.01);
    root.position.set(-M.W / 2 * 0.01, -1.0, M.D / 2 * 0.01);
    const turn = new THREE.Group(); turn.add(root); scene.add(turn);
    const gltf = await new GLTFLoader().loadAsync(BASE + "artac.glb");
    root.add(gltf.scene);
    const nodes = {};
    gltf.scene.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.material = o.material.clone(); } if (o.name) nodes[o.name] = o; });
    const screen = nodes.layar;
    if (screen) { screen.material.side = THREE.DoubleSide; screen.material.emissive = new THREE.Color(1, 1, 1); }
    const tl = new THREE.TextureLoader(), tex = {};
    for (const n of ["home", "missed", "boot", "done"]) {
      tex[n] = tl.load(`${BASE}${n}@3x.png`); tex[n].colorSpace = THREE.SRGBColorSpace; tex[n].flipY = false;
    }
    const caps = Object.values(nodes).filter((o) => o.isMesh && o.name.startsWith("wadah_kaplet_"))
      .sort((a, b) => a.name.slice(-1) - b.name.slice(-1) || a.name.slice(-2, -1) - b.name.slice(-2, -1));
    for (const o of Object.values(nodes)) if (o.isMesh && o.name.startsWith("wadah_")) o.position.z = M.CB_EJ - M.CB1;
    T = { renderer, scene, cam, turn, nodes, screen, tex, caps, host: null, t0: performance.now(), shown: "" };
    loop();
    return T;
  })();
  return loading;
}

function setScreen(n) {
  if (!T.screen || T.shown === n) return;
  T.screen.material.map = T.tex[n]; T.screen.material.emissiveMap = T.tex[n]; T.screen.material.needsUpdate = true; T.shown = n;
}

function loop() {
  requestAnimationFrame(loop);
  if (!T || !T.host || !T.host.isConnected) return;
  const r = T.host.getBoundingClientRect();
  if (r.bottom < 0 || r.top > innerHeight || r.width < 10) return;
  const w = Math.round(r.width), h = Math.round(r.height);
  if (T.renderer.domElement.width !== Math.round(w * T.renderer.getPixelRatio())) { T.renderer.setSize(w, h, false); }
  T.cam.aspect = w / h; T.cam.updateProjectionMatrix();
  const t = (performance.now() - T.t0) / 1000;
  const mini = T.host.classList.contains("mini"), auth = T.host.classList.contains("auth-twin");
  T.turn.rotation.y = reduce ? -0.45 : -0.45 + Math.sin(t * 0.35) * 0.55;
  const d = auth ? 9.0 : mini ? 5.4 : 4.3;
  T.cam.position.set(d * 0.42, auth ? 1.7 : 1.2, d);
  T.cam.lookAt(auth ? 0.15 : 0, auth ? 0.55 : 0.4, 0);
  T.renderer.render(T.scene, T.cam);
}

function applyData(host) {
  const ds = host.dataset;
  const left = Math.max(0, Math.min(28, Number(ds.left ?? 28)));
  T.caps.forEach((c, i) => { c.visible = i >= 28 - left; });
  setScreen(ds.online === "0" ? "missed" : "home");
  let chips = host.querySelector(".twin-chips");
  if (!chips && !host.classList.contains("auth-twin")) {
    chips = document.createElement("div"); chips.className = "twin-chips"; host.appendChild(chips);
    const tag = document.createElement("div"); tag.className = "twin-tag"; tag.textContent = "Digital twin · live"; host.appendChild(tag);
  }
  const sig = [ds.batt, ds.temp, ds.pills, ds.online, left].join("|");
  if (chips && chips.dataset.sig !== sig) {
    chips.dataset.sig = sig;
    chips.innerHTML = `<span><img src="${BASE}ikon/baterai.png" alt="">${ds.batt ?? "-"}%</span>` +
      `<span><img src="${BASE}ikon/termometer.png" alt="">${ds.temp ?? "-"}°C</span>` +
      `<span><img src="${BASE}ikon/blister.png" alt="">${ds.pills ?? left} butir</span>` +
      `<span>${ds.online === "0" ? "● offline" : "● online"}</span>`;
  }
}

async function place() {
  let host = document.querySelector(".twin3d");
  const authOpen = !document.getElementById("authView")?.classList.contains("hidden");
  if (!host && authOpen && innerWidth >= 1100) {
    host = document.querySelector(".auth-twin");
    if (!host) { host = document.createElement("div"); host.className = "auth-twin"; host.dataset.left = "19"; document.body.prepend(host); }
  } else if (!authOpen) document.querySelector(".auth-twin")?.remove();
  if (!host) { if (T) T.host = null; return; }
  if (!host.querySelector("canvas") && !T) { const l = document.createElement("div"); l.className = "twin-load"; l.textContent = "Memuat model 3D…"; host.appendChild(l); }
  try { await ensureTwin(); } catch (e) { console.warn("twin3d", e); return; }
  host.querySelector(".twin-load")?.remove();
  if (T.renderer.domElement.parentNode !== host) host.prepend(T.renderer.domElement);
  T.host = host;
  applyData(host);
}

let pend = 0;
new MutationObserver(() => { cancelAnimationFrame(pend); pend = requestAnimationFrame(place); })
  .observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ["class"] });
place();
