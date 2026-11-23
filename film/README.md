# ARTA-C — "Day 47" (film dokumenter pendek, 90 detik, English)

Film untuk lomba internasional **I2ASPO**. Cerita: pagi ke-47 seorang pasien TB. Film menunjukkan kenapa dosis
sering terlewat, peran PMO, lalu bagaimana ARTA-C memastikan setiap dosis diminum dan terverifikasi.

**Hasil:** `ARTA-C_Day47_documentary.mp4`
- Video: 1920×1080, 24 fps, letterbox 2.35:1, H.264 CRF 17.
- Audio: AAC 192k, −17 LUFS.
- Subtitle bahasa Inggris dibakar (burned-in) di bilah bawah.

## Struktur adegan

| Waktu | Adegan | Isi |
|---|---|---|
| 0–8.5 s | `dawn` (3D) | Meja dapur subuh, cahaya kerai, ARTA-C di samping mug: "Tuberculosis is curable…" |
| 8.5–17 s | `days` (2D) | 180 titik pagi menyala satu per satu: "Six months. One hundred and eighty mornings." |
| 17–24 s | `slip` (2D) | Minggu ke-3: pasien merasa sembuh, dosis mulai bolong (titik merah) |
| 24–35 s | `pmo` (2D) | Jaringan PMO dan pasien; pagi tiba dan pengawas tak bisa hadir di semua rumah |
| 35–41.5 s | `reveal` (3D) | Studio gelap, rim light biru, layar menyala: "ARTA-C." |
| 41.5–46 s | `face` (3D) | POV pasien: ESP32-CAM verifikasi wajah |
| 46–52.5 s | `ppg` (3D) | Jari masuk terowongan PPG (MAX30102): nadi dan SpO2 |
| 52.5–59.5 s | `inside` (3D) | Dinding transparan: blister asli turun baris demi baris (gear + rack), kereta bergeser |
| 59.5–68 s | `peck` (3D) | Cutaway x-ray: pelatuk mendorong satu kaplet menembus foil lalu jatuh ke baki |
| 68–77 s | `notify` (3D + 2D) | Layar "Dose complete"; ponsel PMO menerima "Dose taken · verified" |
| 77–82.5 s | `count` (2D) | Day 47: 47 titik terisi, "133 to go · zero missed" |
| 82.5–90 s | `end` (3D) | Kartu akhir: ARTA-C · Smart TB Medication Companion · "No dose goes unseen." |

## Cara membangun ulang

```bash
python naskah.py        # narasi TTS per baris (edge-tts, en-US-ChristopherNeural) -> audio/vo_*.mp3 + vo.json
python film.py all      # render 3D Blender 5.2 EEVEE -> _frames/<shot>/f_####.png  (±1 jam)
python film.py peck --test 40,85   # uji beberapa frame saja
python audio.py         # musik (sintesis numpy), efek suara tersinkron, ducking, loudnorm -> audio/mix.wav
python edit.py          # grafis 2D, overlay, subtitle, grade, encode -> ARTA-C_Day47_documentary.mp4
python edit.py --still 12,40.5,72.5     # cuplikan QA -> _qa/
```

- `timeline.py` adalah sumber kebenaran waktu (segmen, narasi, efek suara), dipakai oleh `audio.py` dan `edit.py`.
- Kinematika di `film.py` sama dengan halaman showcase web (`public/showcase/index.html`) dan berasal dari `artac.glb`.

## Catatan kejujuran (penting untuk juri)
- Semua gambar alat adalah **visualisasi 3D dari desain**, bukan rekaman prototipe fisik. Kartu akhir menyebut
  "Concept prototype · 3D visualisation".
- Narasi hanya mengklaim **nadi dan SpO2** dari sensor PPG. Estimasi tekanan darah dan gula darah sengaja tidak
  disebut karena masih eksperimental dan bukan alat diagnosis.
- Data pasien di ponsel (Patient #047, HR 78, SpO2 98%) adalah contoh ilustrasi.
- Musik dan efek suara disintesis sendiri (bebas lisensi). Suara narasi memakai Microsoft Edge neural TTS. Periksa
  aturan lomba soal suara sintetis; bila perlu, rekam ulang narasi dengan suara manusia memakai naskah di `naskah.py`.
