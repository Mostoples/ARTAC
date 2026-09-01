/* ============================================================
   ARTA-C — Firebase backend
   Same surface as backend-demo.js so views never know which
   implementation is running.
   ============================================================ */

import { auth, db } from "./firebase-config.js";
import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";
import {
  collection, doc, addDoc, setDoc, getDoc, getDocs, updateDoc, deleteDoc,
  query, where, orderBy, limit, onSnapshot, serverTimestamp,
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js";

export const isDemo = false;
export function resetDemo() { /* not applicable in live mode */ }

const withId = (s) => ({ id: s.id, ...s.data() });
const ts = () => serverTimestamp();

/* ------------------------- auth ------------------------- */
export function onAuth(cb) {
  return onAuthStateChanged(auth, async (u) => {
    if (!u) return cb(null);
    const snap = await getDoc(doc(db, "users", u.uid));
    cb(snap.exists() ? { id: u.uid, ...snap.data() } : { id: u.uid, email: u.email, role: "pasien", name: u.email });
  });
}

export async function signIn(email, password) {
  const cred = await signInWithEmailAndPassword(auth, email.trim(), password);
  const snap = await getDoc(doc(db, "users", cred.user.uid));
  return snap.exists() ? { id: cred.user.uid, ...snap.data() } : { id: cred.user.uid, email, role: "pasien" };
}

export async function signUp({ name, email, password, role, extra = {} }) {
  const cred = await createUserWithEmailAndPassword(auth, email.trim(), password);
  const profile = { name, email: email.trim().toLowerCase(), role, createdAt: ts(), ...extra };
  await setDoc(doc(db, "users", cred.user.uid), profile);
  return { id: cred.user.uid, ...profile };
}

export async function signOutUser() {
  await signOut(auth);
}

export async function updateProfile(id, patch) {
  await updateDoc(doc(db, "users", id), patch);
}

export async function listUsersByRole(role) {
  const snap = await getDocs(query(collection(db, "users"), where("role", "==", role)));
  return snap.docs.map(withId);
}

/* ------------------------ patients ---------------------- */
function patientQuery(profile) {
  const c = collection(db, "patients");
  if (profile.role === "dokter") return query(c, where("doctorId", "==", profile.id));
  if (profile.role === "pmo") return query(c, where("pmoIds", "array-contains", profile.id));
  return query(c, where("userId", "==", profile.id));
}

export function watchPatients(profile, cb) {
  if (!profile) { cb([]); return () => {}; }
  return onSnapshot(patientQuery(profile), (s) => cb(s.docs.map(withId)), () => cb([]));
}

export function watchPatient(pid, cb) {
  return onSnapshot(doc(db, "patients", pid), (s) => cb(s.exists() ? withId(s) : null), () => cb(null));
}

export async function createPatient(data) {
  const ref = await addDoc(collection(db, "patients"), {
    createdAt: ts(), adherence: 100, status: "aktif", ...data,
  });
  const deviceId = data.deviceId || `dev-${ref.id}`;
  await updateDoc(ref, { deviceId });
  await setDoc(doc(db, "devices", deviceId), {
    patientId: ref.id, name: `ARTA-C Box ${deviceId.slice(-4)}`,
    online: true, battery: 100, tempC: 26, targetTempC: 26, humidity: 45,
    pillsLeft: 0, pillsCapacity: 90, dosePerDay: 3, alarmOn: false,
    lidOpenCount: 0, motionAt: null, lastSeen: ts(), firmware: "1.4.2",
  }, { merge: true });
  return ref.id;
}

export async function updatePatient(pid, patch) {
  await updateDoc(doc(db, "patients", pid), patch);
}

export async function deletePatient(pid) {
  const snap = await getDoc(doc(db, "patients", pid));
  const devId = snap.data()?.deviceId;
  const sch = await getDocs(collection(db, "patients", pid, "schedules"));
  await Promise.all(sch.docs.map((d) => deleteDoc(d.ref)));
  for (const c of ["doseLogs", "alerts", "complaints", "messages", "votSessions"]) {
    const rows = await getDocs(query(collection(db, c), where("patientId", "==", pid)));
    await Promise.all(rows.docs.map((d) => deleteDoc(d.ref)));
  }
  if (devId) await deleteDoc(doc(db, "devices", devId)).catch(() => {});
  await deleteDoc(doc(db, "patients", pid));
}

/* ----------------------- schedules ---------------------- */
export function watchSchedules(pid, cb) {
  return onSnapshot(collection(db, "patients", pid, "schedules"),
    (s) => cb(s.docs.map(withId)), () => cb([]));
}

export async function saveSchedule(pid, data) {
  const { id, ...rest } = data;
  if (id) await setDoc(doc(db, "patients", pid, "schedules", id), rest, { merge: true });
  else await addDoc(collection(db, "patients", pid, "schedules"), { patientId: pid, createdAt: ts(), active: true, ...rest });

  const all = await getDocs(collection(db, "patients", pid, "schedules"));
  const dosePerDay = all.docs.map((d) => d.data())
    .filter((s) => s.active !== false)
    .reduce((a, s) => a + (s.times?.length || 0) * (Number(s.dosePerIntake) || 1), 0);
  const p = await getDoc(doc(db, "patients", pid));
  const devId = p.data()?.deviceId;
  if (devId) await updateDoc(doc(db, "devices", devId), { dosePerDay }).catch(() => {});
}

export async function deleteSchedule(pid, sid) {
  await deleteDoc(doc(db, "patients", pid, "schedules", sid));
}

/* ------------------------ devices ----------------------- */
export function watchDevice(deviceId, cb) {
  if (!deviceId) { cb(null); return () => {}; }
  return onSnapshot(doc(db, "devices", deviceId), (s) => cb(s.exists() ? withId(s) : null), () => cb(null));
}

export function watchDevicesFor(profile, cb) {
  return watchPatients(profile, async (pats) => {
    const ids = pats.map((p) => p.deviceId).filter(Boolean);
    const rows = await Promise.all(ids.map((id) => getDoc(doc(db, "devices", id)).catch(() => null)));
    cb(rows.filter((s) => s?.exists()).map(withId));
  });
}

export async function updateDevice(deviceId, patch) {
  await setDoc(doc(db, "devices", deviceId), { ...patch, lastSeen: ts() }, { merge: true });
}

/* --------------- generic collection watchers ------------ */
function watchByPatient(coll, pid, cb, order = "createdAt", dir = "desc", max = 300) {
  return onSnapshot(
    query(collection(db, coll), where("patientId", "==", pid), orderBy(order, dir), limit(max)),
    (s) => cb(s.docs.map(withId)),
    () => cb([])
  );
}

function watchByTeam(coll, profile, cb, order = "createdAt", max = 400) {
  let inner = null;
  const stop = watchPatients(profile, (pats) => {
    inner?.();
    const ids = pats.map((p) => p.id).slice(0, 10); // Firestore "in" limit
    if (!ids.length) { cb([]); return; }
    inner = onSnapshot(
      query(collection(db, coll), where("patientId", "in", ids), orderBy(order, "desc"), limit(max)),
      (s) => cb(s.docs.map(withId)),
      () => cb([])
    );
  });
  return () => { inner?.(); stop(); };
}

/* ----------------------- dose logs ---------------------- */
export function watchDoseLogs(pid, cb, max = 200) {
  return watchByPatient("doseLogs", pid, cb, "scheduledAt", "desc", max);
}
export function watchDoseLogsFor(profile, cb, max = 400) {
  return watchByTeam("doseLogs", profile, cb, "scheduledAt", max);
}
export async function addDoseLog(data) {
  const ref = await addDoc(collection(db, "doseLogs"), { createdAt: ts(), ...data });
  return ref.id;
}
export async function updateDoseLog(id, patch) {
  await updateDoc(doc(db, "doseLogs", id), patch);
}

/* ------------------------ alerts ------------------------ */
export function watchAlerts(pid, cb) { return watchByPatient("alerts", pid, cb); }
export function watchAlertsFor(profile, cb) { return watchByTeam("alerts", profile, cb); }
export async function addAlert(data) {
  const ref = await addDoc(collection(db, "alerts"), { createdAt: ts(), resolved: false, ...data });
  return ref.id;
}
export async function resolveAlert(id) {
  await updateDoc(doc(db, "alerts", id), { resolved: true, resolvedAt: ts() });
}

/* ---------------------- complaints ---------------------- */
export function watchComplaints(pid, cb) { return watchByPatient("complaints", pid, cb); }
export function watchComplaintsFor(profile, cb) { return watchByTeam("complaints", profile, cb); }
export async function addComplaint(data) {
  const ref = await addDoc(collection(db, "complaints"), {
    createdAt: ts(), status: "baru", response: "", ...data,
  });
  return ref.id;
}
export async function respondComplaint(id, patch) {
  await updateDoc(doc(db, "complaints", id), { ...patch, status: "dijawab", respondedAt: ts() });
}

/* ----------------------- messages ----------------------- */
export function watchMessages(pid, cb) {
  return onSnapshot(
    query(collection(db, "messages"), where("patientId", "==", pid), orderBy("createdAt", "asc"), limit(300)),
    (s) => cb(s.docs.map(withId)),
    () => cb([])
  );
}
export async function sendMessage(data) {
  const ref = await addDoc(collection(db, "messages"), { createdAt: ts(), ...data });
  return ref.id;
}

/* ------------------------- VOT -------------------------- */
export function watchVot(pid, cb) { return watchByPatient("votSessions", pid, cb); }
export function watchVotFor(profile, cb) { return watchByTeam("votSessions", profile, cb); }
export async function addVot(data) {
  const ref = await addDoc(collection(db, "votSessions"), { createdAt: ts(), status: "pending", ...data });
  return ref.id;
}
export async function updateVot(id, patch) {
  await updateDoc(doc(db, "votSessions", id), patch);
}
