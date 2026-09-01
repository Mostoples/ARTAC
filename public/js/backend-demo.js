/* ============================================================
   ARTA-C — demo backend
   Mirrors the Firebase backend API but keeps everything in
   localStorage. Active only while firebase-config.js holds
   placeholder keys, so the UI is reviewable offline.
   ============================================================ */

import { buildSeed, DEMO_ACCOUNTS } from "./demo-data.js";

const KEY = "artac.demo.db.v1";
const SESSION = "artac.demo.session";

let db = load();
const subs = new Set();

function load() {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) return JSON.parse(raw);
  } catch { /* corrupt payload: reseed */ }
  const seed = buildSeed();
  localStorage.setItem(KEY, JSON.stringify(seed));
  return seed;
}

function save() {
  localStorage.setItem(KEY, JSON.stringify(db));
  subs.forEach((fn) => { try { fn(); } catch { /* listener errors are non-fatal */ } });
}

function onChange(fn) {
  subs.add(fn);
  fn();
  return () => subs.delete(fn);
}

const uid = (p) => `${p}-${Math.random().toString(36).slice(2, 9)}`;
const clone = (v) => JSON.parse(JSON.stringify(v));

export const isDemo = true;

export function resetDemo() {
  localStorage.removeItem(KEY);
  localStorage.removeItem(SESSION);
  db = load();
  save();
}

/* ------------------------- auth ------------------------- */
let authCb = null;

export function onAuth(cb) {
  authCb = cb;
  const uidNow = localStorage.getItem(SESSION);
  cb(uidNow && db.users[uidNow] ? clone(db.users[uidNow]) : null);
  return () => { authCb = null; };
}

export async function signIn(email, password) {
  const acc = DEMO_ACCOUNTS.find((a) => a.email === email.trim().toLowerCase());
  const user = Object.values(db.users).find(
    (u) => u.email.toLowerCase() === email.trim().toLowerCase()
  );
  if (!user) throw new Error("Akun tidak ditemukan. Gunakan salah satu akun demo.");
  if (acc && password !== acc.password) throw new Error("Kata sandi demo salah (demo1234).");
  localStorage.setItem(SESSION, user.id);
  authCb?.(clone(user));
  return clone(user);
}

export async function signUp({ name, email, password, role, extra = {} }) {
  void password;
  const mail = email.trim().toLowerCase();
  if (Object.values(db.users).some((u) => u.email.toLowerCase() === mail))
    throw new Error("Email sudah terdaftar pada mode demo.");
  const id = uid("u");
  db.users[id] = { id, name, email: mail, role, createdAt: Date.now(), ...extra };
  save();
  localStorage.setItem(SESSION, id);
  authCb?.(clone(db.users[id]));
  return clone(db.users[id]);
}

export async function signOutUser() {
  localStorage.removeItem(SESSION);
  authCb?.(null);
}

export async function updateProfile(id, patch) {
  Object.assign(db.users[id], patch);
  save();
  if (localStorage.getItem(SESSION) === id) authCb?.(clone(db.users[id]));
}

export async function listUsersByRole(role) {
  return Object.values(db.users).filter((u) => u.role === role).map(clone);
}

/* ------------------------ patients ---------------------- */
function visiblePatients(profile) {
  const all = Object.values(db.patients);
  if (!profile) return [];
  if (profile.role === "dokter") return all.filter((p) => p.doctorId === profile.id);
  if (profile.role === "pmo") return all.filter((p) => (p.pmoIds || []).includes(profile.id));
  return all.filter((p) => p.userId === profile.id);
}

export function watchPatients(profile, cb) {
  return onChange(() => cb(visiblePatients(profile).map(clone)));
}

export function watchPatient(pid, cb) {
  return onChange(() => cb(db.patients[pid] ? clone(db.patients[pid]) : null));
}

export async function createPatient(data) {
  const id = uid("pat");
  db.patients[id] = { id, createdAt: Date.now(), adherence: 100, status: "aktif", ...data };
  const devId = data.deviceId || `dev-${id}`;
  db.patients[id].deviceId = devId;
  if (!db.devices[devId]) {
    db.devices[devId] = {
      id: devId, patientId: id, name: `ARTA-C Box ${devId.slice(-4)}`,
      online: true, battery: 100, tempC: 26, targetTempC: 26, humidity: 45,
      pillsLeft: 0, pillsCapacity: 90, dosePerDay: 3, alarmOn: false,
      lidOpenCount: 0, motionAt: null, lastSeen: Date.now(),
      refillDate: Date.now(), firmware: "1.4.2",
    };
  }
  db.schedules[id] = db.schedules[id] || [];
  save();
  return id;
}

export async function updatePatient(pid, patch) {
  Object.assign(db.patients[pid], patch);
  save();
}

export async function deletePatient(pid) {
  const dev = db.patients[pid]?.deviceId;
  delete db.patients[pid];
  delete db.schedules[pid];
  if (dev) delete db.devices[dev];
  for (const c of ["doseLogs", "alerts", "complaints", "messages", "votSessions"])
    db[c] = db[c].filter((r) => r.patientId !== pid);
  save();
}

/* ----------------------- schedules ---------------------- */
export function watchSchedules(pid, cb) {
  return onChange(() => cb(clone(db.schedules[pid] || [])));
}

export async function saveSchedule(pid, data) {
  db.schedules[pid] = db.schedules[pid] || [];
  if (data.id) {
    const i = db.schedules[pid].findIndex((s) => s.id === data.id);
    if (i >= 0) db.schedules[pid][i] = { ...db.schedules[pid][i], ...data };
  } else {
    db.schedules[pid].push({ id: uid("sch"), patientId: pid, createdAt: Date.now(), active: true, ...data });
  }
  const dev = db.devices[db.patients[pid]?.deviceId];
  if (dev) {
    dev.dosePerDay = (db.schedules[pid] || [])
      .filter((s) => s.active)
      .reduce((a, s) => a + (s.times?.length || 0) * (Number(s.dosePerIntake) || 1), 0);
  }
  save();
}

export async function deleteSchedule(pid, sid) {
  db.schedules[pid] = (db.schedules[pid] || []).filter((s) => s.id !== sid);
  save();
}

/* ------------------------ devices ----------------------- */
export function watchDevice(deviceId, cb) {
  return onChange(() => cb(db.devices[deviceId] ? clone(db.devices[deviceId]) : null));
}

export function watchDevicesFor(profile, cb) {
  return onChange(() => {
    const ids = visiblePatients(profile).map((p) => p.deviceId);
    cb(Object.values(db.devices).filter((d) => ids.includes(d.id)).map(clone));
  });
}

export async function updateDevice(deviceId, patch) {
  if (!db.devices[deviceId]) return;
  Object.assign(db.devices[deviceId], patch, { lastSeen: Date.now() });
  save();
}

/* ----------------------- dose logs ---------------------- */
export function watchDoseLogs(pid, cb, max = 200) {
  return onChange(() =>
    cb(db.doseLogs.filter((l) => l.patientId === pid)
      .sort((a, b) => b.scheduledAt - a.scheduledAt).slice(0, max).map(clone))
  );
}

export function watchDoseLogsFor(profile, cb, max = 400) {
  return onChange(() => {
    const ids = visiblePatients(profile).map((p) => p.id);
    cb(db.doseLogs.filter((l) => ids.includes(l.patientId))
      .sort((a, b) => b.scheduledAt - a.scheduledAt).slice(0, max).map(clone));
  });
}

export async function addDoseLog(data) {
  const id = uid("dl");
  db.doseLogs.push({ id, createdAt: Date.now(), ...data });
  save();
  return id;
}

export async function updateDoseLog(id, patch) {
  const l = db.doseLogs.find((x) => x.id === id);
  if (l) Object.assign(l, patch);
  save();
}

/* ------------------------ alerts ------------------------ */
export function watchAlerts(pid, cb) {
  return onChange(() =>
    cb(db.alerts.filter((a) => a.patientId === pid)
      .sort((a, b) => b.createdAt - a.createdAt).map(clone))
  );
}

export function watchAlertsFor(profile, cb) {
  return onChange(() => {
    const ids = visiblePatients(profile).map((p) => p.id);
    cb(db.alerts.filter((a) => ids.includes(a.patientId))
      .sort((a, b) => b.createdAt - a.createdAt).map(clone));
  });
}

export async function addAlert(data) {
  const id = uid("al");
  db.alerts.push({ id, createdAt: Date.now(), resolved: false, ...data });
  save();
  return id;
}

export async function resolveAlert(id) {
  const a = db.alerts.find((x) => x.id === id);
  if (a) { a.resolved = true; a.resolvedAt = Date.now(); }
  save();
}

/* ---------------------- complaints ---------------------- */
export function watchComplaints(pid, cb) {
  return onChange(() =>
    cb(db.complaints.filter((c) => c.patientId === pid)
      .sort((a, b) => b.createdAt - a.createdAt).map(clone))
  );
}

export function watchComplaintsFor(profile, cb) {
  return onChange(() => {
    const ids = visiblePatients(profile).map((p) => p.id);
    cb(db.complaints.filter((c) => ids.includes(c.patientId))
      .sort((a, b) => b.createdAt - a.createdAt).map(clone));
  });
}

export async function addComplaint(data) {
  const id = uid("cp");
  db.complaints.push({ id, createdAt: Date.now(), status: "baru", response: "", ...data });
  save();
  return id;
}

export async function respondComplaint(id, patch) {
  const c = db.complaints.find((x) => x.id === id);
  if (c) Object.assign(c, patch, { status: "dijawab", respondedAt: Date.now() });
  save();
}

/* ----------------------- messages ----------------------- */
export function watchMessages(pid, cb) {
  return onChange(() =>
    cb(db.messages.filter((m) => m.patientId === pid)
      .sort((a, b) => a.createdAt - b.createdAt).map(clone))
  );
}

export async function sendMessage(data) {
  const id = uid("ms");
  db.messages.push({ id, createdAt: Date.now(), ...data });
  save();
  return id;
}

/* ------------------------- VOT -------------------------- */
export function watchVot(pid, cb) {
  return onChange(() =>
    cb(db.votSessions.filter((v) => v.patientId === pid)
      .sort((a, b) => b.createdAt - a.createdAt).map(clone))
  );
}

export function watchVotFor(profile, cb) {
  return onChange(() => {
    const ids = visiblePatients(profile).map((p) => p.id);
    cb(db.votSessions.filter((v) => ids.includes(v.patientId))
      .sort((a, b) => b.createdAt - a.createdAt).map(clone));
  });
}

export async function addVot(data) {
  const id = uid("vt");
  db.votSessions.push({ id, createdAt: Date.now(), status: "pending", ...data });
  save();
  return id;
}

export async function updateVot(id, patch) {
  const v = db.votSessions.find((x) => x.id === id);
  if (v) Object.assign(v, patch);
  save();
}
