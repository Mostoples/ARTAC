/* ============================================================
   ARTA-C — dashboard views
   Each view is a pure render function over the shared state
   object built in app.js.
   ============================================================ */

import {
  esc, icon, gauge, bars, spark, emptyState,
  fmtTime, fmtDate, fmtDateTime, relTime, initials,
} from "./ui.js";
import {
  STATUS_META, VOT_META, ESCALATION, TEMP_LIMITS,
  adherenceOf, streakDays, last7Days, avgDelayMinutes,
  stockForecast, therapyProgress, deviceIssues, cohortStats,
  nextDoseAt, countdown, repeatRisk,
} from "./logic.js";

const statusBadge = (s) => {
  const m = STATUS_META[s] || STATUS_META.pending;
  return `<span class="badge ${m.cls}">${m.label}</span>`;
};

const votBadge = (v) => {
  const m = VOT_META[v] || VOT_META.none;
  return `<span class="badge ${m.cls}">${m.label}</span>`;
};

const levelBadge = (n) =>
  `<span class="badge ${n >= 3 ? "dang" : n === 2 ? "warn" : "mute"}">Tahap ${n}</span>`;

/* ============================================================
   OVERVIEW
   ============================================================ */
export function overview(s) {
  const { patient, device, logs, schedules, alerts, complaints, vots, profile } = s;
  if (!patient) return noPatient(profile);

  const adh = adherenceOf(logs);
  const stock = stockForecast(device);
  const prog = therapyProgress(patient);
  const streak = streakDays(logs);
  const week = last7Days(logs);
  const delay = avgDelayMinutes(logs);
  const openAlerts = alerts.filter((a) => !a.resolved);
  const next = nextDoseAt(schedules);
  const issues = deviceIssues(device);
  const repeat = repeatRisk(logs);
  const votPending = vots.filter((v) => v.status === "pending").length;
  const newComplaints = complaints.filter((c) => c.status === "baru").length;

  return `
  <div class="view stack">
    ${issues.length ? `
    <div class="card tight" style="border-left:4px solid var(--warn)">
      <div class="row between wrapx">
        <div class="row"><span class="tile-icon">${icon("alert", 18)}</span>
          <div><b>${issues.length} hal perlu perhatian pada perangkat</b>
          <div class="small soft">${issues.map((i) => esc(i.text)).join(" · ")}</div></div>
        </div>
        <a class="btn btn-sm btn-ghost" href="#perangkat" data-nav="perangkat">Buka perangkat</a>
      </div>
    </div>` : ""}

    <div class="grid g-4">
      ${statTile("Kepatuhan", `${adh}%`, adh >= 90 ? "Sangat baik" : adh >= 80 ? "Perlu dipantau" : "Berisiko putus obat", "chart", adh < 85)}
      ${statTile("Dosis berikutnya", next ? fmtTime(next) : "-", next ? `dalam ${countdown(next)}` : "Belum ada jadwal", "clock")}
      ${statTile("Sisa obat", `${stock.left}`, `cukup ${stock.days} hari · habis ${fmtDate(stock.runOut)}`, "pill", stock.low)}
      ${statTile("Hari berturut patuh", `${streak}`, `pengobatan hari ke-${prog.days}`, "check")}
    </div>

    <div class="grid g-wide">
      <section class="card">
        <div class="card-head">
          <h3>${icon("chart")} Kepatuhan 7 hari terakhir</h3>
          <span class="badge mute">Rata-rata jeda ${delay} menit</span>
        </div>
        ${bars(week)}
        <hr class="divider">
        <div class="grid g-3">
          <div class="stat"><span class="label">Total dosis tercatat</span><span class="value num">${logs.filter((l) => l.status !== "pending").length}</span></div>
          <div class="stat"><span class="label">Terlewat</span><span class="value num" style="color:var(--dang)">${logs.filter((l) => l.status === "missed").length}</span></div>
          <div class="stat"><span class="label">Terlambat</span><span class="value num" style="color:var(--warn)">${logs.filter((l) => l.status === "late").length}</span></div>
        </div>
      </section>

      <section class="card tc">
        <div class="card-head" style="justify-content:center"><h3>Skor kepatuhan</h3></div>
        <div class="row center">${gauge(adh)}</div>
        <p class="small soft mt-4 mb-0">
          ${adh >= 90 ? "Kepatuhan pasien terjaga, lanjutkan pola pendampingan saat ini."
            : adh >= 80 ? "Ada beberapa dosis terlewat. Pertimbangkan pengingat tambahan dari PMO."
            : "Kepatuhan di bawah ambang aman. Perlu evaluasi dan kunjungan langsung."}
        </p>
      </section>
    </div>

    <div class="grid g-3">
      ${miniCard("Peringatan terbuka", openAlerts.length, openAlerts.length ? "Perlu ditindaklanjuti" : "Semua tertangani", "bell", "peringatan", openAlerts.length > 0)}
      ${miniCard("VOT perlu ditinjau", votPending, votPending ? "Konfirmasi bukti menelan" : "Tidak ada tunggakan", "video", "vot", votPending > 0)}
      ${miniCard("Keluhan baru", newComplaints, newComplaints ? "Menunggu jawaban dokter" : "Tidak ada keluhan baru", "doc", "keluhan", newComplaints > 0)}
    </div>

    ${repeat ? `
    <div class="card tight" style="border-left:4px solid var(--dang)">
      <div class="row"><span class="tile-icon" style="background:color-mix(in srgb, var(--dang) 18%, transparent);color:var(--dang)">${icon("refresh", 18)}</span>
        <div><b>Indikasi pengulangan minum obat</b>
        <div class="small soft">Kotak terbuka dua kali dalam rentang berdekatan. Pastikan pasien tidak menerima dosis ganda.</div></div>
      </div>
    </div>` : ""}

    <div class="grid g-2">
      <section class="card">
        <div class="card-head"><h3>${icon("clock")} Riwayat dosis terkini</h3>
          <a class="btn btn-sm btn-ghost" href="#jadwal" data-nav="jadwal">Semua</a></div>
        ${logs.length ? `<ol class="tl">${logs.slice(0, 6).map((l) => `
          <li class="${l.status === "taken" ? "ok" : l.status === "late" ? "warn" : l.status === "missed" ? "dang" : ""}">
            <div class="row between wrapx">
              <b class="num">${fmtTime(l.scheduledAt)}</b>${statusBadge(l.status)}
            </div>
            <div class="small soft">${fmtDate(l.scheduledAt)}${l.takenAt ? ` · diminum ${fmtTime(l.takenAt)}` : ""}${l.method ? ` · ${l.method === "sensor" ? "terdeteksi sensor" : "input manual"}` : ""}</div>
          </li>`).join("")}</ol>` : emptyState("Belum ada riwayat dosis.", "clock")}
      </section>

      <section class="card">
        <div class="card-head"><h3>${icon("box")} Kondisi kotak obat</h3>
          <span class="badge ${device?.online ? "ok" : "dang"}"><span class="dot ${device?.online ? "ok live" : "dang"}"></span>${device?.online ? "Online" : "Offline"}</span></div>
        ${device ? `
        <div class="row wrapx between mb-4">
          <div class="temp-ring ${Number(device.tempC) > TEMP_LIMITS.max ? "alarm-on" : ""}">${Number(device.tempC).toFixed(1)}°<small>suhu</small></div>
          <div class="temp-ring">${device.humidity}%<small>kelembapan</small></div>
          <div class="temp-ring">${device.battery}%<small>baterai</small></div>
        </div>
        <div class="small soft mb-2">Stok obat ${stock.left} / ${device.pillsCapacity} butir</div>
        <div class="bar ${stock.critical ? "dang" : stock.low ? "warn" : ""}"><i style="width:${stock.pct}%"></i></div>
        <p class="tiny muted mt-4 mb-0">Terakhir terhubung ${relTime(device.lastSeen)} · gerakan terakhir ${relTime(device.motionAt)} · firmware ${esc(device.firmware || "-")}</p>
        ` : emptyState("Perangkat belum terpasang untuk pasien ini.", "box")}
      </section>
    </div>

    <section class="card">
      <div class="card-head"><h3>${icon("stetho")} Ringkasan pengobatan</h3>
        <span class="badge">${esc(patient.phase || "-")}</span></div>
      <div class="grid g-2">
        <div class="col">
          ${infoRow("Diagnosis", patient.diagnosis)}
          ${infoRow("Regimen", patient.regimen)}
          ${infoRow("Mulai pengobatan", fmtDate(patient.startDate))}
          ${infoRow("Berat badan", patient.weightKg ? `${patient.weightKg} kg` : "-")}
        </div>
        <div class="col">
          ${infoRow("Dokter penanggung jawab", patient.doctorName)}
          ${infoRow("Pengawas minum obat", (patient.pmoNames || []).join(", ") || "-")}
          ${infoRow("Telepon", patient.phone)}
          ${infoRow("Alamat", patient.address)}
        </div>
      </div>
      <hr class="divider">
      <div class="row between wrapx mb-2">
        <span class="small soft">Progres pengobatan</span>
        <span class="small num">${prog.days} / ${prog.totalDays} hari (${prog.pct}%)</span>
      </div>
      <div class="bar"><i style="width:${prog.pct}%"></i></div>
    </section>
  </div>`;
}

function statTile(label, value, foot, ic, warn = false) {
  return `<div class="card tight">
    <div class="row between mb-2">
      <span class="tile-icon" ${warn ? 'style="background:color-mix(in srgb, var(--warn) 20%, transparent);color:var(--warn)"' : ""}>${icon(ic, 20)}</span>
    </div>
    <div class="stat"><span class="label">${esc(label)}</span>
    <span class="value num">${esc(value)}</span>
    <span class="foot">${esc(foot)}</span></div>
  </div>`;
}

function miniCard(title, n, foot, ic, nav, warn) {
  return `<a class="card tight hover" href="#${nav}" data-nav="${nav}" style="text-decoration:none;color:inherit">
    <div class="row">
      <span class="tile-icon" ${warn ? 'style="background:color-mix(in srgb, var(--dang) 16%, transparent);color:var(--dang)"' : ""}>${icon(ic, 20)}</span>
      <div class="grow"><div class="stat"><span class="label">${esc(title)}</span>
        <span class="value num">${n}</span><span class="foot">${esc(foot)}</span></div></div>
    </div>
  </a>`;
}

function infoRow(k, v) {
  return `<div class="row between wrapx" style="gap:var(--sp-4)">
    <span class="small muted nowrap">${esc(k)}</span>
    <span class="small right"><b>${esc(v || "-")}</b></span>
  </div>`;
}

function noPatient(profile) {
  const msg = profile?.role === "dokter"
    ? "Belum ada pasien terdaftar. Tambahkan pasien baru untuk mulai memantau."
    : profile?.role === "pmo"
      ? "Anda belum ditugaskan sebagai pengawas untuk pasien mana pun. Hubungi dokter penanggung jawab."
      : "Data pasien Anda belum ditautkan. Hubungi dokter atau petugas untuk penautan akun.";
  return `<div class="view card">${emptyState(msg, "users")}
    ${profile?.role === "dokter" ? '<div class="row center mt-4"><button class="btn btn-primary" data-nav="pasien">Kelola pasien</button></div>' : ""}
  </div>`;
}

/* ============================================================
   COHORT (doctor / PMO patient list)
   ============================================================ */
export function cohort(s) {
  const { patients, allLogs, allAlerts, profile } = s;
  const st = cohortStats(patients, allLogs, allAlerts);
  const canEdit = profile?.role === "dokter";

  return `
  <div class="view stack">
    <div class="grid g-4">
      ${statTile("Pasien dipantau", st.total, "dalam pengobatan aktif", "users")}
      ${statTile("Kepatuhan rata-rata", `${st.avgAdherence}%`, `${st.atRisk} pasien berisiko`, "chart", st.atRisk > 0)}
      ${statTile("Dosis hari ini", `${st.takenToday}/${st.dueToday}`, "sudah diminum", "pill")}
      ${statTile("Peringatan terbuka", st.openAlerts, `${st.critAlerts} tahap kritis`, "bell", st.openAlerts > 0)}
    </div>

    <section class="card">
      <div class="card-head">
        <h3>${icon("users")} Daftar pasien</h3>
        ${canEdit ? `<button class="btn btn-primary btn-sm" data-act="add-patient">${icon("plus", 15)} Pasien baru</button>` : ""}
      </div>
      ${patients.length ? `
      <div class="table-scroll"><table class="tbl">
        <thead><tr>
          <th>Pasien</th><th>Diagnosis</th><th>Fase</th><th>Kepatuhan</th><th>Kotak</th><th>Aksi</th>
        </tr></thead>
        <tbody>
        ${patients.map((p) => {
          const lg = st.perPatient.get(p.id) || [];
          const a = adherenceOf(lg);
          const dev = s.allDevices.find((d) => d.id === p.deviceId);
          return `<tr>
            <td><div class="row"><span class="avatar">${esc(initials(p.name))}</span>
              <div><b>${esc(p.name)}</b><div class="tiny muted">${esc(p.age ? `${p.age} thn` : "")} ${esc(p.gender === "P" ? "Perempuan" : p.gender === "L" ? "Laki-laki" : "")}</div></div></div></td>
            <td class="small">${esc(p.diagnosis || "-")}<div class="tiny muted">${esc(p.regimen || "")}</div></td>
            <td><span class="badge mute">${esc(p.phase || "-")}</span></td>
            <td style="min-width:130px">
              <div class="row between tiny mb-2"><span class="num">${a}%</span></div>
              <div class="bar ${a < 80 ? "dang" : a < 90 ? "warn" : ""}"><i style="width:${a}%"></i></div>
            </td>
            <td><span class="badge ${dev?.online ? "ok" : "dang"}"><span class="dot ${dev?.online ? "ok" : "dang"}"></span>${dev?.online ? "Online" : "Offline"}</span></td>
            <td><div class="row">
              <button class="btn btn-sm btn-ghost" data-act="open-patient" data-id="${esc(p.id)}">Buka</button>
              ${canEdit ? `<button class="btn btn-sm btn-ghost" data-act="edit-patient" data-id="${esc(p.id)}" aria-label="Ubah data ${esc(p.name)}">${icon("settings", 14)}</button>` : ""}
            </div></td>
          </tr>`;
        }).join("")}
        </tbody>
      </table></div>` : emptyState(canEdit ? "Belum ada pasien. Tambahkan pasien baru." : "Belum ada pasien yang ditugaskan kepada Anda.", "users")}
    </section>
  </div>`;
}

/* ============================================================
   SCHEDULE + DOSE LOG
   ============================================================ */
export function schedule(s) {
  const { patient, schedules, logs, profile } = s;
  if (!patient) return noPatient(profile);
  const canEdit = profile?.role === "dokter";
  const next = nextDoseAt(schedules);

  return `
  <div class="view stack">
    <section class="card">
      <div class="card-head">
        <h3>${icon("pill")} Jadwal dosis</h3>
        ${canEdit ? `<button class="btn btn-primary btn-sm" data-act="add-schedule">${icon("plus", 15)} Tambah jadwal</button>`
          : '<span class="badge mute">Hanya dokter dapat mengubah</span>'}
      </div>
      ${schedules.length ? `<div class="col">${schedules.map((sc) => `
        <div class="card tight flat">
          <div class="row between wrapx">
            <div>
              <b>${esc(sc.medicine)}</b>
              <div class="small soft">${sc.dosePerIntake} butir per minum · ${(sc.times || []).length}x sehari</div>
              ${sc.note ? `<div class="tiny muted">${esc(sc.note)}</div>` : ""}
            </div>
            <div class="row wrapx">
              <div class="chip-row">${(sc.times || []).map((t) => `<span class="badge num">${esc(t)}</span>`).join("")}</div>
              <span class="badge ${sc.active === false ? "mute" : "ok"}">${sc.active === false ? "Nonaktif" : "Aktif"}</span>
              ${canEdit ? `
                <button class="btn btn-sm btn-ghost" data-act="edit-schedule" data-id="${esc(sc.id)}">${icon("settings", 14)}</button>
                <button class="btn btn-sm btn-ghost" data-act="del-schedule" data-id="${esc(sc.id)}" aria-label="Hapus jadwal">${icon("x", 14)}</button>` : ""}
            </div>
          </div>
        </div>`).join("")}</div>`
        : emptyState("Belum ada jadwal dosis. Dokter perlu menetapkan dosis dan jam minum.", "pill")}
      ${next ? `<p class="small soft mt-4 mb-0">Dosis berikutnya ${fmtTime(next)}, dalam ${countdown(next)}.</p>` : ""}
    </section>

    <section class="card">
      <div class="card-head">
        <h3>${icon("check")} Ceklist peminuman obat</h3>
        <button class="btn btn-sm btn-ghost" data-act="mark-dose">Catat dosis manual</button>
      </div>
      ${logs.length ? `
      <div class="table-scroll"><table class="tbl">
        <thead><tr><th>Jadwal</th><th>Status</th><th>Diminum</th><th>Sumber</th><th>VOT</th><th>Aksi</th></tr></thead>
        <tbody>${logs.slice(0, 40).map((l) => `
          <tr>
            <td class="nowrap"><b class="num">${fmtTime(l.scheduledAt)}</b><div class="tiny muted">${fmtDate(l.scheduledAt)}</div></td>
            <td>${statusBadge(l.status)}</td>
            <td class="num small">${l.takenAt ? fmtTime(l.takenAt) : "-"}</td>
            <td class="small">${l.method === "sensor" ? "Sensor kotak" : l.method === "manual" ? "Manual PMO" : "-"}</td>
            <td>${votBadge(l.votStatus)}</td>
            <td>${l.status === "pending" || l.status === "missed"
              ? `<button class="btn btn-sm btn-ghost" data-act="confirm-dose" data-id="${esc(l.id)}">Tandai diminum</button>` : ""}</td>
          </tr>`).join("")}
        </tbody></table></div>` : emptyState("Belum ada catatan dosis.", "check")}
    </section>
  </div>`;
}

/* ============================================================
   DEVICE + SIMULATOR
   ============================================================ */
export function deviceView(s) {
  const { patient, device, profile } = s;
  if (!patient) return noPatient(profile);
  if (!device) return `<div class="view card">${emptyState("Perangkat belum tertaut dengan pasien ini.", "box")}</div>`;

  const stock = stockForecast(device);
  const issues = deviceIssues(device);
  const tempBad = Number(device.tempC) > TEMP_LIMITS.max || Number(device.tempC) < TEMP_LIMITS.min;

  return `
  <div class="view stack">
    <section class="card">
      <div class="card-head">
        <h3>${icon("box")} ${esc(device.name || device.id)}</h3>
        <div class="row">
          <span class="badge ${device.online ? "ok" : "dang"}"><span class="dot ${device.online ? "ok live" : "dang"}"></span>${device.online ? "Terhubung" : "Offline"}</span>
          ${device.alarmOn ? '<span class="badge dang">Alarm aktif</span>' : ""}
        </div>
      </div>
      <div class="sim-grid">
        ${simCell("Suhu kompartemen", `${Number(device.tempC).toFixed(1)}°C`, `target ${device.targetTempC}°C · ambang ${TEMP_LIMITS.min}–${TEMP_LIMITS.max}°C`, tempBad)}
        ${simCell("Kelembapan", `${device.humidity}%`, "menjaga obat tidak lembap")}
        ${simCell("Baterai", `${device.battery}%`, Number(device.battery) <= 20 ? "segera dicas" : "daya cukup", Number(device.battery) <= 20)}
        ${simCell("Sisa obat", `${stock.left} butir`, `cukup ${stock.days} hari`, stock.low)}
        ${simCell("Bungkus dibuka", `${device.lidOpenCount}x`, "total sejak refill")}
        ${simCell("Gerakan terakhir", relTime(device.motionAt), "sensor deteksi ambil obat")}
      </div>
    </section>

    ${issues.length ? `
    <section class="card">
      <div class="card-head"><h3>${icon("alert")} Diagnostik perangkat</h3></div>
      <ul class="lst">${issues.map((i) => `
        <li><span class="dot ${i.level >= 3 ? "dang" : "warn"}"></span>
          <div class="grow"><b>${esc(i.type)}</b><div class="small soft">${esc(i.text)}</div></div>
          ${levelBadge(i.level)}</li>`).join("")}</ul>
    </section>` : ""}

    <section class="card">
      <div class="card-head">
        <h3>${icon("settings")} Kendali & simulasi perangkat</h3>
        <span class="badge mute">Pengganti telemetri hardware</span>
      </div>
      <p class="small soft">
        Selama unit fisik belum tersambung, kendali di bawah ini mengirim perintah dan telemetri
        tiruan ke basis data agar alur aplikasi dapat diuji menyeluruh.
      </p>
      <div class="grid g-2">
        <div class="col">
          <div class="field">
            <label for="setTemp">Target suhu (°C)</label>
            <input class="input num" type="number" id="setTemp" min="15" max="30" step="0.5" value="${esc(device.targetTempC)}">
          </div>
          <div class="field">
            <label for="setPills">Isi ulang jumlah butir</label>
            <input class="input num" type="number" id="setPills" min="0" max="${esc(device.pillsCapacity)}" value="${esc(device.pillsLeft)}">
            <span class="hint">Kapasitas ${esc(device.pillsCapacity)} butir. Refill masih dilakukan manual.</span>
          </div>
          <button class="btn btn-primary" data-act="save-device">Simpan pengaturan</button>
        </div>
        <div class="col">
          <div class="card tight flat">
            <div class="row between">
              <div><b>Status koneksi</b><div class="tiny muted">Simulasikan kotak tertinggal atau mati</div></div>
              <label class="switch"><input type="checkbox" id="tgOnline" ${device.online ? "checked" : ""} aria-label="Status online perangkat"><span class="track"></span><span class="knob"></span></label>
            </div>
          </div>
          <div class="card tight flat">
            <div class="row between">
              <div><b>Alarm dispenser</b><div class="tiny muted">Suara dan indikator visual</div></div>
              <label class="switch"><input type="checkbox" id="tgAlarm" ${device.alarmOn ? "checked" : ""} aria-label="Alarm perangkat"><span class="track"></span><span class="knob"></span></label>
            </div>
          </div>
          <button class="btn btn-ghost btn-block" data-act="sim-press">${icon("pill", 15)} Tekan tombol pembuka obat</button>
          <button class="btn btn-ghost btn-block" data-act="sim-motion">${icon("motion", 15)} Picu sensor gerakan</button>
        </div>
      </div>
    </section>
  </div>`;
}

function simCell(label, value, foot, warn = false) {
  return `<div class="sim-cell">
    <span class="label upper" style="color:var(--fg-mute)">${esc(label)}</span>
    <span class="num" style="font-size:1.5rem;font-weight:800;${warn ? "color:var(--warn)" : ""}">${esc(value)}</span>
    <span class="tiny muted">${esc(foot)}</span>
  </div>`;
}

/* ============================================================
   ALERTS + ESCALATION
   ============================================================ */
export function alertsView(s) {
  const { alerts, patient, profile } = s;
  if (!patient) return noPatient(profile);
  const open = alerts.filter((a) => !a.resolved);
  const done = alerts.filter((a) => a.resolved);

  return `
  <div class="view stack">
    <section class="card">
      <div class="card-head"><h3>${icon("bell")} Tangga eskalasi alarm</h3><span class="badge">${ESCALATION.length} tahap</span></div>
      <ol class="tl">${ESCALATION.map((e, i) => `
        <li class="${i >= 3 ? "dang" : i >= 2 ? "warn" : "ok"}">
          <div class="row between wrapx"><b>Tahap ${e.level} · ${esc(e.label)}</b>
            <span class="badge mute num">${e.at === 0 ? "tepat waktu" : `+${e.at} menit`}</span></div>
          <div class="small soft">${esc(e.detail)}</div>
        </li>`).join("")}</ol>
    </section>

    <section class="card">
      <div class="card-head"><h3>${icon("alert")} Peringatan terbuka</h3>
        <span class="badge ${open.length ? "dang" : "ok"}">${open.length}</span></div>
      ${open.length ? `<div class="col">${open.map((a) => `
        <div class="card tight flat" style="border-left:4px solid ${a.level >= 3 ? "var(--dang)" : a.level === 2 ? "var(--warn)" : "var(--info)"}">
          <div class="row between wrapx">
            <div class="grow"><div class="row wrapx mb-2">${levelBadge(a.level)}<span class="badge mute">${esc(a.type)}</span>
              <span class="tiny muted">${relTime(a.createdAt)}</span></div>
              <div class="small">${esc(a.message)}</div></div>
            <button class="btn btn-sm btn-ghost" data-act="resolve-alert" data-id="${esc(a.id)}">Tandai selesai</button>
          </div>
        </div>`).join("")}</div>` : emptyState("Tidak ada peringatan terbuka. Semua dosis terpantau.", "check")}
    </section>

    <section class="card">
      <div class="card-head"><h3>Riwayat peringatan</h3></div>
      ${done.length ? `<ul class="lst">${done.slice(0, 12).map((a) => `
        <li><span class="dot ok"></span><div class="grow"><div class="small">${esc(a.message)}</div>
          <div class="tiny muted">${esc(a.type)} · selesai ${relTime(a.resolvedAt || a.createdAt)}</div></div></li>`).join("")}</ul>`
        : emptyState("Belum ada riwayat.", "doc")}
    </section>
  </div>`;
}

/* ============================================================
   VOT
   ============================================================ */
export function votView(s) {
  const { vots, patient, profile } = s;
  if (!patient) return noPatient(profile);
  const canVerify = profile?.role === "dokter" || profile?.role === "pmo";

  return `
  <div class="view stack">
    <div class="grid g-2">
      <section class="card">
        <div class="card-head"><h3>${icon("video")} Rekam sesi VOT</h3><span class="badge">Video Observed Therapy</span></div>
        <div class="cam-stage mb-4" id="camStage">
          <div class="ph" id="camPlaceholder">
            ${icon("video", 32)}
            <div class="small mt-4">Kamera belum aktif</div>
          </div>
          <video id="camVideo" class="hidden" playsinline muted></video>
          <span class="rec-badge hidden" id="recBadge"><span class="dot" style="background:#fff"></span> REC <span id="recTime" class="num">00:00</span></span>
        </div>
        <div class="row wrapx btn-row">
          <button class="btn btn-primary" data-act="cam-start">Aktifkan kamera</button>
          <button class="btn btn-ghost hidden" data-act="cam-record">Mulai rekam</button>
          <button class="btn btn-ghost hidden" data-act="cam-stop">Selesai &amp; kirim</button>
        </div>
        <p class="tiny muted mt-4 mb-0">
          Rekaman diproses di peranti Anda untuk pratinjau. Pada penerapan nyata, video diunggah
          terenkripsi ke penyimpanan rumah sakit sesuai persetujuan pasien.
        </p>
      </section>

      <section class="card">
        <div class="card-head"><h3>Riwayat sesi</h3><span class="badge mute">${vots.length} sesi</span></div>
        ${vots.length ? `<div class="col">${vots.map((v) => `
          <div class="card tight flat">
            <div class="row between wrapx">
              <div><b class="small">${fmtDateTime(v.createdAt)}</b>
                <div class="tiny muted">durasi ${v.durationSec || 0}s${v.verifiedBy ? ` · ditinjau ${esc(v.verifiedBy)}` : ""}</div>
                ${v.note ? `<div class="tiny soft">${esc(v.note)}</div>` : ""}</div>
              <div class="row">
                ${votBadge(v.status)}
                ${canVerify && v.status === "pending" ? `
                  <button class="btn btn-sm btn-ghost" data-act="vot-verify" data-id="${esc(v.id)}" aria-label="Verifikasi sesi">${icon("check", 14)}</button>
                  <button class="btn btn-sm btn-ghost" data-act="vot-reject" data-id="${esc(v.id)}" aria-label="Tolak sesi">${icon("x", 14)}</button>` : ""}
              </div>
            </div>
          </div>`).join("")}</div>` : emptyState("Belum ada sesi VOT terekam.", "video")}
      </section>
    </div>
  </div>`;
}

/* ============================================================
   COMPLAINTS
   ============================================================ */
export function complaintsView(s) {
  const { complaints, patient, profile } = s;
  if (!patient) return noPatient(profile);
  const isDoctor = profile?.role === "dokter";

  return `
  <div class="view stack">
    <section class="card">
      <div class="card-head"><h3>${icon("doc")} Laporan keluhan</h3>
        <button class="btn btn-primary btn-sm" data-act="add-complaint">${icon("plus", 15)} Keluhan baru</button></div>
      ${complaints.length ? `<div class="col">${complaints.map((c) => `
        <div class="card tight flat">
          <div class="row between wrapx mb-2">
            <div class="row wrapx">
              <b>${esc(c.symptom)}</b>
              <span class="badge ${c.severity === "berat" ? "dang" : c.severity === "sedang" ? "warn" : "mute"}">${esc(c.severity)}</span>
              <span class="badge ${c.status === "dijawab" ? "ok" : "warn"}">${esc(c.status)}</span>
            </div>
            <span class="tiny muted">${relTime(c.createdAt)}</span>
          </div>
          <p class="small soft mb-0">${esc(c.note)}</p>
          ${c.response ? `
            <div class="card tight sunken mt-4">
              <div class="tiny upper muted mb-2">Jawaban ${esc(c.respondedBy || "dokter")}</div>
              <div class="small mb-0">${esc(c.response)}</div>
            </div>` : isDoctor ? `
            <button class="btn btn-sm btn-ghost mt-4" data-act="reply-complaint" data-id="${esc(c.id)}">Balas keluhan</button>` : ""}
        </div>`).join("")}</div>` : emptyState("Belum ada keluhan dilaporkan.", "doc")}
    </section>

    <section class="card">
      <div class="card-head"><h3>Efek samping yang umum pada terapi TBC</h3></div>
      <ul class="lst">
        <li><span class="dot warn"></span><div class="grow"><b>Mual dan nyeri lambung</b><div class="tiny muted">Sering pada awal terapi. Atur jarak dengan makan sesuai arahan dokter.</div></div></li>
        <li><span class="dot"></span><div class="grow"><b>Urine kemerahan</b><div class="tiny muted">Efek rifampisin, umumnya tidak berbahaya.</div></div></li>
        <li><span class="dot warn"></span><div class="grow"><b>Kesemutan tangan atau kaki</b><div class="tiny muted">Laporkan agar dokter menilai kebutuhan vitamin B6.</div></div></li>
        <li><span class="dot dang"></span><div class="grow"><b>Kulit atau mata menguning, gangguan penglihatan</b><div class="tiny muted">Segera hubungi dokter, jangan menunggu jadwal kontrol.</div></div></li>
      </ul>
      <p class="tiny muted mt-4 mb-0">Informasi ini bersifat edukatif dan tidak menggantikan penilaian tenaga kesehatan.</p>
    </section>
  </div>`;
}

/* ============================================================
   CHAT
   ============================================================ */
export function chatView(s) {
  const { messages, patient, profile } = s;
  if (!patient) return noPatient(profile);

  return `
  <div class="view card">
    <div class="card-head">
      <h3>${icon("chat")} Komunikasi dua arah</h3>
      <span class="badge mute">${esc(patient.name)} · dokter · PMO</span>
    </div>
    <div class="chat-box mb-4" id="chatBox">
      ${messages.length ? messages.map((m) => `
        <div class="msg ${m.senderId === profile.id ? "me" : ""}">
          <span class="avatar" title="${esc(m.senderName)}">${esc(initials(m.senderName))}</span>
          <div>
            <div class="bubble">${esc(m.text)}</div>
            <div class="meta">${esc(m.senderName)} · ${esc(m.senderRole)} · ${relTime(m.createdAt)}</div>
          </div>
        </div>`).join("") : emptyState("Belum ada pesan. Mulai percakapan dengan tim pendamping.", "chat")}
    </div>
    <form class="row" id="chatForm">
      <label class="sr-only" for="chatInput">Tulis pesan</label>
      <input class="input grow" id="chatInput" placeholder="Tulis pesan untuk dokter atau pengawas…" autocomplete="off" required>
      <button class="btn btn-primary" type="submit" aria-label="Kirim pesan">${icon("send", 16)}</button>
    </form>
    <p class="tiny muted mt-4 mb-0">Untuk keadaan darurat, hubungi layanan gawat darurat, jangan menunggu balasan di aplikasi.</p>
  </div>`;
}

/* ============================================================
   REPORT
   ============================================================ */
export function reportView(s) {
  const { patient, logs, complaints, vots, device, profile } = s;
  if (!patient) return noPatient(profile);

  const adh = adherenceOf(logs);
  const prog = therapyProgress(patient);
  const stock = stockForecast(device);
  const week = last7Days(logs);
  const series = week.map((w) => w.pct);
  const taken = logs.filter((l) => l.status === "taken").length;
  const late = logs.filter((l) => l.status === "late").length;
  const missed = logs.filter((l) => l.status === "missed").length;
  const verified = vots.filter((v) => v.status === "verified").length;

  return `
  <div class="view stack">
    <section class="card">
      <div class="card-head">
        <h3>${icon("chart")} Laporan evaluasi pengobatan</h3>
        <button class="btn btn-sm btn-ghost" data-act="print-report">Cetak / simpan PDF</button>
      </div>
      <div class="grid g-4">
        ${statTile("Kepatuhan", `${adh}%`, `${taken} dosis diminum`, "check")}
        ${statTile("Terlambat", `${late}`, "di luar jam jadwal", "clock", late > 0)}
        ${statTile("Terlewat", `${missed}`, "perlu evaluasi", "alert", missed > 0)}
        ${statTile("VOT terverifikasi", `${verified}`, `dari ${vots.length} sesi`, "video")}
      </div>
      <hr class="divider">
      <div class="grid g-2">
        <div>
          <div class="small upper muted mb-2">Tren kepatuhan mingguan</div>
          ${spark(series)}
        </div>
        <div>
          <div class="small upper muted mb-2">Progres regimen</div>
          <div class="row between small mb-2"><span>${esc(patient.regimen || "-")}</span><span class="num">${prog.pct}%</span></div>
          <div class="bar"><i style="width:${prog.pct}%"></i></div>
          <p class="tiny muted mt-4 mb-0">Berjalan ${prog.days} hari (${prog.weeks} pekan) dari perkiraan ${prog.totalDays} hari. Fase ${esc(patient.phase || "-")}.</p>
        </div>
      </div>
    </section>

    <section class="card">
      <div class="card-head"><h3>Kesimpulan otomatis</h3></div>
      <ul class="lst">
        <li><span class="dot ${adh >= 90 ? "ok" : adh >= 80 ? "warn" : "dang"}"></span>
          <div class="grow"><b>Kepatuhan ${adh >= 90 ? "baik" : adh >= 80 ? "cukup" : "rendah"}</b>
          <div class="small soft">${adh >= 90 ? "Pertahankan pendampingan dan lanjutkan regimen sesuai jadwal."
            : adh >= 80 ? "Tambahkan pengingat dari PMO pada jam rawan terlewat."
            : "Pertimbangkan kunjungan rumah dan tinjau ulang hambatan pasien."}</div></div></li>
        <li><span class="dot ${stock.critical ? "dang" : stock.low ? "warn" : "ok"}"></span>
          <div class="grow"><b>Ketersediaan obat</b>
          <div class="small soft">Sisa ${stock.left} butir, prediksi habis ${fmtDate(stock.runOut)} (${stock.days} hari). ${stock.low ? "Jadwalkan refill segera." : "Stok masih memadai."}</div></div></li>
        <li><span class="dot ${complaints.some((c) => c.severity === "berat") ? "dang" : complaints.length ? "warn" : "ok"}"></span>
          <div class="grow"><b>Keluhan pasien</b>
          <div class="small soft">${complaints.length ? `${complaints.length} keluhan tercatat, ${complaints.filter((c) => c.status === "baru").length} belum dijawab.` : "Tidak ada keluhan tercatat pada periode ini."}</div></div></li>
      </ul>
    </section>

    <section class="card">
      <div class="card-head"><h3>Rincian dosis</h3></div>
      <div class="table-scroll"><table class="tbl">
        <thead><tr><th>Tanggal</th><th>Jadwal</th><th>Status</th><th>Diminum</th><th>VOT</th></tr></thead>
        <tbody>${logs.slice(0, 30).map((l) => `
          <tr><td class="small nowrap">${fmtDate(l.scheduledAt)}</td>
            <td class="num small">${fmtTime(l.scheduledAt)}</td>
            <td>${statusBadge(l.status)}</td>
            <td class="num small">${l.takenAt ? fmtTime(l.takenAt) : "-"}</td>
            <td>${votBadge(l.votStatus)}</td></tr>`).join("")}
        </tbody></table></div>
    </section>
  </div>`;
}

/* ============================================================
   PROFILE
   ============================================================ */
export function profileView(s) {
  const { profile, patients } = s;
  const roleLabel = { dokter: "Dokter", pmo: "Pengawas Minum Obat", pasien: "Pasien" }[profile.role] || profile.role;

  return `
  <div class="view stack">
    <section class="card">
      <div class="card-head"><h3>${icon("users")} Profil saya</h3><span class="badge">${esc(roleLabel)}</span></div>
      <div class="row mb-4"><span class="avatar lg">${esc(initials(profile.name))}</span>
        <div><b>${esc(profile.name)}</b><div class="small muted">${esc(profile.email)}</div></div></div>
      <form class="grid g-2" id="profileForm">
        <div class="field"><label for="pfName">Nama</label>
          <input class="input" id="pfName" value="${esc(profile.name || "")}" required></div>
        <div class="field"><label for="pfPhone">Telepon</label>
          <input class="input" id="pfPhone" type="tel" value="${esc(profile.phone || "")}"></div>
        ${profile.role === "dokter" ? `
          <div class="field"><label for="pfHospital">Rumah sakit</label>
            <input class="input" id="pfHospital" value="${esc(profile.hospital || "")}"></div>
          <div class="field"><label for="pfSpecialty">Spesialisasi</label>
            <input class="input" id="pfSpecialty" value="${esc(profile.specialty || "")}"></div>` : ""}
        ${profile.role === "pmo" ? `
          <div class="field"><label for="pfRelation">Hubungan dengan pasien</label>
            <input class="input" id="pfRelation" value="${esc(profile.relation || "")}"></div>` : ""}
        <div style="grid-column:1/-1"><button class="btn btn-primary" type="submit">Simpan perubahan</button></div>
      </form>
    </section>

    <section class="card">
      <div class="card-head"><h3>Cakupan akses</h3></div>
      <p class="small soft">
        ${profile.role === "dokter" ? "Sebagai dokter, Anda mengendalikan data pasien, dosis obat, pemberian obat, dan penunjukan pengawas minum obat."
          : profile.role === "pmo" ? "Sebagai pengawas, Anda memantau kepatuhan harian, memverifikasi VOT, dan menindaklanjuti alarm."
          : "Sebagai pasien, Anda menerima pengingat, merekam VOT, melaporkan keluhan, dan melihat progres pengobatan."}
      </p>
      <div class="row between wrapx">
        <span class="small muted">Pasien dalam cakupan Anda</span>
        <b class="num">${patients.length}</b>
      </div>
    </section>

    <section class="card">
      <div class="card-head"><h3>Tema tampilan</h3></div>
      <p class="small soft">Pilih antara gaya neumorphism yang lembut atau glassmorphism yang transparan.</p>
      <div id="profileTheme"></div>
    </section>
  </div>`;
}
