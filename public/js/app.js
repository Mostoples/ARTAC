/* ============================================================
   ARTA-C — application controller
   Handles auth flow, live subscriptions, routing, and actions.
   ============================================================ */

import * as be from "./backend.js";
import * as V from "./views.js";
import { setDemoMode } from "./firebase-config.js";
import { mountThemeSwitch } from "./theme.js";
import {
  enableAnim, revealNow, countUp, replay, animateGauge, shake,
} from "./anim.js";
import {
  $, $$, esc, icon, toast, modal, confirmDialog,
  initials, toDate, fmtTime,
} from "./ui.js";
import {
  createSimulator, escalationFor, deviceIssues, adherenceOf,
} from "./logic.js";

/* ---------------- state ---------------- */
const state = {
  profile: null,
  patients: [],
  activeId: null,
  patient: null,
  device: null,
  schedules: [],
  logs: [],
  alerts: [],
  complaints: [],
  messages: [],
  vots: [],
  allLogs: [],
  allAlerts: [],
  allDevices: [],
  view: "ringkasan",
};

/* Module-level mutable state. Declared up here because the auth
   callback below can fire before the rest of the file finishes
   evaluating; `let` bindings declared later would still be in their
   temporal dead zone at that point. */
let subs = [];          // per-patient subscriptions
let globalSubs = [];    // cohort-wide subscriptions
let paintedView = null; // last fully-choreographed view, so live data repaints stay calm
let raf = null;         // pending render frame
let sim = null;
let camStream = null;
let recTimer = null;
let recStart = 0;

const stopAll = (list) => { list.forEach((f) => { try { f(); } catch { /* already detached */ } }); return []; };

/* ---------------- nav definition ---------------- */
const NAV = {
  ringkasan:  { label: "Ringkasan",   icon: "dashboard", render: V.overview, roles: ["dokter", "pmo", "pasien"] },
  pasien:     { label: "Pasien",      icon: "users",     render: V.cohort,   roles: ["dokter", "pmo"] },
  jadwal:     { label: "Jadwal & Ceklist", icon: "pill", render: V.schedule, roles: ["dokter", "pmo", "pasien"] },
  perangkat:  { label: "Kotak Obat",  icon: "box",       render: V.deviceView, roles: ["dokter", "pmo", "pasien"] },
  peringatan: { label: "Peringatan",  icon: "bell",      render: V.alertsView, roles: ["dokter", "pmo", "pasien"] },
  vot:        { label: "Video (VOT)", icon: "video",     render: V.votView,  roles: ["dokter", "pmo", "pasien"] },
  keluhan:    { label: "Keluhan",     icon: "doc",       render: V.complaintsView, roles: ["dokter", "pmo", "pasien"] },
  konsultasi: { label: "Konsultasi",  icon: "chat",      render: V.chatView, roles: ["dokter", "pmo", "pasien"] },
  laporan:    { label: "Laporan",     icon: "chart",     render: V.reportView, roles: ["dokter", "pmo", "pasien"] },
  profil:     { label: "Profil",      icon: "settings",  render: V.profileView, roles: ["dokter", "pmo", "pasien"] },
};

/* ============================================================
   AUTH SCREEN
   ============================================================ */
enableAnim();
mountThemeSwitch($("#authTheme"));

const DEMO_ROLES = [
  { role: "dokter", email: "dokter@artac.id", label: "Dokter", ic: "stetho",
    desc: "Kelola pasien, dosis, dan jadwal" },
  { role: "pmo", email: "pmo@artac.id", label: "Pengawas", ic: "users",
    desc: "Pantau kepatuhan dan verifikasi VOT" },
  { role: "pasien", email: "pasien@artac.id", label: "Pasien", ic: "shield",
    desc: "Pengingat, VOT, dan keluhan" },
];

$("#demoBox").innerHTML = be.isDemo
  ? `<div class="row mb-4"><span class="tile-icon">${icon("eye", 18)}</span>
      <div class="grow"><b class="small">Mode pratinjau aktif</b>
      <div class="tiny muted">Data contoh tersimpan di peramban ini, tidak menyentuh Firestore.
      Pilih peran untuk langsung masuk.</div></div></div>
     <div class="col" id="demoRoles">
       ${DEMO_ROLES.map((r) => `
         <button class="btn btn-ghost btn-block" data-demo-role="${r.role}" style="justify-content:flex-start">
           ${icon(r.ic, 16)}
           <span class="grow" style="text-align:left">Masuk sebagai <b>${r.label}</b>
             <span class="tiny muted" style="display:block;font-weight:400">${esc(r.desc)}</span></span>
         </button>`).join("")}
     </div>
     <hr class="divider">
     <div class="row wrapx">
       <button class="btn btn-sm btn-ghost grow" id="resetDemo">Setel ulang data</button>
       <button class="btn btn-sm btn-ghost grow" id="exitDemo">Keluar mode pratinjau</button>
     </div>`
  : `<div class="row mb-4"><span class="tile-icon">${icon("shield", 18)}</span>
      <div class="grow"><b class="small">Terhubung ke Firebase</b>
      <div class="tiny muted">Data tersimpan pada proyek ARTA-C. Belum punya akun? Gunakan tab
      <b>Daftar</b>, atau coba dulu dengan data contoh tanpa mendaftar.</div></div></div>
     <button class="btn btn-primary btn-block" id="enterDemo">
       ${icon("eye", 16)} Coba mode pratinjau (tanpa daftar)
     </button>`;

$("#enterDemo")?.addEventListener("click", () => setDemoMode(true));

$("#exitDemo")?.addEventListener("click", async () => {
  if (await confirmDialog("Keluar mode pratinjau",
    "Aplikasi akan kembali memakai data Firebase. Data contoh tetap tersimpan di peramban.", "Keluar")) {
    setDemoMode(false);
  }
});

$("#resetDemo")?.addEventListener("click", async () => {
  if (await confirmDialog("Setel ulang data contoh",
    "Seluruh perubahan pada mode pratinjau akan dikembalikan ke data awal.", "Setel ulang")) {
    be.resetDemo();
    location.reload();
  }
});

/* one-click demo sign-in per role */
$("#demoRoles")?.addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-demo-role]");
  if (!btn) return;
  const entry = DEMO_ROLES.find((r) => r.role === btn.dataset.demoRole);
  const label = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<span class="grow" style="text-align:left">Menyiapkan sesi…</span>`;
  try {
    await be.signIn(entry.email, "demo1234");
  } catch (ex) {
    toast(friendlyAuthError(ex), "err", 5200);
    btn.disabled = false;
    btn.innerHTML = label;
  }
});

/* tab switching */
const tabLogin = $("#tabLogin"), tabReg = $("#tabReg");
tabLogin.addEventListener("click", () => switchTab(true));
tabReg.addEventListener("click", () => switchTab(false));
function switchTab(login) {
  tabLogin.setAttribute("aria-selected", String(login));
  tabReg.setAttribute("aria-selected", String(!login));
  $("#loginForm").classList.toggle("hidden", !login);
  $("#regForm").classList.toggle("hidden", login);
}

/* role-dependent extra field */
$$('#regForm input[name="role"]').forEach((r) => {
  r.addEventListener("change", () => {
    const role = $('#regForm input[name="role"]:checked').value;
    const wrap = $("#rgExtraWrap"), label = wrap.querySelector("label"), input = $("#rgExtra");
    wrap.classList.remove("hidden");
    if (role === "dokter") { label.textContent = "Rumah sakit / instansi"; input.placeholder = "RSUD Cendana"; }
    else if (role === "pmo") { label.textContent = "Hubungan dengan pasien"; input.placeholder = "Keluarga inti / kader"; }
    else { label.textContent = "Alamat"; input.placeholder = "Alamat tempat tinggal"; }
  });
});

/* login */
$("#loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = $("#loginBtn"), err = $("#loginErr");
  err.classList.add("hidden");
  btn.disabled = true; btn.textContent = "Memproses…";
  try {
    await be.signIn($("#liEmail").value, $("#liPass").value);
  } catch (ex) {
    err.textContent = friendlyAuthError(ex);
    err.classList.remove("hidden");
    shake($("#loginForm").closest(".card"));
  } finally {
    btn.disabled = false; btn.textContent = "Masuk";
  }
});

/* register */
$("#regForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = $("#regBtn"), err = $("#regErr");
  err.classList.add("hidden");
  const role = $('#regForm input[name="role"]:checked').value;
  const extraVal = $("#rgExtra").value.trim();
  const extra = { phone: $("#rgPhone").value.trim() };
  if (role === "dokter") extra.hospital = extraVal;
  else if (role === "pmo") extra.relation = extraVal;
  else extra.address = extraVal;

  btn.disabled = true; btn.textContent = "Mendaftarkan…";
  try {
    await be.signUp({
      name: $("#rgName").value.trim(),
      email: $("#rgEmail").value,
      password: $("#rgPass").value,
      role, extra,
    });
    toast("Akun berhasil dibuat.", "ok");
  } catch (ex) {
    err.textContent = friendlyAuthError(ex);
    err.classList.remove("hidden");
    shake($("#regForm").closest(".card"));
  } finally {
    btn.disabled = false; btn.textContent = "Daftar";
  }
});

function friendlyAuthError(ex) {
  const c = String(ex?.code || ex?.message || ex);
  if (c.includes("invalid-credential") || c.includes("wrong-password") || c.includes("user-not-found"))
    return "Email atau kata sandi tidak cocok.";
  if (c.includes("email-already-in-use")) return "Email sudah terdaftar. Silakan masuk.";
  if (c.includes("weak-password")) return "Kata sandi minimal 6 karakter.";
  if (c.includes("invalid-email")) return "Format email tidak valid.";
  if (c.includes("too-many-requests")) return "Terlalu banyak percobaan. Coba lagi beberapa saat.";
  if (c.includes("network")) return "Gangguan jaringan. Periksa koneksi Anda.";
  if (c.includes("configuration-not-found") || c.includes("operation-not-allowed"))
    return "Metode Email/Password belum diaktifkan pada Firebase Authentication.";
  if (c.includes("permission-denied") || c.includes("insufficient"))
    return "Akses ditolak oleh aturan keamanan. Pastikan firestore.rules sudah diterapkan.";
  return ex?.message || "Terjadi kesalahan. Coba lagi.";
}

/* ============================================================
   SESSION
   ============================================================ */
be.onAuth((profile) => {
  $("#boot").classList.add("hidden");
  state.profile = profile;

  if (!profile) {
    subs = stopAll(subs);
    globalSubs = stopAll(globalSubs);
    sim?.stop();
    $("#shell").classList.add("hidden");
    $("#authView").classList.remove("hidden");
    revealNow($("#authView"));
    return;
  }

  $("#authView").classList.add("hidden");
  $("#shell").classList.remove("hidden");
  paintedView = null;
  mountShell();
});

/* ============================================================
   SHELL
   ============================================================ */
function mountShell() {
  const p = state.profile;
  const roleLabel = { dokter: "Dokter", pmo: "Pengawas Minum Obat", pasien: "Pasien" }[p.role] || p.role;

  $("#whoCard").innerHTML = `
    <div class="row"><span class="avatar">${esc(initials(p.name))}</span>
      <div class="grow" style="min-width:0">
        <b class="small" style="display:block;overflow:hidden;text-overflow:ellipsis">${esc(p.name || p.email)}</b>
        <span class="tiny muted">${esc(roleLabel)}</span>
      </div></div>`;

  $("#simBadge").innerHTML = be.isDemo
    ? `<span class="badge warn">Mode pratinjau</span>`
    : `<span class="badge ok"><span class="dot ok live"></span>Firebase aktif</span>`;

  mountThemeSwitch($("#shellTheme"));
  renderNav({ animate: true });

  $("#patientPickWrap").classList.toggle("hidden", p.role === "pasien");

  globalSubs = stopAll(globalSubs);
  globalSubs.push(be.watchPatients(p, (list) => {
    state.patients = list.slice().sort((a, b) => String(a.name).localeCompare(String(b.name)));
    const pick = $("#patientPick");
    pick.innerHTML = state.patients.length
      ? state.patients.map((x) => `<option value="${esc(x.id)}">${esc(x.name)}</option>`).join("")
      : '<option value="">Belum ada pasien</option>';

    if (!state.activeId || !state.patients.some((x) => x.id === state.activeId))
      selectPatient(state.patients[0]?.id || null);
    else { pick.value = state.activeId; render(); }
  }));

  globalSubs.push(be.watchDoseLogsFor(p, (rows) => { state.allLogs = rows; render(); }));
  globalSubs.push(be.watchAlertsFor(p, (rows) => { state.allAlerts = rows; refreshBadges(); render(); }));
  globalSubs.push(be.watchDevicesFor(p, (rows) => { state.allDevices = rows; render(); }));

  $("#patientPick").onchange = (e) => selectPatient(e.target.value);

  startSimulator();
  route();
}

function renderNav({ animate = false } = {}) {
  const role = state.profile.role;
  const navEl = $("#sideNav");
  navEl.innerHTML = Object.entries(NAV)
    .filter(([, v]) => v.roles.includes(role))
    .map(([k, v]) => `
      <a href="#${k}" data-nav="${k}" class="${state.view === k ? "active" : ""}">
        ${icon(v.icon, 17)}<span>${esc(v.label)}</span>
        ${k === "peringatan" ? '<span class="count hidden" data-badge="alerts"></span>' : ""}
      </a>`).join("");

  if (animate) {
    navEl.classList.add("fresh");
    setTimeout(() => navEl.classList.remove("fresh"), 700);
  }
  refreshBadges();
}

function refreshBadges() {
  const n = state.allAlerts.filter((a) => !a.resolved).length;
  const el = document.querySelector('[data-badge="alerts"]');
  if (el) { el.textContent = n; el.classList.toggle("hidden", n === 0); }
}

function selectPatient(pid) {
  state.activeId = pid;
  subs = stopAll(subs);
  state.patient = null; state.device = null;
  state.schedules = []; state.logs = []; state.alerts = [];
  state.complaints = []; state.messages = []; state.vots = [];

  if (!pid) { render(); return; }
  const pick = $("#patientPick");
  if (pick) pick.value = pid;

  subs.push(be.watchPatient(pid, (p) => {
    state.patient = p;
    if (p?.deviceId) {
      subs.push(be.watchDevice(p.deviceId, (d) => { state.device = d; render(); }));
    }
    render();
  }));
  subs.push(be.watchSchedules(pid, (r) => { state.schedules = r; render(); }));
  subs.push(be.watchDoseLogs(pid, (r) => { state.logs = r; render(); }));
  subs.push(be.watchAlerts(pid, (r) => { state.alerts = r; render(); }));
  subs.push(be.watchComplaints(pid, (r) => { state.complaints = r; render(); }));
  subs.push(be.watchMessages(pid, (r) => { state.messages = r; render(); }));
  subs.push(be.watchVot(pid, (r) => { state.vots = r; render(); }));
}

/* ---------------- routing ---------------- */
function route() {
  const key = location.hash.replace("#", "") || "ringkasan";
  const nav = NAV[key];
  state.view = nav && nav.roles.includes(state.profile.role) ? key : "ringkasan";
  render();
}
window.addEventListener("hashchange", route);

function render() {
  if (!state.profile) return;
  cancelAnimationFrame(raf);
  raf = requestAnimationFrame(() => {
    const nav = NAV[state.view] || NAV.ringkasan;
    const isNavigation = paintedView !== state.view;

    $("#viewTitle").textContent = nav.label;
    $$("#sideNav a").forEach((a) => a.classList.toggle("active", a.dataset.nav === state.view));

    const host = $("#content");
    host.innerHTML = nav.render(state);

    // Live subscriptions repaint often. Full entrance choreography runs
    // only when the user actually navigates, so incoming telemetry does
    // not make the page flicker.
    const view = host.firstElementChild;
    if (view && !isNavigation) view.classList.add("quiet");

    if (isNavigation) {
      animateGauge(host);
      replay(host);
      countUp(host);
      paintedView = state.view;
    }

    afterRender();
  });
}

/* ---------------- sidebar (mobile) ---------------- */
$("#burger").innerHTML = icon("menu", 18);
$("#burger").addEventListener("click", () => toggleSidebar(true));
function toggleSidebar(open) {
  const sb = $("#sidebar");
  sb.classList.toggle("open", open);
  $("#burger").setAttribute("aria-expanded", String(open));
  let scrim = $("#scrim");
  if (open && !scrim) {
    scrim = document.createElement("div");
    scrim.id = "scrim"; scrim.className = "scrim";
    scrim.addEventListener("click", () => toggleSidebar(false));
    document.body.appendChild(scrim);
  } else if (!open) scrim?.remove();
}

$("#refreshBtn").addEventListener("click", () => { sim?.tick(); render(); toast("Data dimuat ulang.", "info", 1600); });

$("#logoutBtn").addEventListener("click", async () => {
  if (await confirmDialog("Keluar dari aplikasi", "Anda perlu masuk kembali untuk membuka dasbor.", "Keluar")) {
    stopCamera();
    await be.signOutUser();
  }
});

/* ============================================================
   ACTION DELEGATION
   ============================================================ */
document.addEventListener("click", (e) => {
  const nav = e.target.closest("[data-nav]");
  if (nav && !nav.matches("#sideNav a")) {
    e.preventDefault();
    location.hash = nav.dataset.nav;
    toggleSidebar(false);
    return;
  }
  if (e.target.closest("#sideNav a")) toggleSidebar(false);

  const btn = e.target.closest("[data-act]");
  if (!btn) return;
  const id = btn.dataset.id;
  const act = btn.dataset.act;
  handleAction(act, id, btn);
});

async function handleAction(act, id, btn) {
  const p = state.patient;
  try {
    switch (act) {
      case "add-patient": return patientDialog();
      case "edit-patient": return patientDialog(state.patients.find((x) => x.id === id));
      case "open-patient": selectPatient(id); location.hash = "ringkasan"; return;

      case "add-schedule": return scheduleDialog();
      case "edit-schedule": return scheduleDialog(state.schedules.find((x) => x.id === id));
      case "del-schedule":
        if (await confirmDialog("Hapus jadwal", "Jadwal dosis ini akan dihapus dari dispenser.", "Hapus")) {
          await be.deleteSchedule(p.id, id);
          toast("Jadwal dihapus.", "ok");
        }
        return;

      case "mark-dose": return markDoseDialog();
      case "confirm-dose":
        await be.updateDoseLog(id, { status: "taken", takenAt: Date.now(), method: "manual" });
        await consumePills(1);
        toast("Dosis ditandai diminum.", "ok");
        return;

      case "resolve-alert":
        await be.resolveAlert(id);
        toast("Peringatan ditandai selesai.", "ok");
        return;

      case "save-device": {
        const t = Number($("#setTemp").value);
        const pills = Number($("#setPills").value);
        await be.updateDevice(state.device.id, { targetTempC: t, pillsLeft: pills, refillDate: Date.now() });
        toast("Pengaturan perangkat disimpan.", "ok");
        return;
      }
      case "sim-press": {
        await be.updateDevice(state.device.id, {
          lidOpenCount: (state.device.lidOpenCount || 0) + 1,
          motionAt: Date.now(), alarmOn: false,
        });
        const pending = state.logs.find((l) => l.status === "pending" || l.status === "missed");
        if (pending) {
          const sched = toDate(pending.scheduledAt)?.getTime() || Date.now();
          const lateMin = Math.max(0, (Date.now() - sched) / 60000);
          await be.updateDoseLog(pending.id, {
            status: lateMin > 30 ? "late" : "taken", takenAt: Date.now(), method: "sensor",
          });
        }
        await consumePills(1);
        toast("Bungkus obat terbuka, respons pasien tercatat.", "ok");
        return;
      }
      case "sim-motion":
        await be.updateDevice(state.device.id, { motionAt: Date.now() });
        toast("Sensor gerakan terpicu.", "info");
        return;

      case "cam-start": return startCamera();
      case "cam-record": return startRecording();
      case "cam-stop": return finishRecording();
      case "vot-verify":
        await be.updateVot(id, { status: "verified", verifiedBy: state.profile.name });
        toast("Sesi VOT terverifikasi.", "ok");
        return;
      case "vot-reject":
        await be.updateVot(id, { status: "rejected", verifiedBy: state.profile.name });
        toast("Sesi VOT ditolak.", "warn");
        return;

      case "add-complaint": return complaintDialog();
      case "reply-complaint": return replyDialog(state.complaints.find((x) => x.id === id));

      case "print-report": window.print(); return;
      default: return;
    }
  } catch (ex) {
    toast(friendlyAuthError(ex), "err", 5200);
    if (btn) btn.disabled = false;
  }
}

async function consumePills(n) {
  const d = state.device;
  if (!d) return;
  const perIntake = state.schedules.find((s) => s.active !== false)?.dosePerIntake || n;
  await be.updateDevice(d.id, { pillsLeft: Math.max(0, (d.pillsLeft || 0) - perIntake) });
}

/* ============================================================
   DIALOGS
   ============================================================ */
function patientDialog(existing) {
  const isNew = !existing;
  const d = existing || {};
  modal({
    title: isNew ? "Pasien baru" : `Ubah data ${d.name}`,
    wide: true,
    body: `
      <form id="patForm" class="grid g-2">
        <div class="field"><label for="fName">Nama lengkap</label>
          <input class="input" id="fName" required value="${esc(d.name || "")}"></div>
        <div class="field"><label for="fNik">NIK</label>
          <input class="input" id="fNik" value="${esc(d.nik || "")}"></div>
        <div class="field"><label for="fAge">Usia</label>
          <input class="input num" id="fAge" type="number" min="0" max="120" value="${esc(d.age ?? "")}"></div>
        <div class="field"><label for="fGender">Jenis kelamin</label>
          <select class="select" id="fGender">
            <option value="L" ${d.gender === "L" ? "selected" : ""}>Laki-laki</option>
            <option value="P" ${d.gender === "P" ? "selected" : ""}>Perempuan</option>
          </select></div>
        <div class="field"><label for="fWeight">Berat badan (kg)</label>
          <input class="input num" id="fWeight" type="number" min="0" max="250" value="${esc(d.weightKg ?? "")}"></div>
        <div class="field"><label for="fPhone">Telepon</label>
          <input class="input" id="fPhone" type="tel" value="${esc(d.phone || "")}"></div>
        <div class="field" style="grid-column:1/-1"><label for="fAddr">Alamat</label>
          <input class="input" id="fAddr" value="${esc(d.address || "")}"></div>
        <div class="field"><label for="fDiag">Diagnosis</label>
          <select class="select" id="fDiag">
            ${["TB Paru Kasus Baru", "TB Paru Kambuh", "TB Ekstra Paru", "TB Resistan Obat"]
              .map((x) => `<option ${d.diagnosis === x ? "selected" : ""}>${x}</option>`).join("")}
          </select></div>
        <div class="field"><label for="fRegimen">Regimen</label>
          <select class="select" id="fRegimen">
            ${["2(HRZE)/4(HR)3", "2(HRZE)S/1(HRZE)/5(HR)E3", "Regimen individual"]
              .map((x) => `<option ${d.regimen === x ? "selected" : ""}>${x}</option>`).join("")}
          </select></div>
        <div class="field"><label for="fPhase">Fase pengobatan</label>
          <select class="select" id="fPhase">
            ${["Intensif", "Lanjutan"].map((x) => `<option ${d.phase === x ? "selected" : ""}>${x}</option>`).join("")}
          </select></div>
        <div class="field"><label for="fStart">Mulai pengobatan</label>
          <input class="input" id="fStart" type="date" value="${dateInput(d.startDate)}"></div>
        <div class="field" style="grid-column:1/-1"><label for="fPmo">Pengawas minum obat</label>
          <input class="input" id="fPmo" value="${esc((d.pmoNames || []).join(", "))}" placeholder="Nama pengawas, mis. keluarga atau kader">
          <span class="hint">Untuk penautan akun pengawas, gunakan email akun mereka pada kolom di bawah.</span></div>
        <div class="field" style="grid-column:1/-1"><label for="fPmoMail">Email akun pengawas (opsional)</label>
          <input class="input" id="fPmoMail" type="email" placeholder="pmo@contoh.id"></div>
      </form>`,
    footer: `<button class="btn btn-ghost" data-close>Batal</button>
             <button class="btn btn-primary" id="savePat">${isNew ? "Simpan pasien" : "Simpan perubahan"}</button>`,
    onMount(root, close) {
      root.querySelector("#savePat").addEventListener("click", async () => {
        const form = root.querySelector("#patForm");
        if (!form.reportValidity()) return;
        const btn = root.querySelector("#savePat");
        btn.disabled = true; btn.textContent = "Menyimpan…";

        const pmoNames = root.querySelector("#fPmo").value.split(",").map((x) => x.trim()).filter(Boolean);
        const data = {
          name: root.querySelector("#fName").value.trim(),
          nik: root.querySelector("#fNik").value.trim(),
          age: Number(root.querySelector("#fAge").value) || null,
          gender: root.querySelector("#fGender").value,
          weightKg: Number(root.querySelector("#fWeight").value) || null,
          phone: root.querySelector("#fPhone").value.trim(),
          address: root.querySelector("#fAddr").value.trim(),
          diagnosis: root.querySelector("#fDiag").value,
          regimen: root.querySelector("#fRegimen").value,
          phase: root.querySelector("#fPhase").value,
          startDate: new Date(root.querySelector("#fStart").value || Date.now()).getTime(),
          pmoNames,
        };

        try {
          const mail = root.querySelector("#fPmoMail").value.trim().toLowerCase();
          let pmoIds = existing?.pmoIds || [];
          if (mail) {
            const pmos = await be.listUsersByRole("pmo");
            const match = pmos.find((u) => (u.email || "").toLowerCase() === mail);
            if (match && !pmoIds.includes(match.id)) pmoIds = [...pmoIds, match.id];
            else if (!match) toast("Akun pengawas dengan email tersebut belum ditemukan.", "warn", 5000);
          }
          if (isNew) {
            const newId = await be.createPatient({
              ...data,
              doctorId: state.profile.id,
              doctorName: state.profile.name,
              pmoIds,
            });
            toast("Pasien baru tersimpan.", "ok");
            close();
            selectPatient(newId);
            location.hash = "jadwal";
          } else {
            await be.updatePatient(existing.id, { ...data, pmoIds });
            toast("Data pasien diperbarui.", "ok");
            close();
          }
        } catch (ex) {
          toast(friendlyAuthError(ex), "err", 5200);
          btn.disabled = false; btn.textContent = "Simpan";
        }
      });
    },
  });
}

function dateInput(v) {
  const d = toDate(v) || new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function scheduleDialog(existing) {
  const d = existing || { times: ["07:00"], dosePerIntake: 3 };
  modal({
    title: existing ? "Ubah jadwal dosis" : "Tambah jadwal dosis",
    body: `
      <form id="schForm" class="stack">
        <div class="field"><label for="sMed">Nama obat / paket</label>
          <input class="input" id="sMed" required value="${esc(d.medicine || "FDC Kategori 1 (RHZE)")}"></div>
        <div class="field"><label for="sDose">Jumlah butir per minum</label>
          <input class="input num" id="sDose" type="number" min="1" max="12" required value="${esc(d.dosePerIntake || 3)}"></div>
        <div class="field"><label for="sTimes">Jam minum</label>
          <input class="input num" id="sTimes" required value="${esc((d.times || []).join(", "))}" placeholder="07:00, 19:00">
          <span class="hint">Pisahkan beberapa jam dengan tanda koma, format 24 jam.</span></div>
        <div class="field"><label for="sNote">Catatan untuk pasien</label>
          <textarea class="textarea" id="sNote" placeholder="mis. diminum 1 jam sebelum makan">${esc(d.note || "")}</textarea></div>
        <div class="card tight flat"><div class="row between">
          <div><b class="small">Jadwal aktif</b><div class="tiny muted">Alarm dispenser mengikuti jadwal ini</div></div>
          <label class="switch"><input type="checkbox" id="sActive" ${d.active !== false ? "checked" : ""} aria-label="Jadwal aktif"><span class="track"></span><span class="knob"></span></label>
        </div></div>
      </form>`,
    footer: `<button class="btn btn-ghost" data-close>Batal</button>
             <button class="btn btn-primary" id="saveSch">Simpan jadwal</button>`,
    onMount(root, close) {
      root.querySelector("#saveSch").addEventListener("click", async () => {
        const form = root.querySelector("#schForm");
        if (!form.reportValidity()) return;
        const times = root.querySelector("#sTimes").value.split(",").map((t) => t.trim())
          .filter((t) => /^\d{1,2}:\d{2}$/.test(t))
          .map((t) => t.padStart(5, "0"));
        if (!times.length) { toast("Format jam belum benar, contoh 07:00.", "warn"); return; }

        const btn = root.querySelector("#saveSch");
        btn.disabled = true; btn.textContent = "Menyimpan…";
        try {
          await be.saveSchedule(state.patient.id, {
            ...(existing?.id ? { id: existing.id } : {}),
            medicine: root.querySelector("#sMed").value.trim(),
            dosePerIntake: Number(root.querySelector("#sDose").value),
            times,
            note: root.querySelector("#sNote").value.trim(),
            active: root.querySelector("#sActive").checked,
          });
          toast("Jadwal dosis tersimpan dan disinkronkan ke dispenser.", "ok");
          close();
        } catch (ex) {
          toast(friendlyAuthError(ex), "err", 5200);
          btn.disabled = false; btn.textContent = "Simpan jadwal";
        }
      });
    },
  });
}

function markDoseDialog() {
  const now = new Date();
  modal({
    title: "Catat dosis manual",
    body: `
      <form id="dsForm" class="stack">
        <p class="small soft mb-0">Gunakan bila pasien minum obat di luar dispenser, misalnya kotak tertinggal.</p>
        <div class="field"><label for="dTime">Waktu minum</label>
          <input class="input num" id="dTime" type="time" required value="${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}"></div>
        <div class="field"><label for="dStatus">Status</label>
          <select class="select" id="dStatus">
            <option value="taken">Diminum tepat waktu</option>
            <option value="late">Diminum terlambat</option>
            <option value="missed">Tidak diminum</option>
          </select></div>
      </form>`,
    footer: `<button class="btn btn-ghost" data-close>Batal</button>
             <button class="btn btn-primary" id="saveDose">Simpan catatan</button>`,
    onMount(root, close) {
      root.querySelector("#saveDose").addEventListener("click", async () => {
        const [hh, mm] = root.querySelector("#dTime").value.split(":").map(Number);
        const when = new Date(); when.setHours(hh || 0, mm || 0, 0, 0);
        const status = root.querySelector("#dStatus").value;
        try {
          await be.addDoseLog({
            patientId: state.patient.id,
            deviceId: state.patient.deviceId || null,
            scheduledAt: when.getTime(),
            takenAt: status === "missed" ? null : when.getTime(),
            status, method: status === "missed" ? null : "manual",
            votStatus: "none", escalation: status === "missed" ? 3 : 0,
          });
          if (status !== "missed") await consumePills(1);
          toast("Catatan dosis tersimpan.", "ok");
          close();
        } catch (ex) { toast(friendlyAuthError(ex), "err", 5200); }
      });
    },
  });
}

function complaintDialog() {
  modal({
    title: "Laporkan keluhan",
    body: `
      <form id="cpForm" class="stack">
        <div class="field"><label for="cSym">Keluhan</label>
          <input class="input" id="cSym" required list="symList" placeholder="mis. Mual">
          <datalist id="symList">
            ${["Mual", "Muntah", "Nyeri lambung", "Urine kemerahan", "Kesemutan tangan/kaki",
               "Gatal atau ruam", "Nyeri sendi", "Gangguan penglihatan", "Kulit/mata menguning",
               "Demam", "Batuk bertambah"].map((x) => `<option>${x}</option>`).join("")}
          </datalist></div>
        <div class="field"><label for="cSev">Tingkat keparahan</label>
          <select class="select" id="cSev">
            <option value="ringan">Ringan, masih bisa beraktivitas</option>
            <option value="sedang">Sedang, mengganggu aktivitas</option>
            <option value="berat">Berat, perlu segera ditangani</option>
          </select></div>
        <div class="field"><label for="cNote">Keterangan</label>
          <textarea class="textarea" id="cNote" required placeholder="Kapan mulai, seberapa sering, dan kaitannya dengan waktu minum obat"></textarea></div>
        <p class="tiny muted mb-0">Bila keluhan berat atau memburuk cepat, segera hubungi layanan kesehatan terdekat.</p>
      </form>`,
    footer: `<button class="btn btn-ghost" data-close>Batal</button>
             <button class="btn btn-primary" id="saveCp">Kirim keluhan</button>`,
    onMount(root, close) {
      root.querySelector("#saveCp").addEventListener("click", async () => {
        const form = root.querySelector("#cpForm");
        if (!form.reportValidity()) return;
        const severity = root.querySelector("#cSev").value;
        try {
          await be.addComplaint({
            patientId: state.patient.id,
            symptom: root.querySelector("#cSym").value.trim(),
            severity,
            note: root.querySelector("#cNote").value.trim(),
            reportedBy: state.profile.name,
          });
          if (severity === "berat") {
            await be.addAlert({
              patientId: state.patient.id, type: "keluhan_berat", level: 4,
              message: `Keluhan berat dilaporkan: ${root.querySelector("#cSym").value.trim()}. Perlu tinjauan dokter.`,
            });
          }
          toast("Keluhan terkirim ke dokter.", "ok");
          close();
        } catch (ex) { toast(friendlyAuthError(ex), "err", 5200); }
      });
    },
  });
}

function replyDialog(c) {
  if (!c) return;
  modal({
    title: `Balas keluhan: ${c.symptom}`,
    body: `
      <div class="card tight sunken mb-4">
        <div class="tiny upper muted mb-2">Laporan pasien</div>
        <div class="small mb-0">${esc(c.note)}</div>
      </div>
      <form id="rpForm" class="field">
        <label for="rText">Jawaban dan anjuran</label>
        <textarea class="textarea" id="rText" required placeholder="Anjuran penanganan, penyesuaian dosis, atau permintaan kontrol"></textarea>
      </form>`,
    footer: `<button class="btn btn-ghost" data-close>Batal</button>
             <button class="btn btn-primary" id="saveRp">Kirim jawaban</button>`,
    onMount(root, close) {
      root.querySelector("#saveRp").addEventListener("click", async () => {
        const form = root.querySelector("#rpForm");
        if (!form.reportValidity()) return;
        try {
          await be.respondComplaint(c.id, {
            response: root.querySelector("#rText").value.trim(),
            respondedBy: state.profile.name,
          });
          toast("Jawaban terkirim.", "ok");
          close();
        } catch (ex) { toast(friendlyAuthError(ex), "err", 5200); }
      });
    },
  });
}

/* ============================================================
   AFTER-RENDER BINDINGS
   ============================================================ */
function afterRender() {
  // chat
  const cf = $("#chatForm");
  if (cf) {
    const box = $("#chatBox");
    if (box) box.scrollTop = box.scrollHeight;
    cf.addEventListener("submit", async (e) => {
      e.preventDefault();
      const input = $("#chatInput");
      const text = input.value.trim();
      if (!text) return;
      input.value = "";
      try {
        await be.sendMessage({
          patientId: state.patient.id,
          senderId: state.profile.id,
          senderName: state.profile.name,
          senderRole: state.profile.role,
          text,
        });
      } catch (ex) { toast(friendlyAuthError(ex), "err", 5200); }
    });
  }

  // profile form
  const pf = $("#profileForm");
  if (pf) {
    mountThemeSwitch($("#profileTheme"));
    pf.addEventListener("submit", async (e) => {
      e.preventDefault();
      const patch = {
        name: $("#pfName").value.trim(),
        phone: $("#pfPhone").value.trim(),
      };
      if ($("#pfHospital")) patch.hospital = $("#pfHospital").value.trim();
      if ($("#pfSpecialty")) patch.specialty = $("#pfSpecialty").value.trim();
      if ($("#pfRelation")) patch.relation = $("#pfRelation").value.trim();
      try {
        await be.updateProfile(state.profile.id, patch);
        Object.assign(state.profile, patch);
        mountShell();
        toast("Profil diperbarui.", "ok");
      } catch (ex) { toast(friendlyAuthError(ex), "err", 5200); }
    });
  }

  // camera view left: release the stream
  if (state.view !== "vot") stopCamera();

  /* Wide tables scroll sideways on a phone. Add a hint above them, and drop
     the edge fade once the user has scrolled to the end. */
  $$("#content .table-scroll").forEach((wrap) => {
    if (wrap.scrollWidth <= wrap.clientWidth + 2) return;
    if (!wrap.previousElementSibling?.classList?.contains("scroll-hint")) {
      const hint = document.createElement("div");
      hint.className = "scroll-hint";
      hint.textContent = "Geser tabel ke samping untuk melihat kolom lainnya.";
      wrap.parentElement.insertBefore(hint, wrap);
    }
    const sync = () => {
      const atEnd = wrap.scrollLeft + wrap.clientWidth >= wrap.scrollWidth - 2;
      wrap.classList.toggle("at-end", atEnd);
    };
    wrap.addEventListener("scroll", sync, { passive: true });
    sync();
  });
}

/* ============================================================
   CAMERA / VOT
   ============================================================ */
async function startCamera() {
  try {
    camStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "user", width: { ideal: 1280 } },
      audio: true,
    });
    const v = $("#camVideo");
    v.srcObject = camStream;
    v.classList.remove("hidden");
    await v.play();
    $("#camPlaceholder")?.classList.add("hidden");
    $('[data-act="cam-start"]')?.classList.add("hidden");
    $('[data-act="cam-record"]')?.classList.remove("hidden");
    toast("Kamera aktif. Arahkan ke wajah dan obat.", "info");
  } catch {
    toast("Tidak dapat mengakses kamera. Periksa izin peramban.", "err", 5200);
  }
}

function startRecording() {
  recStart = Date.now();
  $("#recBadge")?.classList.remove("hidden");
  $('[data-act="cam-record"]')?.classList.add("hidden");
  $('[data-act="cam-stop"]')?.classList.remove("hidden");
  clearInterval(recTimer);
  recTimer = setInterval(() => {
    const s = Math.floor((Date.now() - recStart) / 1000);
    const t = $("#recTime");
    if (t) t.textContent = `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
  }, 500);
}

async function finishRecording() {
  const dur = Math.max(1, Math.round((Date.now() - recStart) / 1000));
  clearInterval(recTimer);
  stopCamera();
  try {
    await be.addVot({
      patientId: state.patient.id,
      durationSec: dur,
      status: "pending",
      recordedBy: state.profile.name,
      note: "",
    });
    const recent = state.logs.find((l) => l.takenAt);
    if (recent) await be.updateDoseLog(recent.id, { votStatus: "pending" });
    toast(`Sesi VOT ${dur} detik dikirim untuk ditinjau.`, "ok");
  } catch (ex) { toast(friendlyAuthError(ex), "err", 5200); }
}

function stopCamera() {
  clearInterval(recTimer);
  camStream?.getTracks().forEach((t) => t.stop());
  camStream = null;
}

/* ============================================================
   SIMULATOR + ESCALATION WATCHDOG
   ============================================================ */
function startSimulator() {
  sim?.stop();
  sim = createSimulator({
    getDevices: () => (state.device ? [state.device] : []),
    onTick: (d, patch) => { be.updateDevice(d.id, patch).catch(() => {}); },
    intervalMs: 15000,
  });
  sim.start();

  clearInterval(startSimulator._watch);
  startSimulator._watch = setInterval(watchdog, 30000);
}

/** Raises escalation alerts for overdue doses and device issues. */
async function watchdog() {
  const p = state.patient, d = state.device;
  if (!p) return;

  const overdue = state.logs.find((l) => {
    if (l.status !== "pending") return false;
    const t = toDate(l.scheduledAt)?.getTime();
    return t && Date.now() > t;
  });

  if (overdue) {
    const mins = Math.floor((Date.now() - toDate(overdue.scheduledAt).getTime()) / 60000);
    const step = escalationFor(mins);
    if ((overdue.escalation || 0) < step.level) {
      await be.updateDoseLog(overdue.id, {
        escalation: step.level,
        status: mins > 120 ? "missed" : "pending",
      }).catch(() => {});
      await be.addAlert({
        patientId: p.id, type: "dosis_terlewat", level: step.level,
        message: `Dosis ${fmtTime(overdue.scheduledAt)} belum direspons ${mins} menit. ${step.label}: ${step.detail}`,
      }).catch(() => {});
      if (d && step.level === 1) await be.updateDevice(d.id, { alarmOn: true }).catch(() => {});
    }
  }

  if (d) {
    const issues = deviceIssues(d);
    const open = state.alerts.filter((a) => !a.resolved);
    for (const i of issues) {
      if (i.type === "alarm") continue;
      if (!open.some((a) => a.type === i.type)) {
        await be.addAlert({ patientId: p.id, type: i.type, level: i.level, message: i.text }).catch(() => {});
      }
    }
  }

  // keep the stored adherence figure roughly in sync for cohort views
  if (state.logs.length) {
    const a = adherenceOf(state.logs);
    if (Math.abs((p.adherence ?? 0) - a) >= 2) await be.updatePatient(p.id, { adherence: a }).catch(() => {});
  }
}

window.addEventListener("beforeunload", stopCamera);
