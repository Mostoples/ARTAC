# ARTA-C: UI layar alat (LVGL 8.3, ESP32 CYD 2,8")

Sepuluh layar bergaya "glass depth" (token AQUENT), dengan ikon 3D dari Blender:

| Layar | Isi |
|---|---|
| Splash (`UI_BOOT`) | Logo |
| Beranda (`UI_HOME`) | Cincin dosis berikut, hari pengobatan, sisa blister, kepatuhan minggu ini, suhu, kelembapan, baterai |
| Alarm (`UI_ALARM`) | Hitung mundur 60 menit, tombol "I'm ready" / tunda |
| Verifikasi wajah (`UI_FACE`) | Bingkai kamera + garis pindai, progres pencocokan |
| Cek PPG (`UI_PPG`) | Detak jantung + grafik gelombang langsung, SpO₂, estimasi tekanan darah dan gula darah (bertanda *) |
| Dispensing (`UI_DISPENSE`) | Peta blister 4×7 (kosong / sedang / penuh), progres kaplet |
| Selesai (`UI_DONE`) | Hijau, terkirim ke PMO, streak |
| Isi ulang (`UI_REFILL`) | 3 langkah untuk PMO |
| Dosis terlewat (`UI_MISSED`) | Merah, PMO sudah diberi tahu |
| Pengaturan (`UI_SETTINGS`) | Bahasa EN/ID, Wi-Fi, volume, kalibrasi, daftar ulang wajah |

Semua teks tersedia dalam **English** dan **Bahasa Indonesia** (`ui_state()->lang_id`).

## Build

- **Library:** `lvgl` 8.3.x dan `GFX Library for Arduino` 1.6.x.
- **lv_conf.h:** `LV_COLOR_DEPTH 16`, `LV_COLOR_16_SWAP 1`, `LV_MEM_SIZE` ≥ 48 KB.
- **Board:** *ESP32 Dev Module*, **Partition Scheme: Huge APP**.
- **Ukuran hasil build:** ±913 KB. Sudah dikompilasi dengan arduino-cli, esp32 core 3.3.7.
- Pin layar (HSPI) dan sentuh (XPT2046, bit-bang) ditulis di `.ino`, jadi `User_Setup` TFT_eSPI tidak dipakai.
- `DEMO_MODE 1`: layar berganti otomatis mengikuti alur satu jadwal (untuk presentasi/video).
- Logika asli memakai API berikut:
  - `ui_show(UI_x)`: pindah layar
  - `ui_state()`: ubah data, lalu panggil `ui_refresh()`
  - `ui_ppg_push(sample)`: kirim satu sampel gelombang PPG
  - `ui_set_action_cb(cb)`: terima aksi tombol

## Regenerasi aset

| Yang dibuat ulang | Perintah |
|---|---|
| Ikon 3D | `blender -b --factory-startup -P ../../ui3d/ikon3d.py -- ../../ui3d/ikon` |
| Array gambar (`ui_img.c`) | `python ../../ui3d/buat_aset_lvgl.py` |
| Font (`pj_*.c`) | `npx lv_font_conv --font PlusJakartaSans-*.ttf --size N --bpp 4 --format lvgl -r 0x20-0x7E,0xB0,0xB7,0x2022,0x2026,0x203A` |

Mockup acuan (piksel sama) ada di `ui3d/layar_alat.html`, dan hasil tangkapannya di `ui3d/layar/`.
