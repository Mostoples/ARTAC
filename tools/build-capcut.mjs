/* ============================================================
   ARTA-C — generate a CapCut compile spec from the screenshots.
   Vertical 1080x1920, one photo per beat, captions, transitions.
   Schema follows capcut-cli compile: top-level width/height/fps,
   tracks[].items[], photos need type:"photo".
   ============================================================ */
import { readdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const SHOTS = "shots";
const THEME = process.argv[2] === "glass" ? "glass" : "neu";
const SPEC = `tools/artac-${THEME}.json`;
const PER = 2.6;   // seconds per screenshot
const XFADE = 0.4; // transition length

const files = (await readdir(SHOTS)).filter((f) => f.endsWith(".png")).sort();

/* Narration per beat, in story order. */
const CAPTIONS = {
  "landing-01-hero": "ARTA-C\nSmart medicine box\npasien TBC",
  "landing-02-cara-kerja": "Cara kerja: dari resep dokter\nsampai evaluasi",
  "landing-03-perangkat": "Perangkat IoT\nalarm, sensor, suhu",
  "landing-04-aplikasi": "Aplikasi PMO\nterintegrasi",
  "landing-05-eskalasi-vot": "Alarm eskalasi 5 tahap\n+ Video Observed Therapy",
  "landing-06-kemitraan": "Dokter & rumah sakit\npengendali utama",
  "landing-07-keterbatasan": "Keterbatasan\nkami akui terbuka",
  "app-00-masuk": "Masuk sebagai dokter,\npengawas, atau pasien",
  "dokter-01-ringkasan": "Dasbor dokter\nkepatuhan real-time",
  "dokter-02-pasien": "Daftar pasien\n& status kotak obat",
  "dokter-03-jadwal": "Penjadwalan dosis\ntersinkron ke dispenser",
  "dokter-04-perangkat": "Telemetri kotak obat\nsuhu, baterai, sisa obat",
  "dokter-05-peringatan": "Peringatan bertingkat\nsampai ke dokter",
  "dokter-06-vot": "Verifikasi VOT\nbukti obat diminum",
  "dokter-07-keluhan": "Keluhan pasien\ndibalas dokter",
  "dokter-08-konsultasi": "Komunikasi dua arah",
  "dokter-09-laporan": "Laporan evaluasi\nsiap dicetak",
  "dokter-10-profil": "Profil &\ncakupan akses",
  "dokter-99-menu": "Navigasi ringkas\ndi ponsel",
  "pmo-01-ringkasan": "Dasbor pengawas\nminum obat",
  "pmo-05-peringatan": "PMO menindaklanjuti\nalarm lebih dulu",
  "pasien-01-ringkasan": "Tampilan pasien\npengingat & progres",
  "pasien-05-vot": "Pasien merekam VOT\ndari aplikasi",
};

const captionFor = (f) => {
  for (const [k, v] of Object.entries(CAPTIONS)) if (f.includes(k)) return v;
  return null;
};

const order = [
  ...files.filter((f) => f.startsWith(`${THEME}-landing-`)),
  ...files.filter((f) => f === `${THEME}-app-00-masuk.png`),
  ...files.filter((f) => f.startsWith(`${THEME}-app-dokter-`)),
  ...files.filter((f) => f.startsWith(`${THEME}-app-pmo-`)),
  ...files.filter((f) => f.startsWith(`${THEME}-app-pasien-`)),
];

const picked = order.filter((f) => captionFor(f));
if (!picked.length) throw new Error("no frames matched the storyboard");

const videoItems = [];
const textItems = [];
const operations = [];
let t = 0;

picked.forEach((f, i) => {
  const ref = `shot${i}`;
  videoItems.push({
    ref,
    path: resolve(SHOTS, f).replace(/\\/g, "/"),
    type: "photo",
    start: +t.toFixed(3),
    duration: PER,
  });
  textItems.push({
    text: captionFor(f),
    start: +(t + 0.3).toFixed(3),
    duration: +(PER - 0.6).toFixed(3),
    fontSize: 12,
    color: "#FFFFFF",
    y: -0.74,
  });
  // dissolve into the next shot
  if (i < picked.length - 1) {
    operations.push({ op: "transition", target: ref, slug: "dissolve", duration: XFADE });
  }
  t += PER;
});

const spec = {
  name: `ARTA-C Showcase ${THEME === "glass" ? "Glass" : "Neumorph"}`,
  width: 1080,
  height: 1920,
  fps: 30,
  ratio: "9:16",
  tracks: [
    { type: "video", name: "shots", items: videoItems },
    { type: "text", name: "captions", items: textItems },
  ],
  operations,
};

await writeFile(SPEC, JSON.stringify(spec, null, 2));
console.log(`spec: ${SPEC}`);
console.log(`frames: ${picked.length}, duration: ${t.toFixed(1)}s, theme: ${THEME}`);
