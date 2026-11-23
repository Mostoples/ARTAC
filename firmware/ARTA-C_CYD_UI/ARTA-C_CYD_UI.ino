/*
  ARTA-C - UI layar alat (ESP32-2432S028 "CYD" 2,8" ILI9341 + sentuh XPT2046), LVGL 8.3.

  Library: lvgl 8.3.x (lv_conf.h: LV_COLOR_DEPTH 16, LV_COLOR_16_SWAP 1), GFX Library for Arduino 1.6.x.
  Board  : "ESP32 Dev Module", Partition Scheme "Huge APP (3MB No OTA)" (font + gambar ±1,1 MB).
  Pin CYD sudah ditulis di sini, jadi User_Setup TFT_eSPI global tidak perlu diubah.

  DEMO_MODE 1 : layar berganti otomatis (alur satu jadwal) + tombol sentuh aktif - untuk presentasi/video.
  DEMO_MODE 0 : panggil ui_show()/ui_state() dari logika jadwal, servo, PPG (lihat dokumen teknis bab 6).
*/
#include <Arduino.h>
#include <Arduino_GFX_Library.h>
#include <lvgl.h>
#include "ui.h"

#define DEMO_MODE 1

// ---- layar ILI9341 (HSPI) ----
#define TFT_DC 2
#define TFT_CS 15
#define TFT_SCK 14
#define TFT_MOSI 13
#define TFT_MISO 12
#define TFT_BL 21
// ---- sentuh XPT2046 (SPI terpisah, bit-bang) ----
#define T_CLK 25
#define T_MOSI 32
#define T_MISO 39
#define T_CS 33
#define T_IRQ 36
#define T_XMIN 200   // kalibrasi mentah (sesuaikan bila sentuhan meleset)
#define T_XMAX 3700
#define T_YMIN 240
#define T_YMAX 3800

Arduino_DataBus *bus = new Arduino_ESP32SPI(TFT_DC, TFT_CS, TFT_SCK, TFT_MOSI, TFT_MISO, HSPI);
Arduino_GFX *gfx = new Arduino_ILI9341(bus, GFX_NOT_DEFINED, 1 /* landscape */);

static lv_disp_draw_buf_t draw_buf;
static lv_color_t *buf1;

static void flush_cb(lv_disp_drv_t *d, const lv_area_t *a, lv_color_t *px) {
  gfx->draw16bitBeRGBBitmap(a->x1, a->y1, (uint16_t *)px, a->x2 - a->x1 + 1, a->y2 - a->y1 + 1);
  lv_disp_flush_ready(d);
}

static uint16_t xpt_read(uint8_t cmd) {
  digitalWrite(T_CS, LOW);
  for (int i = 7; i >= 0; i--) {
    digitalWrite(T_MOSI, (cmd >> i) & 1);
    digitalWrite(T_CLK, HIGH); digitalWrite(T_CLK, LOW);
  }
  uint16_t v = 0;
  for (int i = 0; i < 16; i++) {
    digitalWrite(T_CLK, HIGH);
    v = (v << 1) | digitalRead(T_MISO);
    digitalWrite(T_CLK, LOW);
  }
  digitalWrite(T_CS, HIGH);
  return v >> 4;
}

static void touch_cb(lv_indev_drv_t *, lv_indev_data_t *data) {
  if (digitalRead(T_IRQ) == HIGH) { data->state = LV_INDEV_STATE_REL; return; }
  uint32_t sx = 0, sy = 0;
  for (int i = 0; i < 4; i++) { sx += xpt_read(0xD0); sy += xpt_read(0x90); }
  int x = map(sx / 4, T_XMIN, T_XMAX, 0, 320), y = map(sy / 4, T_YMIN, T_YMAX, 0, 240);
  data->point.x = constrain(x, 0, 319);
  data->point.y = constrain(y, 0, 239);
  data->state = LV_INDEV_STATE_PR;
}

// ---- aksi tombol -> alur ----
static void on_action(ui_action_t a) {
  ui_state_t *s = ui_state();
  switch (a) {
    case UI_ACT_READY: case UI_ACT_TAKE_NOW: s->face_progress = 0; ui_show(UI_FACE); break;
    case UI_ACT_SNOOZE: case UI_ACT_HOME: ui_show(UI_HOME); break;
    case UI_ACT_LANGUAGE: s->lang_id = !s->lang_id; ui_show(UI_SETTINGS); break;
    case UI_ACT_REFILL_START: ui_show(UI_HOME); break;
    default: break;
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(TFT_BL, OUTPUT); digitalWrite(TFT_BL, HIGH);
  pinMode(T_CLK, OUTPUT); pinMode(T_MOSI, OUTPUT); pinMode(T_CS, OUTPUT); pinMode(T_MISO, INPUT); pinMode(T_IRQ, INPUT);
  digitalWrite(T_CS, HIGH);
  gfx->begin(40000000);
  gfx->fillScreen(0x0000);

  lv_init();
  buf1 = (lv_color_t *)heap_caps_malloc(320 * 40 * sizeof(lv_color_t), MALLOC_CAP_DMA);
  lv_disp_draw_buf_init(&draw_buf, buf1, NULL, 320 * 40);
  static lv_disp_drv_t dd;
  lv_disp_drv_init(&dd);
  dd.hor_res = 320; dd.ver_res = 240;
  dd.flush_cb = flush_cb;
  dd.draw_buf = &draw_buf;
  lv_disp_drv_register(&dd);
  static lv_indev_drv_t id;
  lv_indev_drv_init(&id);
  id.type = LV_INDEV_TYPE_POINTER;
  id.read_cb = touch_cb;
  lv_indev_drv_register(&id);

  ui_init();
  ui_set_action_cb(on_action);
}

#if DEMO_MODE
// urutan demo: boot -> beranda -> alarm -> wajah -> PPG -> dispensing -> selesai -> (terlewat, isi ulang, pengaturan)
static const ui_screen_t demo[] = {UI_HOME, UI_ALARM, UI_FACE, UI_PPG, UI_DISPENSE, UI_DONE, UI_MISSED, UI_REFILL, UI_SETTINGS};
static uint8_t di = 0;
static uint32_t t_next = 2500, t_tick = 0;
static float ph = 0;
#endif

void loop() {
  static uint32_t last = millis();
  uint32_t now = millis();
  lv_tick_inc(now - last);
  last = now;
  lv_timer_handler();
#if DEMO_MODE
  ui_state_t *s = ui_state();
  if (now > t_next) {
    ui_screen_t sc = demo[di];
    di = (di + 1) % (sizeof demo / sizeof demo[0]);
    if (sc == UI_FACE) s->face_progress = 0;
    if (sc == UI_DISPENSE) s->disp_i = 1;
    ui_show(sc);
    t_next = now + (sc == UI_FACE || sc == UI_PPG || sc == UI_DISPENSE ? 6000 : 4000);
  }
  if (now - t_tick > 30) {          // animasi nilai
    t_tick = now;
    ph += 0.21f;
    float beat = fmodf(ph, 6.2832f);
    int v = 45 + (int)(10 * sinf(ph * 0.5f));
    if (beat < 0.5f) v += (int)(50 * sinf(beat * 6.2832f));
    ui_ppg_push(constrain(v, 0, 100));
    if (ui_current() == UI_FACE && s->face_progress < 100) { s->face_progress++; ui_refresh(); }
    if (ui_current() == UI_DISPENSE && (now / 1800) % 2 == 0 && s->disp_i < s->disp_n) {
      static uint32_t lastd = 0;
      if (now - lastd > 1800) { lastd = now; s->disp_i++; s->taken_mask |= 1UL << (4 + s->disp_i - 2); ui_refresh(); }
    }
    if (ui_current() == UI_ALARM && s->alarm_left_s > 0 && (now % 1000) < 31) { s->alarm_left_s--; ui_refresh(); }
  }
#endif
  delay(5);
}
