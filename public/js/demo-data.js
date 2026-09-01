/* ============================================================
   ARTA-C — seed data for demo mode
   Used only when firebase-config.js still has placeholder keys,
   so the UI can be reviewed before a real project is wired up.
   ============================================================ */

const now = Date.now();
const H = 3600e3;
const D = 24 * H;

function at(dayOffset, hh, mm = 0) {
  const d = new Date(now + dayOffset * D);
  d.setHours(hh, mm, 0, 0);
  return d.getTime();
}

export function buildSeed() {
  const uidDok = "demo-dokter";
  const uidPmo = "demo-pmo";
  const uidPas = "demo-pasien";
  const p1 = "pat-001";
  const p2 = "pat-002";
  const p3 = "pat-003";

  const users = {
    [uidDok]: {
      id: uidDok, name: "dr. Anindya Kartika, Sp.P", email: "dokter@artac.id",
      role: "dokter", phone: "0811-2000-101", hospital: "RSUD Cendana",
      specialty: "Pulmonologi", createdAt: now - 90 * D,
    },
    [uidPmo]: {
      id: uidPmo, name: "Bu Sari Handayani", email: "pmo@artac.id",
      role: "pmo", phone: "0812-3000-202", relation: "Ibu / keluarga inti",
      createdAt: now - 88 * D,
    },
    [uidPas]: {
      id: uidPas, name: "Rizky Ananda", email: "pasien@artac.id",
      role: "pasien", phone: "0813-4000-303", createdAt: now - 88 * D,
    },
  };

  const patients = {
    [p1]: {
      id: p1, name: "Rizky Ananda", nik: "3204xxxxxxxx0071", age: 24, gender: "L",
      phone: "0813-4000-303", address: "Jl. Melati 12, Bandung",
      diagnosis: "TB Paru Kasus Baru", regimen: "2(HRZE)/4(HR)3", phase: "Intensif",
      startDate: now - 42 * D, weightKg: 54,
      doctorId: uidDok, doctorName: users[uidDok].name,
      pmoIds: [uidPmo], pmoNames: [users[uidPmo].name],
      userId: uidPas, deviceId: "dev-ARTAC-0071",
      status: "aktif", adherence: 92, createdAt: now - 42 * D,
    },
    [p2]: {
      id: p2, name: "Siti Marlina", nik: "3204xxxxxxxx0112", age: 37, gender: "P",
      phone: "0857-1122-3344", address: "Jl. Kenanga 4, Cimahi",
      diagnosis: "TB Paru Kambuh", regimen: "2(HRZE)S/1(HRZE)/5(HR)E3", phase: "Lanjutan",
      startDate: now - 120 * D, weightKg: 48,
      doctorId: uidDok, doctorName: users[uidDok].name,
      pmoIds: [uidPmo], pmoNames: ["Pak Dedi (kader)"],
      deviceId: "dev-ARTAC-0112",
      status: "aktif", adherence: 68, createdAt: now - 120 * D,
    },
    [p3]: {
      id: p3, name: "Bayu Prakoso", nik: "3204xxxxxxxx0203", age: 51, gender: "L",
      phone: "0878-5566-7788", address: "Jl. Cempaka 9, Bandung",
      diagnosis: "TB Paru Kasus Baru", regimen: "2(HRZE)/4(HR)3", phase: "Intensif",
      startDate: now - 12 * D, weightKg: 61,
      doctorId: uidDok, doctorName: users[uidDok].name,
      pmoIds: [uidPmo], pmoNames: [users[uidPmo].name],
      deviceId: "dev-ARTAC-0203",
      status: "aktif", adherence: 100, createdAt: now - 12 * D,
    },
  };

  const schedules = {
    [p1]: [{
      id: "sch-1", patientId: p1, medicine: "FDC Kategori 1 (RHZE)",
      dosePerIntake: 3, times: ["07:00"], active: true,
      note: "Diminum 1 jam sebelum makan", createdAt: now - 42 * D,
    }],
    [p2]: [{
      id: "sch-2", patientId: p2, medicine: "FDC Kategori 2 (RH + E)",
      dosePerIntake: 4, times: ["07:00", "19:00"], active: true,
      note: "Pantau keluhan mual", createdAt: now - 120 * D,
    }],
    [p3]: [{
      id: "sch-3", patientId: p3, medicine: "FDC Kategori 1 (RHZE)",
      dosePerIntake: 3, times: ["06:30"], active: true,
      note: "", createdAt: now - 12 * D,
    }],
  };

  const devices = {
    "dev-ARTAC-0071": {
      id: "dev-ARTAC-0071", patientId: p1, name: "ARTA-C Box #0071",
      online: true, battery: 78, tempC: 26.4, targetTempC: 26, humidity: 48,
      pillsLeft: 63, pillsCapacity: 90, dosePerDay: 3,
      alarmOn: false, lidOpenCount: 42, motionAt: now - 5 * H,
      lastSeen: now - 4 * 60e3, refillDate: now - 21 * D, firmware: "1.4.2",
    },
    "dev-ARTAC-0112": {
      id: "dev-ARTAC-0112", patientId: p2, name: "ARTA-C Box #0112",
      online: true, battery: 34, tempC: 29.8, targetTempC: 26, humidity: 61,
      pillsLeft: 18, pillsCapacity: 120, dosePerDay: 8,
      alarmOn: true, lidOpenCount: 96, motionAt: now - 28 * H,
      lastSeen: now - 2 * 60e3, refillDate: now - 27 * D, firmware: "1.4.2",
    },
    "dev-ARTAC-0203": {
      id: "dev-ARTAC-0203", patientId: p3, name: "ARTA-C Box #0203",
      online: false, battery: 91, tempC: 25.1, targetTempC: 26, humidity: 44,
      pillsLeft: 81, pillsCapacity: 90, dosePerDay: 3,
      alarmOn: false, lidOpenCount: 11, motionAt: now - 26 * H,
      lastSeen: now - 9 * H, refillDate: now - 4 * D, firmware: "1.4.1",
    },
  };

  /* ---- dose history: 14 days, mostly adherent for p1 ---- */
  const doseLogs = [];
  let n = 0;
  const mk = (o) => doseLogs.push({ id: `dl-${++n}`, ...o });

  for (let d = 13; d >= 1; d--) {
    const sched = at(-d, 7);
    const missed = d === 9 || d === 4;
    const late = d === 6;
    mk({
      patientId: p1, deviceId: "dev-ARTAC-0071", scheduledAt: sched,
      takenAt: missed ? null : sched + (late ? 96 * 60e3 : 6 * 60e3),
      status: missed ? "missed" : late ? "late" : "taken",
      method: missed ? null : "sensor", votStatus: missed ? "none" : d % 3 === 0 ? "verified" : "none",
      escalation: missed ? 3 : 0, createdAt: sched,
    });
  }
  // today for p1: pending
  mk({
    patientId: p1, deviceId: "dev-ARTAC-0071", scheduledAt: at(0, 7),
    takenAt: at(0, 7) + 9 * 60e3, status: "taken", method: "sensor",
    votStatus: "verified", escalation: 0, createdAt: at(0, 7),
  });

  for (let d = 6; d >= 0; d--) {
    for (const hh of [7, 19]) {
      const sched = at(-d, hh);
      if (sched > now) {
        mk({ patientId: p2, deviceId: "dev-ARTAC-0112", scheduledAt: sched, takenAt: null,
             status: "pending", method: null, votStatus: "none", escalation: 0, createdAt: sched });
        continue;
      }
      const missed = (d + hh) % 5 === 0;
      mk({
        patientId: p2, deviceId: "dev-ARTAC-0112", scheduledAt: sched,
        takenAt: missed ? null : sched + 12 * 60e3,
        status: missed ? "missed" : "taken", method: missed ? null : "manual",
        votStatus: "none", escalation: missed ? 3 : 0, createdAt: sched,
      });
    }
  }

  for (let d = 5; d >= 0; d--) {
    const sched = at(-d, 6, 30);
    mk({
      patientId: p3, deviceId: "dev-ARTAC-0203", scheduledAt: sched,
      takenAt: sched + 4 * 60e3, status: "taken", method: "sensor",
      votStatus: d === 0 ? "pending" : "none", escalation: 0, createdAt: sched,
    });
  }

  const alerts = [
    { id: "al-1", patientId: p2, type: "dosis_terlewat", level: 3,
      message: "Dosis 19:00 tidak diminum. Eskalasi tahap 3: notifikasi dokter.",
      createdAt: now - 13 * H, resolved: false },
    { id: "al-2", patientId: p2, type: "suhu", level: 2,
      message: "Suhu kotak 29.8°C melebihi ambang 28°C. Jauhkan dari sinar matahari.",
      createdAt: now - 5 * H, resolved: false },
    { id: "al-3", patientId: p2, type: "stok", level: 2,
      message: "Sisa obat 18 butir, prediksi habis dalam 2 hari. Jadwalkan refill.",
      createdAt: now - 3 * H, resolved: false },
    { id: "al-4", patientId: p3, type: "offline", level: 1,
      message: "Kotak tidak terhubung 9 jam. Kemungkinan kotak tertinggal di rumah.",
      createdAt: now - 9 * H, resolved: false },
    { id: "al-5", patientId: p1, type: "dosis_terlewat", level: 1,
      message: "Pengingat tahap 1: alarm berbunyi, menunggu respons pasien.",
      createdAt: now - 4 * D, resolved: true, resolvedAt: now - 4 * D + 2 * H },
  ];

  const complaints = [
    { id: "cp-1", patientId: p1, symptom: "Mual", severity: "ringan",
      note: "Mual sekitar 30 menit setelah minum obat pagi.",
      createdAt: now - 2 * D, status: "dijawab",
      response: "Minum obat 1 jam sebelum makan, laporkan bila muntah lebih 2x.",
      respondedBy: users[uidDok].name },
    { id: "cp-2", patientId: p1, symptom: "Urine kemerahan", severity: "ringan",
      note: "Warna urine oranye kemerahan sejak 3 hari.",
      createdAt: now - 6 * H, status: "baru", response: "" },
    { id: "cp-3", patientId: p2, symptom: "Kesemutan tangan", severity: "sedang",
      note: "Kesemutan di ujung jari, terutama malam.",
      createdAt: now - 20 * H, status: "baru", response: "" },
  ];

  const messages = [
    { id: "ms-1", patientId: p1, senderId: uidPmo, senderName: users[uidPmo].name,
      senderRole: "pmo", text: "Dok, Rizky sudah minum obat pagi ini, videonya sudah saya unggah.",
      createdAt: now - 5 * H },
    { id: "ms-2", patientId: p1, senderId: uidDok, senderName: users[uidDok].name,
      senderRole: "dokter", text: "Baik, terima kasih Bu. Kepatuhan minggu ini bagus, lanjutkan.",
      createdAt: now - 4.6 * H },
    { id: "ms-3", patientId: p1, senderId: uidPas, senderName: users[uidPas].name,
      senderRole: "pasien", text: "Dok, urine saya masih kemerahan, apakah aman?",
      createdAt: now - 90 * 60e3 },
  ];

  const votSessions = [
    { id: "vt-1", patientId: p1, doseLogId: "dl-14", createdAt: now - 5 * H,
      status: "verified", durationSec: 46, verifiedBy: users[uidPmo].name,
      note: "Terlihat menelan 3 tablet, minum air sampai habis." },
    { id: "vt-2", patientId: p3, doseLogId: "dl-33", createdAt: now - 3 * H,
      status: "pending", durationSec: 38, verifiedBy: "", note: "" },
    { id: "vt-3", patientId: p1, doseLogId: "dl-11", createdAt: now - 3 * D,
      status: "verified", durationSec: 52, verifiedBy: users[uidPmo].name, note: "" },
  ];

  return { users, patients, schedules, devices, doseLogs, alerts, complaints, messages, votSessions };
}

export const DEMO_ACCOUNTS = [
  { role: "dokter", email: "dokter@artac.id", password: "demo1234", label: "Dokter" },
  { role: "pmo", email: "pmo@artac.id", password: "demo1234", label: "Pengawas (PMO)" },
  { role: "pasien", email: "pasien@artac.id", password: "demo1234", label: "Pasien" },
];
