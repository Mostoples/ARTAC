// ARTA-C device UI (LVGL 8.3) - konsep B "glass depth", layar CYD 320x240.
#pragma once
#include "lvgl.h"

typedef enum {
  UI_BOOT, UI_HOME, UI_ALARM, UI_FACE, UI_PPG, UI_DISPENSE, UI_DONE, UI_REFILL, UI_MISSED, UI_SETTINGS, UI_COUNT
} ui_screen_t;

typedef enum {   // aksi dari tombol layar -> logika aplikasi
  UI_ACT_READY, UI_ACT_SNOOZE, UI_ACT_TAKE_NOW, UI_ACT_CALL_PMO, UI_ACT_REFILL_START,
  UI_ACT_CALIBRATE, UI_ACT_ENROLL_FACE, UI_ACT_LANGUAGE, UI_ACT_HOME
} ui_action_t;

typedef struct {
  char clock[6];          // "06:52"
  int temp_c, humidity, battery;
  char next_dose[6];      // "07:00"
  int minutes_to_dose;
  int caplets_per_dose;
  int day, total_days;
  int blister_left;       // dari 28
  int week_taken;         // 0..7
  int alarm_left_s;       // hitung mundur respon
  int face_progress;      // 0..100
  int hr, spo2, bp_sys, bp_dia, glucose;   // bp & glucose = estimasi
  bool finger;
  int disp_i, disp_n, blister_row;
  uint32_t taken_mask;    // bit (row*4+col) = kantong sudah kosong
  char done_time[6];
  int streak;
  char wifi[24];
  char device_id[20];
  bool lang_id;           // false = English, true = Bahasa Indonesia
} ui_state_t;

void ui_init(void);
void ui_show(ui_screen_t s);
ui_screen_t ui_current(void);
ui_state_t *ui_state(void);
void ui_refresh(void);                  // tulis ulang label dari state
void ui_ppg_push(int16_t sample);       // satu sampel gelombang PPG (0..100)
void ui_set_action_cb(void (*cb)(ui_action_t));
