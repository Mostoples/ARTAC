/* ============================================================
   ARTA-C — landing page content rendering
   ============================================================ */

import { $, icon, esc } from "./ui.js";
import { mountThemeSwitch } from "./theme.js";
import { ESCALATION } from "./logic.js";
import {
  enableAnim, observeReveal, revealNow, countUp, scrollProgress, tilt,
} from "./anim.js";

enableAnim();
mountThemeSwitch($("#themeSwitch"));

/* ---------------- how it works ---------------- */
const STEPS = [
  { n: 1, t: "Dokter menjadwalkan", d: "Dosis, jam minum, dan regimen diinput dokter pada aplikasi yang tersinkron dengan dispenser." },
  { n: 2, t: "Obat dimasukkan", d: "Petugas atau PMO mengisi kotak sesuai jadwal, jumlah butir tercatat sebagai stok awal." },
  { n: 3, t: "Alarm berbunyi", d: "Pada waktu yang ditentukan dispenser mengeluarkan suara dan tanda visual sebagai pengingat." },
  { n: 4, t: "Pasien menekan tombol", d: "Pembuka otomatis melepas bungkus obat, sensor gerak mencatat respons pasien." },
  { n: 5, t: "Verifikasi VOT", d: "Pasien merekam video singkat saat minum obat, PMO dan dokter meninjau bukti menelan." },
  { n: 6, t: "Laporan & evaluasi", d: "Sistem menyusun laporan kepatuhan, keluhan, dan perkembangan kondisi secara berkala." },
];

$("#steps").innerHTML = STEPS.map((s, i) => `
  <article class="card hover" data-reveal style="--i:${i}">
    <div class="row mb-4"><span class="step-n">${s.n}</span><h3 class="mb-0">${esc(s.t)}</h3></div>
    <p class="soft small mb-0">${esc(s.d)}</p>
  </article>`).join("");

/* ---------------- hardware ---------------- */
const HARDWARE = [
  { i: "pill", t: "Pembuka obat otomatis", d: "Satu tekanan tombol melepas bungkus obat, membantu pasien lanjut usia dan yang kesulitan membuka blister." },
  { i: "bell", t: "Alarm peringatan berjam", d: "Suara dan indikator visual pada jam minum yang dijadwalkan dokter, dapat diulang bila belum direspons." },
  { i: "motion", t: "Sensor deteksi gerakan", d: "Mendeteksi saat obat diambil dari kotak, menjadi dasar ceklist otomatis kepatuhan." },
  { i: "temp", t: "Pengatur suhu ruang", d: "Menjaga suhu kompartemen tetap stabil pada 15–28°C agar potensi obat tidak menurun." },
  { i: "eye", t: "Tampilan sisa obat", d: "Layar menampilkan jumlah butir tersisa, jadwal berikutnya, dan status koneksi kotak." },
  { i: "video", t: "Kamera terhubung aplikasi", d: "Kamera untuk sesi VOT yang bisa langsung diakses PMO melalui aplikasi." },
];

$("#hardware").innerHTML = HARDWARE.map((h, i) => `
  <article class="card hover" data-reveal style="--i:${i}">
    <div class="row mb-4"><span class="tile-icon">${icon(h.i, 20)}</span><h3 class="mb-0">${esc(h.t)}</h3></div>
    <p class="soft small mb-0">${esc(h.d)}</p>
  </article>`).join("");

/* ---------------- app features ---------------- */
const APPFEAT = [
  { i: "dashboard", t: "Dasbor pengawas", d: "Laporan peminuman obat dan kondisi terkini pasien dalam satu tampilan." },
  { i: "chat", t: "Komunikasi dua arah", d: "Pesan antara pasien, PMO, dan dokter tersimpan pada satu riwayat percakapan." },
  { i: "alert", t: "Alarm eskalasi", d: "Bila dosis tak direspons, notifikasi naik bertahap dari kotak ke pasien, PMO, lalu dokter." },
  { i: "doc", t: "Keluhan pasien", d: "Pasien melaporkan efek samping dengan tingkat keparahan, dokter membalas langsung." },
  { i: "chart", t: "Durasi & prediksi habis", d: "Menghitung lama pengobatan berjalan dan memperkirakan tanggal obat habis." },
  { i: "stetho", t: "Konsultasi dokter", d: "Tanya jawab klinis tanpa harus menunggu jadwal kontrol berikutnya." },
  { i: "check", t: "Ceklist otomatis", d: "Status dosis terisi otomatis dari sensor kotak, tetap bisa dikoreksi manual oleh PMO." },
  { i: "refresh", t: "Indikasi pengulangan", d: "Menandai kemungkinan dosis ganda bila kotak dibuka dua kali dalam rentang berdekatan." },
];

$("#appfeat").innerHTML = APPFEAT.map((f, i) => `
  <article class="card hover" data-reveal style="--i:${i}">
    <div class="row mb-4"><span class="tile-icon">${icon(f.i, 20)}</span><h3 class="mb-0">${esc(f.t)}</h3></div>
    <p class="soft small mb-0">${esc(f.d)}</p>
  </article>`).join("");

/* ---------------- escalation ladder ---------------- */
$("#escList").innerHTML = ESCALATION.map((s, i) => `
  <li class="${i >= 3 ? "dang" : i >= 2 ? "warn" : ""}">
    <div class="row between wrapx">
      <b>Tahap ${s.level} · ${esc(s.label)}</b>
      <span class="badge mute num">${s.at === 0 ? "tepat waktu" : `+${s.at} menit`}</span>
    </div>
    <div class="small soft">${esc(s.detail)}</div>
  </li>`).join("");

/* ---------------- roles ---------------- */
const ROLES = [
  { i: "stetho", t: "Dokter & rumah sakit", d: "Kunci pengendali utama: input data pasien, dosis obat, pemberian obat, dan penunjukan PMO." },
  { i: "users", t: "Pengawas minum obat", d: "Memantau dasbor harian, memverifikasi VOT, dan menindaklanjuti alarm eskalasi." },
  { i: "shield", t: "Pasien", d: "Menerima pengingat, merekam VOT, melaporkan keluhan, dan melihat progres pengobatan." },
];

$("#roles").innerHTML = ROLES.map((r, i) => `
  <article class="card hover" data-reveal style="--i:${i}">
    <div class="row mb-4"><span class="tile-icon">${icon(r.i, 20)}</span><h3 class="mb-0">${esc(r.t)}</h3></div>
    <p class="soft small mb-0">${esc(r.d)}</p>
  </article>`).join("");

/* ---------------- limitations ---------------- */
const LIMITS = [
  { t: "Kotak tertinggal atau tidak dibawa", d: "Status offline lebih dari beberapa jam memicu peringatan pada dasbor PMO." },
  { t: "Ponsel pasien disenyapkan", d: "Karena itu alarm utama tetap berada pada perangkat kotak, bukan hanya notifikasi ponsel." },
  { t: "Refill masih manual sebulan sekali", d: "Prediksi obat habis membantu penjadwalan, namun pengisian tetap dilakukan petugas." },
  { t: "Belum menyediakan obat jangka panjang", d: "Kapasitas kompartemen terbatas, sehingga fase lanjutan perlu beberapa siklus pengisian." },
];

$("#limits").innerHTML = LIMITS.map((l) => `
  <div class="limit-item">
    <span class="tile-icon">${icon("alert", 18)}</span>
    <div><b>${esc(l.t)}</b><div class="small soft">${esc(l.d)}</div></div>
  </div>`).join("");

/* smooth in-page scroll for nav links */
document.querySelectorAll('a[href^="#"]').forEach((a) => {
  a.addEventListener("click", (e) => {
    const id = a.getAttribute("href").slice(1);
    const target = document.getElementById(id);
    if (!target) return;
    e.preventDefault();
    target.scrollIntoView({ behavior: "smooth", block: "start" });
  });
});

/* ---------------- motion ---------------- */
// the hero sits above the fold, so it plays at once rather than on scroll
revealNow($(".hero"));
countUp($(".hero"));

// everything below the fold, including the cards injected above
observeReveal();
scrollProgress();
tilt($(".device"));

