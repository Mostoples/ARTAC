# Panduan Cetak 3D: ARTA-C Portable v2

Panduan untuk mencetak 34 file STL di folder [`stl/`](stl/), disiapkan untuk **Bambu Lab A1 mini (bed 180 × 180 × 180 mm)**. Semua file sudah **diputar ke posisi cetak terbaik**: tinggal impor ke slicer, jangan diputar lagi.

## Ringkasan

| | |
|---|---|
| Jumlah file | 34 STL: 5 part panjang **dibelah dua** (akhiran `_A_bawah` / `_B_atas`) supaya muat bed 180 mm |
| Filamen | ±595 g, jadi **1 rol 1 kg cukup** (sisanya untuk wadah cadangan atau cetak ulang) |
| Waktu cetak | ±22–26 jam di Bambu Lab A1 mini (profil standar 0,20 mm) |
| Printer | **Bambu Lab A1 mini** (180 × 180 mm). Semua part muat; `14_pemandu_kanan` (194 mm) diletakkan **diagonal 45°** |
| Nozzle | 0,4 mm |

> **Part yang dibelah** (sambungan ekor burung/dovetail, dilem setelah dicetak, lihat bagian 6):
> dinding depan, dinding belakang (dibelah di atas layar), dinding kiri, dinding kanan, dan wadah belakang
> (dibelah di sela baris 3–4). Wadah depan dipendekkan menjadi 176 mm supaya muat utuh.

## 1. Bahan

| Bahan | Untuk part | Alasan |
|---|---|---|
| **PLA** | dinding, blok sudut, rel, pemandu, landasan, corong, braket, klem layar, wadah | Mudah dicetak dan cukup kaku |
| **PETG** (disarankan) | roda gigi G1 & G2, pelatuk, engkol servo 3, tuas servo 2, kereta | Bagian bergerak dan menahan beban: lebih ulet, tidak getas, gesekannya lebih halus |

Kalau hanya punya PLA, semua part tetap bisa dicetak dengan PLA. Gigi roda gigi dan pelatuk saja yang lebih cepat aus.

## 2. Setelan slicer (Bambu Studio, profil A1 mini)

| Setelan | Nilai | Catatan |
|---|---|---|
| Layer height | **0,2 mm** | Roda gigi (10, 11) dan pelatuk (05): **0,12–0,16 mm** supaya gigi halus |
| Dinding / perimeter | **3** (≈1,2 mm) | Penting supaya lubang sekrup kuat |
| Top / bottom layer | 4 / 4 | |
| Infill | **20 % gyroid** | Roda gigi, engkol, pelatuk: **40–50 %** |
| Suhu PLA | nozzle 200–210 °C, bed 60 °C | |
| Suhu PETG | nozzle 230–245 °C, bed 75–80 °C, fan 30–50 % | |
| Kecepatan | Profil standar Bambu Studio | Untuk roda gigi dan pelatuk pilih mode *Silent* / kecepatan 50 % supaya lebih presisi |
| Elephant foot compensation | **0,15 mm** | Wajib untuk roda gigi supaya gigi bawah tidak melebar |
| XY hole compensation | 0,1 mm (kalau tersedia) | Membantu lubang M3 dan lubang spline servo |
| Support | **Hanya untuk 04_kereta dan 15_landasan**: "touching build plate / tree support" | Part lain tanpa support |
| Brim | 5 mm untuk part tinggi dan ramping: 12_spacer_G2, 16_corong_baki, 13/14 pemandu | Mencegah terlepas atau goyang |
| Bed | Textured PEI (bawaan A1 mini), suhu sesuai filamen | Bersihkan dengan sabun cuci piring sebelum cetak dinding |

## 3. Cetak uji dulu (±20 menit)

Sebelum mencetak part besar, cetak dua part kecil ini untuk mengecek toleransi printer:

1. **06_engkol_servo3** (0,3 g). Tekan ke spline MG90S.
   - Harus masuk dengan tekanan jari dan tidak goyang.
   - Terlalu sesak: naikkan XY hole compensation 0,05 mm.
   - Terlalu longgar: turunkan, atau tempelkan horn bawaan servo dengan lem.
2. **12_spacer_G2** (0,6 g). Masukkan baut M3, harus lewat tanpa dipaksa.
   Lubang ulir di part lain (Ø2,6 mm) juga harus bisa dimasuki sekrup M3 dengan diputar.

Kalau keduanya pas, setelan sudah siap untuk semua part.

## 4. Urutan cetak per plate (Bambu Lab A1 mini, 180 × 180 mm)

| Plate | Isi | Bahan | ± Waktu* | ± Berat |
|---|---|---|---|---|
| 1 | 10_gear_G1 + 11_gear_G2 + 05_pelatuk + 06_engkol + 07_tuas + 12_spacer + 04_kereta (support) | **PETG** | 2 jam | 26 g |
| 2 | 19_wadah_belakang_B_atas | PLA | 1,5 jam | 30 g |
| 3 | 19_wadah_belakang_A_bawah + 17/18 klem_layar | PLA | 1,5 jam | 27 g |
| 4 | 20_wadah_depan | PLA | 1,5 jam | 40 g |
| 5 | 01_dinding_belakang_A_bawah | PLA | 2,5 jam | 70 g |
| 6 | 01_dinding_belakang_B_atas + 01_dinding_bawah | PLA | 2,5 jam | 78 g |
| 7 | 01_dinding_depan_A_bawah (dudukan layar, kantong baterai, sensor) | PLA | 3 jam | 78 g |
| 8 | 01_dinding_depan_B_atas + 01_dinding_atas | PLA | 2,5 jam | 75 g |
| 9 | 01_dinding_kiri_A + 01_dinding_kiri_B + 01_dinding_kanan_B | PLA | 2 jam | 50 g |
| 10 | 01_dinding_kanan_A + 03_rel_kereta + 13_pemandu_kiri + 15_landasan (support) | PLA | 2,5 jam | 52 g |
| 11 | 14_pemandu_kanan (**diagonal 45°**) + 16_corong_baki + 02_blok_sudut ×4 + 08/09 braket servo | PLA | 2 jam | 45 g |
| 12 | 21_kantong_jari_ppg | **PLA hitam** | 0,7 jam | 15 g |

\*Perkiraan untuk profil standar A1 mini. Angka pasti lihat di Bambu Studio setelah slicing.

Mulai dari **plate 1–4** (mekanisme dan wadah) supaya fungsi mekanisme dan kecocokan blister bisa diuji lebih dulu.
Dinding dicetak belakangan.

## 5. Detail tiap part

| File | Jml | Support | Perhatian khusus |
|---|---|---|---|
| 01_dinding_depan_A/B | 1+1 | – | **Dibelah** di atas layar (7 dovetail). Muka luar menempel di bed (permukaan halus). Di sisi atas ada kantong layar, LiPo, IP5306, ESP32-CAM, cincin buzzer, dan DHT11. Bersihkan lubang lensa kamera Ø9, lubang buzzer, lubang kabel sensor jari 8×4,5 mm, 4 lubang baut kantong jari, dan kisi DHT11. |
| 01_dinding_belakang_A/B | 1+1 | – | **Dibelah** (7 dovetail). Banyak lubang sekrup (countersink di muka luar). Pakai bed bersih; ruangan tanpa angin mencegah warping. |
| 01_dinding_atas | 1 | – | Ada celah tempat wadah masuk. Cek ukurannya pas dengan wadah. |
| 01_dinding_kiri_A/B | 1+1 | – | **Dibelah** di atas port USB-C (2 dovetail). Ada lubang **port USB-C** (10 × 4,6 mm) untuk mengecas dan lubang saklar Ø6,2 mm. Cocokkan dengan modul IP5306 sebelum dicetak. |
| 01_dinding_bawah | 1 | – | – |
| 01_dinding_kanan_A/B | 1+1 | – | **Dibelah** (2 dovetail) |
| 02_blok_sudut_BL/BR/TL/TR | 4 | – | Kecil; BL dan BR lebih panjang (tebal penuh) |
| 03_rel_kereta | 1 | – | Panjang 161 mm. Pastikan lurus (tidak warping). |
| 04_kereta | 1 | **ya** | Support hanya di bawah kait rel dan atap jalur yoke. Bersihkan alur yoke sampai pelatuk bisa maju-mundur dengan lancar. |
| 05_pelatuk | 1 | – | Layer 0,12–0,16 mm. Bantalan depannya yang menekan kubah blister. |
| 06_engkol_servo3 | 1 | – | Masuk ke spline MG90S (lihat cetak uji) |
| 07_tuas_servo2 | 1 | – | Panjang 122 mm, rebah. PETG supaya lentur dan tidak patah. |
| 08_braket_servo2, 09_braket_servo1 | 1+1 | – | – |
| 10_gear_G1_40T, 11_gear_G2_36T-12T | 1+1 | – | Layer 0,12–0,16, elephant foot 0,15, infill 40 %. Cek gigi tidak menempel (bersihkan dengan cutter). |
| 12_spacer_G2 | 1 | – | Pakai brim (tinggi dan ramping) |
| 13_pemandu_kiri, 14_pemandu_kanan | 1+1 | – | 14 sepanjang 194 mm: **putar 45° di bed**. Jalur naik-turun wadah. Permukaan dalam harus halus; ampelas kalau seret. |
| 15_landasan | 1 | **ya** | Support di bawah batang atas. Empat celah miring 45° (tempat kaplet keluar) harus bersih dari sisa support. |
| 16_corong_baki | 1 | – | Tinggi 47 mm. Pakai brim. Permukaan luncur sebaiknya halus supaya kaplet tidak tersangkut. |
| 17/18_klem_layar | 1+1 | – | – |
| 19_wadah_belakang_A/B | 1+1 | – | **Dibelah** di sela baris 3–4 (2 dovetail mini). Rack ada di sisi kiri; setelah dilem, gigi rack harus lurus tanpa undakan. |
| 20_wadah_depan | 1 | – | Utuh, 117 × 176 mm. Jendela kubah 23,5 × 13,5 mm, **miring 45°**. Cocokkan dengan blister asli sebelum mencetak banyak. |
| 21_kantong_jari_ppg | 1 | – | Cetak **PLA hitam** (kedap cahaya, penting untuk sinyal PPG). Lubang jari harus halus; jendela sensor 6×8 mm bersih. Papan MAX30102 dimasukkan dari bawah lalu dikunci lem tembak, sensor menghadap ke atas. |

## 6. Setelah dicetak

1. **Bersihkan** sisa support, stringing, dan bibir bawah (elephant foot), terutama di roda gigi, rack, dan alur.
2. **Lem part yang dibelah** (dinding depan, belakang, kiri, kanan, wadah belakang):
   - Coba pasangkan ekor burung tanpa lem dulu. Harus masuk dengan tekanan jari; kalau sesak, amplas sisi tonjolan.
   - Letakkan kedua belahan di atas kaca atau permukaan rata dengan muka luar menghadap ke bawah, lalu lem dengan lem CA (lem korea/lem G) atau epoksi 5 menit. Tekan rata dan tunggu sampai kering.
   - **Wadah belakang:** pastikan gigi rack di sisi kiri lurus tanpa undakan di sambungan. Amplas tipis bila ada. Wadah depan yang utuh nanti menjepit sambungan ini dengan baut M2 di kedua belahan.
   - Sambungan dinding belakang juga diperkuat oleh part dalam yang dibaut melintasinya (landasan, pemandu).
3. **Lubang M3**: putar sekrup M3 ke tiap lubang Ø2,6 mm sekali untuk "mengulir" plastik, lalu lepas lagi.
4. **Uji fungsi sebelum dirakit**:
   - Pelatuk harus meluncur maju-mundur di alur kereta tanpa macet.
   - Wadah harus turun-naik di pemandu dengan halus. Kalau seret, gosok dengan ampelas 400 atau beri sedikit grafit/lilin.
   - G2 dan rack wadah harus bisa diputar dengan tangan tanpa melompat gigi, termasuk saat melewati sambungan.
   - Blister asli harus masuk ke wadah dan tiap kubah harus pas di jendelanya.
5. Lanjutkan ke perakitan di **PANDUAN_RAKIT.pdf**.

## 7. Masalah yang sering terjadi

| Masalah | Penyebab | Solusi |
|---|---|---|
| Dinding besar melengkung (warping) | Bed kurang panas atau ada angin | Bed 60 °C (PLA), lem stik/PEI bersih, brim 5 mm, tutup printer |
| Roda gigi macet atau berisik | Elephant foot atau gigi kasar | Kompensasi 0,15 mm, layer 0,12 mm, ampelas sisi gigi, beri sedikit grease silikon |
| Lubang sekrup terlalu kecil | Printer over-extrusion | Kalibrasi flow (e-steps / flow rate), atau bor Ø2,5 mm |
| Engkol atau G1 longgar di spline servo | Toleransi printer | Lem horn bawaan servo ke part, atau cetak ulang dengan kompensasi lebih kecil |
| Kubah blister tidak pas di jendela wadah | Ukuran blister berbeda dari perkiraan | Ukur blister, ubah `BL_W, BL_H, CAP_L, CAP_W, TILT, GAP_X, GAP_Z` di `build.py`, lalu jalankan `python build.py` |

## 8. Bahan non-cetak

Daftar lengkap (jumlah dihitung dari model) ada di **PANDUAN_RAKIT.pdf** bagian 1. Ringkasnya:

- Sekrup **M3 × 10** kepala countersink ±37 (beli 45), **M3 × 12** + mur ×4, **M3 × 40** + mur nyloc + 2 ring ×1 (poros G2), **M2 × 8** ×6
- **MG90S** ×3, **PCA9685** ×1, **ESP32-2432S028 (CYD)** ×1, **LiPo 103450** ×1, **IP5306 (USB-C)** ×1, kapasitor 1000 µF ×1
- **ESP32-CAM** (OV2640) ×1 + adaptor USB-TTL untuk upload pertama, **MAX30102** ×1, **DHT11** ×1, **buzzer aktif 5 V Ø12 mm** ×1, transistor S8050/2N2222 + resistor 1 kΩ, saklar toggle mini Ø6 ×1
- **Lem CA atau epoksi** untuk sambungan part yang dibelah; lem tembak (hot glue) untuk mengunci ESP32-CAM, MAX30102, DHT11, dan buzzer
