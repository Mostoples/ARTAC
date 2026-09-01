/* ============================================================
   ARTA-C — domain logic
   Adherence scoring, escalation ladder, stock prediction,
   and the IoT box simulator.
   ============================================================ */

import { toDate } from "./ui.js";

export const ESCALATION = [
  { level: 1, at: 0,  label: "Alarm kotak", detail: "Suara + LED pada dispenser, tutup obat siap dibuka." },
  { level: 2, at: 15, label: "Notifikasi pasien", detail: "Push + panggilan aplikasi ke ponsel pasien." },
  { level: 3, at: 30, label: "Notifikasi PMO", detail: "PMO diminta menghubungi pasien langsung." },
  { level: 4, at: 60, label: "Notifikasi dokter", detail: "Dokter menerima laporan dosis terlewat." },
  { level: 5, at: 120, label: "Kunjungan rumah", detail: "Kader diminta melakukan verifikasi di lokasi." },
];

export const TEMP_LIMITS = { min: 15, max: 28 };

export const STATUS_META = {
  taken:   { label: "Diminum",  cls: "ok",   dot: "ok" },
  late:    { label: "Terlambat", cls: "warn", dot: "warn" },
  missed:  { label: "Terlewat", cls: "dang", dot: "dang" },
  pending: { label: "Menunggu", cls: "mute", dot: "" },
  skipped: { label: "Dilewati", cls: "mute", dot: "" },
};

export const VOT_META = {
  verified: { label: "Terverifikasi", cls: "ok" },
  pending:  { label: "Perlu ditinjau", cls: "warn" },
  rejected: { label: "Ditolak", cls: "dang" },
  none:     { label: "Tanpa VOT", cls: "mute" },
};

/** Adherence percentage from dose logs, ignoring not-yet-due doses. */
export function adherenceOf(logs) {
  const done = logs.filter((l) => l.status !== "pending");
  if (!done.length) return 100;
  const good = done.filter((l) => l.status === "taken" || l.status === "late").length;
  return Math.round((good / done.length) * 100);
}

/** Counts consecutive most-recent days without a missed dose. */
export function streakDays(logs) {
  const byDay = new Map();
  for (const l of logs) {
    const d = toDate(l.scheduledAt);
    if (!d || l.status === "pending") continue;
    const k = d.toDateString();
    const prev = byDay.get(k);
    const bad = l.status === "missed";
    byDay.set(k, { bad: (prev?.bad || false) || bad, t: d.getTime() });
  }
  const days = [...byDay.values()].sort((a, b) => b.t - a.t);
  let n = 0;
  for (const d of days) { if (d.bad) break; n++; }
  return n;
}

/** Last 7 calendar days as bar-chart rows. */
export function last7Days(logs) {
  const DAYS = ["Min", "Sen", "Sel", "Rab", "Kam", "Jum", "Sab"];
  const out = [];
  for (let i = 6; i >= 0; i--) {
    const day = new Date();
    day.setDate(day.getDate() - i);
    day.setHours(0, 0, 0, 0);
    const next = day.getTime() + 864e5;
    const rows = logs.filter((l) => {
      const t = toDate(l.scheduledAt)?.getTime();
      return t >= day.getTime() && t < next && l.status !== "pending";
    });
    const good = rows.filter((l) => l.status === "taken" || l.status === "late").length;
    const pct = rows.length ? Math.round((good / rows.length) * 100) : 0;
    out.push({
      label: DAYS[day.getDay()],
      pct: rows.length ? pct : 0,
      miss: rows.length > 0 && pct < 100,
      empty: rows.length === 0,
    });
  }
  return out;
}

/** Average minutes between scheduled time and actual intake. */
export function avgDelayMinutes(logs) {
  const rows = logs.filter((l) => l.takenAt && l.scheduledAt);
  if (!rows.length) return 0;
  const total = rows.reduce((a, l) => {
    const s = toDate(l.scheduledAt).getTime();
    const t = toDate(l.takenAt).getTime();
    return a + Math.max(0, (t - s) / 60000);
  }, 0);
  return Math.round(total / rows.length);
}

/** Days of stock left plus the projected run-out date. */
export function stockForecast(device) {
  const perDay = Math.max(1, Number(device?.dosePerDay) || 1);
  const left = Math.max(0, Number(device?.pillsLeft) || 0);
  const days = Math.floor(left / perDay);
  const runOut = new Date(Date.now() + days * 864e5);
  return {
    days,
    perDay,
    left,
    runOut,
    pct: device?.pillsCapacity ? Math.round((left / device.pillsCapacity) * 100) : 0,
    critical: days <= 3,
    low: days <= 7,
  };
}

/** Duration of therapy so far and the regimen milestone. */
export function therapyProgress(patient) {
  const start = toDate(patient?.startDate);
  if (!start) return { days: 0, weeks: 0, totalDays: 168, pct: 0 };
  const days = Math.max(0, Math.floor((Date.now() - start.getTime()) / 864e5));
  const totalDays = /kambuh|kategori 2|category 2/i.test(patient.regimen || "") ? 240 : 168;
  return {
    days,
    weeks: Math.floor(days / 7),
    totalDays,
    pct: Math.min(100, Math.round((days / totalDays) * 100)),
  };
}

/** Escalation step for a dose that is `minutes` overdue. */
export function escalationFor(minutes) {
  let step = ESCALATION[0];
  for (const s of ESCALATION) if (minutes >= s.at) step = s;
  return step;
}

/** Detects a same-window repeat intake (double dosing risk). */
export function repeatRisk(logs, windowMin = 90) {
  const taken = logs.filter((l) => l.takenAt).map((l) => toDate(l.takenAt).getTime()).sort((a, b) => a - b);
  for (let i = 1; i < taken.length; i++) {
    if (taken[i] - taken[i - 1] < windowMin * 60e3) return true;
  }
  return false;
}

/** Next scheduled intake as a Date, based on schedule times. */
export function nextDoseAt(schedules) {
  const times = schedules.filter((s) => s.active !== false).flatMap((s) => s.times || []);
  if (!times.length) return null;
  const now = new Date();
  const candidates = times.map((t) => {
    const [hh, mm] = String(t).split(":").map(Number);
    const d = new Date();
    d.setHours(hh || 0, mm || 0, 0, 0);
    if (d <= now) d.setDate(d.getDate() + 1);
    return d;
  });
  return candidates.sort((a, b) => a - b)[0];
}

/** Human countdown string, e.g. "3j 12m". */
export function countdown(target) {
  const d = toDate(target);
  if (!d) return "-";
  let s = Math.max(0, Math.floor((d.getTime() - Date.now()) / 1000));
  const h = Math.floor(s / 3600); s -= h * 3600;
  const m = Math.floor(s / 60); s -= m * 60;
  if (h > 0) return `${h}j ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

/** Health flags for a device. Returns array of {level,text,type}. */
export function deviceIssues(device) {
  const out = [];
  if (!device) return out;
  const st = stockForecast(device);
  if (!device.online) out.push({ type: "offline", level: 2, text: "Kotak offline, kemungkinan tertinggal atau mati" });
  if (Number(device.battery) <= 20) out.push({ type: "baterai", level: 2, text: `Baterai ${device.battery}%, segera dicas` });
  if (Number(device.tempC) > TEMP_LIMITS.max) out.push({ type: "suhu", level: 2, text: `Suhu ${device.tempC}°C di atas ambang ${TEMP_LIMITS.max}°C` });
  if (Number(device.tempC) < TEMP_LIMITS.min) out.push({ type: "suhu", level: 2, text: `Suhu ${device.tempC}°C di bawah ambang ${TEMP_LIMITS.min}°C` });
  if (st.critical) out.push({ type: "stok", level: 3, text: `Sisa ${st.left} butir, prediksi habis ${st.days} hari` });
  else if (st.low) out.push({ type: "stok", level: 1, text: `Stok menipis, cukup untuk ${st.days} hari` });
  if (device.alarmOn) out.push({ type: "alarm", level: 3, text: "Alarm aktif, dosis belum direspons" });
  return out;
}

/** Aggregate cohort numbers for the supervisor/doctor dashboard. */
export function cohortStats(patients, logs, alerts) {
  const perPatient = new Map();
  for (const l of logs) {
    if (!perPatient.has(l.patientId)) perPatient.set(l.patientId, []);
    perPatient.get(l.patientId).push(l);
  }
  const adher = patients.map((p) => adherenceOf(perPatient.get(p.id) || []));
  const avg = adher.length ? Math.round(adher.reduce((a, b) => a + b, 0) / adher.length) : 100;
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const todays = logs.filter((l) => toDate(l.scheduledAt)?.getTime() >= today.getTime());
  return {
    total: patients.length,
    avgAdherence: avg,
    atRisk: adher.filter((a) => a < 85).length,
    takenToday: todays.filter((l) => l.status === "taken" || l.status === "late").length,
    dueToday: todays.length,
    openAlerts: alerts.filter((a) => !a.resolved).length,
    critAlerts: alerts.filter((a) => !a.resolved && a.level >= 3).length,
    perPatient,
  };
}

/* ============================================================
   IoT simulator
   Stands in for the physical box until hardware telemetry is
   connected. Nudges temperature, battery and motion so the
   dashboard shows live movement.
   ============================================================ */
export function createSimulator({ getDevices, onTick, intervalMs = 6000 }) {
  let timer = null;
  const jitter = (v, amt, min, max) =>
    Math.min(max, Math.max(min, +(v + (Math.random() - 0.5) * amt).toFixed(1)));

  function tick() {
    const devices = getDevices() || [];
    for (const d of devices) {
      if (!d.online) continue;
      const target = Number(d.targetTempC) || 26;
      // thermostat pulls temperature back toward target
      const drift = (target - Number(d.tempC || target)) * 0.25;
      const patch = {
        tempC: jitter(Number(d.tempC || target) + drift, 0.6, 12, 36),
        humidity: Math.round(jitter(Number(d.humidity || 45), 3, 25, 85)),
        battery: Math.max(1, Number(d.battery || 100) - (Math.random() < 0.25 ? 1 : 0)),
      };
      onTick(d, patch);
    }
  }

  return {
    start() { if (!timer) timer = setInterval(tick, intervalMs); },
    stop() { clearInterval(timer); timer = null; },
    tick,
  };
}
