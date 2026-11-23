// ARTA-C device UI (LVGL 8.3) - 10 layar sesuai mockup ui3d/layar_alat.html (konsep B).
// Layar dibangun saat ditampilkan dan layar lama dihapus, supaya muat di LV_MEM_SIZE 48 KB.
#include "ui.h"
#include "ui_img.h"
#include <stdio.h>
#include <string.h>

LV_FONT_DECLARE(pj_600_10)
LV_FONT_DECLARE(pj_600_11)
LV_FONT_DECLARE(pj_700_9)
LV_FONT_DECLARE(pj_700_13)
LV_FONT_DECLARE(pj_800_16)
LV_FONT_DECLARE(pj_800_22)
LV_FONT_DECLARE(pj_800_30)
LV_FONT_DECLARE(pj_800_40)

#define C_INK   lv_color_hex(0xF3F7FF)
#define C_INK2  lv_color_hex(0xBFD3FF)
#define C_MUT   lv_color_hex(0x86A2D6)
#define C_BLUE  lv_color_hex(0x5FA2FF)
#define C_DEEP  lv_color_hex(0x2F7BFF)
#define C_OK    lv_color_hex(0x3CE3A0)
#define C_WARN  lv_color_hex(0xFFC24D)
#define C_RED   lv_color_hex(0xFF5A72)

static ui_state_t S;
static ui_screen_t cur = UI_BOOT;
static lv_obj_t *scr = NULL;
static void (*act_cb)(ui_action_t) = NULL;
static lv_style_t st_card, st_hero, st_row, st_btn, st_ghost, st_red;
static bool styles_ok = false;

// objek dinamis (diisi ulang oleh ui_refresh)
static lv_obj_t *l_clock, *l_temp, *l_hum, *l_batt, *l_next, *l_minutes, *l_caps, *l_day, *l_dayof, *l_left, *l_week;
static lv_obj_t *arc_next, *l_alarm_cd, *arc_face, *l_face, *l_hr, *l_spo2, *l_bp, *l_glu, *chart;
static lv_chart_series_t *ser;
static lv_obj_t *l_disp, *bar_disp, *cells[28], *l_done1, *l_done2;

#define TX(en, id) (S.lang_id ? (id) : (en))

// ------------------------------------------------------------------ gaya
static void styles(void) {
  if (styles_ok) return;
  styles_ok = true;
  lv_style_init(&st_card);
  lv_style_set_radius(&st_card, 14);
  lv_style_set_bg_color(&st_card, lv_color_hex(0x3A62B4));
  lv_style_set_bg_grad_color(&st_card, lv_color_hex(0x1B336F));
  lv_style_set_bg_grad_dir(&st_card, LV_GRAD_DIR_VER);
  lv_style_set_bg_opa(&st_card, LV_OPA_60);
  lv_style_set_border_color(&st_card, lv_color_white());
  lv_style_set_border_opa(&st_card, LV_OPA_20);
  lv_style_set_border_width(&st_card, 1);
  lv_style_set_shadow_color(&st_card, lv_color_black());
  lv_style_set_shadow_opa(&st_card, LV_OPA_40);
  lv_style_set_shadow_width(&st_card, 14);
  lv_style_set_shadow_ofs_y(&st_card, 5);
  lv_style_set_pad_all(&st_card, 0);

  lv_style_init(&st_hero);
  lv_style_set_shadow_color(&st_hero, C_DEEP);
  lv_style_set_shadow_opa(&st_hero, LV_OPA_60);
  lv_style_set_shadow_width(&st_hero, 22);
  lv_style_set_border_color(&st_hero, lv_color_hex(0x8CC6FF));
  lv_style_set_border_opa(&st_hero, LV_OPA_50);

  lv_style_init(&st_row);
  lv_style_set_radius(&st_row, 11);
  lv_style_set_bg_color(&st_row, lv_color_white());
  lv_style_set_bg_opa(&st_row, LV_OPA_10);
  lv_style_set_border_color(&st_row, lv_color_white());
  lv_style_set_border_opa(&st_row, LV_OPA_20);
  lv_style_set_border_width(&st_row, 1);
  lv_style_set_pad_all(&st_row, 0);

  lv_style_init(&st_btn);
  lv_style_set_radius(&st_btn, LV_RADIUS_CIRCLE);
  lv_style_set_bg_color(&st_btn, C_BLUE);
  lv_style_set_bg_grad_color(&st_btn, lv_color_hex(0x1646D6));
  lv_style_set_bg_grad_dir(&st_btn, LV_GRAD_DIR_HOR);
  lv_style_set_bg_opa(&st_btn, LV_OPA_COVER);
  lv_style_set_shadow_color(&st_btn, C_DEEP);
  lv_style_set_shadow_opa(&st_btn, LV_OPA_50);
  lv_style_set_shadow_width(&st_btn, 14);
  lv_style_set_shadow_ofs_y(&st_btn, 5);
  lv_style_set_text_color(&st_btn, lv_color_white());
  lv_style_set_text_font(&st_btn, &pj_800_16);

  lv_style_init(&st_ghost);
  lv_style_set_radius(&st_ghost, LV_RADIUS_CIRCLE);
  lv_style_set_bg_color(&st_ghost, lv_color_white());
  lv_style_set_bg_opa(&st_ghost, LV_OPA_10);
  lv_style_set_border_color(&st_ghost, lv_color_white());
  lv_style_set_border_opa(&st_ghost, LV_OPA_20);
  lv_style_set_border_width(&st_ghost, 1);
  lv_style_set_shadow_width(&st_ghost, 0);
  lv_style_set_text_color(&st_ghost, C_INK2);
  lv_style_set_text_font(&st_ghost, &pj_700_13);

  lv_style_init(&st_red);
  lv_style_set_bg_color(&st_red, lv_color_hex(0xFF7A8E));
  lv_style_set_bg_grad_color(&st_red, lv_color_hex(0xC3264A));
  lv_style_set_shadow_color(&st_red, C_RED);
}

// ------------------------------------------------------------------ pembantu
static lv_obj_t *base(const lv_img_dsc_t *bg) {
  lv_obj_t *s = lv_obj_create(NULL);
  lv_obj_clear_flag(s, LV_OBJ_FLAG_SCROLLABLE);
  lv_obj_set_style_bg_color(s, lv_color_hex(0x0B1E4A), 0);
  lv_obj_t *im = lv_img_create(s);
  lv_img_set_src(im, bg);
  lv_img_set_pivot(im, 0, 0);
  lv_img_set_zoom(im, 512);            // latar 160x120 diperbesar 2x
  lv_img_set_antialias(im, true);
  lv_obj_set_pos(im, 0, 0);
  return s;
}

static lv_obj_t *card(lv_obj_t *p, int x, int y, int w, int h, bool hero) {
  lv_obj_t *o = lv_obj_create(p);
  lv_obj_remove_style_all(o);
  lv_obj_add_style(o, &st_card, 0);
  if (hero) lv_obj_add_style(o, &st_hero, 0);
  lv_obj_set_pos(o, x, y);
  lv_obj_set_size(o, w, h);
  lv_obj_clear_flag(o, LV_OBJ_FLAG_SCROLLABLE | LV_OBJ_FLAG_CLICKABLE);
  return o;
}

static lv_obj_t *label(lv_obj_t *p, int x, int y, const char *t, const lv_font_t *f, lv_color_t c) {
  lv_obj_t *l = lv_label_create(p);
  lv_label_set_text(l, t);
  lv_obj_set_style_text_font(l, f, 0);
  lv_obj_set_style_text_color(l, c, 0);
  lv_obj_set_pos(l, x, y);
  return l;
}

static lv_obj_t *chip(lv_obj_t *p, int x, int y, const char *t, lv_color_t c) {
  lv_obj_t *l = label(p, x, y, t, &pj_700_9, c);
  lv_obj_set_style_text_letter_space(l, 1, 0);
  return l;
}

static lv_obj_t *image(lv_obj_t *p, const lv_img_dsc_t *src, int x, int y) {
  lv_obj_t *im = lv_img_create(p);
  lv_img_set_src(im, src);
  lv_obj_set_pos(im, x, y);
  return im;
}

static void on_btn(lv_event_t *e) {
  if (act_cb) act_cb((ui_action_t)(intptr_t)lv_event_get_user_data(e));
}

static lv_obj_t *button(lv_obj_t *p, int x, int y, int w, int h, const char *t, ui_action_t a, int kind) {
  lv_obj_t *b = lv_btn_create(p);
  lv_obj_remove_style_all(b);
  lv_obj_add_style(b, kind == 1 ? &st_ghost : &st_btn, 0);
  if (kind == 2) lv_obj_add_style(b, &st_red, 0);
  lv_obj_set_style_transform_width(b, -2, LV_STATE_PRESSED);
  lv_obj_set_style_transform_height(b, -2, LV_STATE_PRESSED);
  lv_obj_set_pos(b, x, y);
  lv_obj_set_size(b, w, h);
  lv_obj_t *l = lv_label_create(b);
  lv_label_set_text(l, t);
  lv_obj_center(l);
  lv_obj_add_event_cb(b, on_btn, LV_EVENT_CLICKED, (void *)(intptr_t)a);
  return b;
}

static lv_obj_t *row(lv_obj_t *p, int x, int y, int w, const char *left, const char *right, lv_color_t rc, ui_action_t a) {
  lv_obj_t *r = lv_obj_create(p);
  lv_obj_remove_style_all(r);
  lv_obj_add_style(r, &st_row, 0);
  lv_obj_set_pos(r, x, y);
  lv_obj_set_size(r, w, 30);
  lv_obj_clear_flag(r, LV_OBJ_FLAG_SCROLLABLE);
  lv_obj_t *l = label(r, 10, 7, left, &pj_700_13, C_INK);
  (void)l;
  if (right) {
    lv_obj_t *rl = lv_label_create(r);
    lv_label_set_text(rl, right);
    lv_obj_set_style_text_font(rl, &pj_700_13, 0);
    lv_obj_set_style_text_color(rl, rc, 0);
    lv_obj_align(rl, LV_ALIGN_RIGHT_MID, -10, 0);
  }
  if ((int)a >= 0) {
    lv_obj_add_flag(r, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_add_event_cb(r, on_btn, LV_EVENT_CLICKED, (void *)(intptr_t)a);
  }
  return r;
}

static void topbar(lv_obj_t *p, const char *right1, lv_color_t c1, const char *right2) {
  lv_obj_t *b = label(p, 12, 7, "ARTA", &pj_800_16, C_INK);
  lv_obj_t *c = label(p, 0, 7, "-C", &pj_800_16, C_BLUE);
  lv_obj_align_to(c, b, LV_ALIGN_OUT_RIGHT_MID, 0, 0);
  if (right2) {
    lv_obj_t *r2 = lv_label_create(p);
    lv_label_set_text(r2, right2);
    lv_obj_set_style_text_font(r2, &pj_700_9, 0);
    lv_obj_set_style_text_color(r2, C_INK2, 0);
    lv_obj_align(r2, LV_ALIGN_TOP_RIGHT, -12, 11);
    if (right1) {
      lv_obj_t *r1 = lv_label_create(p);
      lv_label_set_text(r1, right1);
      lv_obj_set_style_text_font(r1, &pj_700_9, 0);
      lv_obj_set_style_text_color(r1, c1, 0);
      lv_obj_align_to(r1, r2, LV_ALIGN_OUT_LEFT_MID, -10, 0);
    }
  }
}

static lv_obj_t *ring(lv_obj_t *p, int x, int y, int d, int w, lv_color_t c, int val) {
  lv_obj_t *a = lv_arc_create(p);
  lv_obj_set_pos(a, x, y);
  lv_obj_set_size(a, d, d);
  lv_arc_set_rotation(a, 270);
  lv_arc_set_bg_angles(a, 0, 360);
  lv_arc_set_range(a, 0, 100);
  lv_arc_set_value(a, val);
  lv_obj_remove_style(a, NULL, LV_PART_KNOB);
  lv_obj_clear_flag(a, LV_OBJ_FLAG_CLICKABLE);
  lv_obj_set_style_arc_width(a, w, LV_PART_MAIN);
  lv_obj_set_style_arc_width(a, w, LV_PART_INDICATOR);
  lv_obj_set_style_arc_color(a, lv_color_white(), LV_PART_MAIN);
  lv_obj_set_style_arc_opa(a, LV_OPA_20, LV_PART_MAIN);
  lv_obj_set_style_arc_color(a, c, LV_PART_INDICATOR);
  lv_obj_set_style_arc_rounded(a, true, LV_PART_INDICATOR);
  return a;
}

// ------------------------------------------------------------------ layar
static void build_boot(lv_obj_t *s) {
  image(s, &pil_100, 110, 26);
  lv_obj_t *t = label(s, 0, 128, "ARTA-C", &pj_800_30, C_INK);
  lv_obj_align(t, LV_ALIGN_TOP_MID, 0, 128);
  lv_obj_t *sub = label(s, 0, 0, TX("Smart TB medication companion", "Pendamping minum obat TB"), &pj_600_11, C_INK2);
  lv_obj_align(sub, LV_ALIGN_TOP_MID, 0, 166);
  lv_obj_t *bar = lv_bar_create(s);
  lv_obj_set_pos(bar, 90, 194);
  lv_obj_set_size(bar, 140, 5);
  lv_bar_set_value(bar, 70, LV_ANIM_ON);
  lv_obj_set_style_bg_color(bar, lv_color_white(), LV_PART_MAIN);
  lv_obj_set_style_bg_opa(bar, LV_OPA_20, LV_PART_MAIN);
  lv_obj_set_style_bg_color(bar, C_BLUE, LV_PART_INDICATOR);
  lv_obj_t *c = label(s, 0, 0, TX("Connecting to ARTA-C cloud...", "Menghubungkan ke cloud ARTA-C..."), &pj_600_10, C_MUT);
  lv_obj_align(c, LV_ALIGN_TOP_MID, 0, 206);
}

static void build_home(lv_obj_t *s) {
  topbar(s, NULL, C_INK2, NULL);
  image(s, &termometer_14, 168, 9);
  l_temp = label(s, 184, 10, "", &pj_700_9, C_INK2);
  l_hum = label(s, 214, 10, "", &pj_700_9, C_INK2);
  image(s, &baterai_14, 240, 9);
  l_batt = label(s, 255, 10, "", &pj_700_9, C_INK2);
  l_clock = label(s, 282, 10, "", &pj_700_9, C_INK2);

  lv_obj_t *h = card(s, 10, 32, 170, 198, true);
  chip(h, 12, 10, TX("NEXT DOSE", "DOSIS BERIKUT"), C_BLUE);
  arc_next = ring(h, 14, 24, 142, 11, C_BLUE, 74);
  l_next = label(h, 0, 0, "", &pj_800_30, C_INK);
  lv_obj_align(l_next, LV_ALIGN_TOP_MID, 0, 74);
  l_minutes = label(h, 0, 0, "", &pj_600_10, C_INK2);
  lv_obj_align(l_minutes, LV_ALIGN_TOP_MID, 0, 108);
  image(h, &pil_58, 106, 116);
  l_caps = label(h, 12, 174, "", &pj_700_13, C_INK);

  lv_obj_t *c1 = card(s, 188, 32, 122, 62, false);
  chip(c1, 10, 7, TX("TREATMENT", "PENGOBATAN"), C_BLUE);
  l_day = label(c1, 10, 20, "", &pj_800_22, C_INK);
  l_dayof = label(c1, 10, 45, "", &pj_600_10, C_INK2);
  lv_obj_t *c2 = card(s, 188, 100, 122, 62, false);
  image(c2, &blister_58, 60, 8);
  chip(c2, 10, 7, "BLISTER", C_BLUE);
  l_left = label(c2, 10, 20, "", &pj_800_22, C_INK);
  label(c2, 10, 45, TX("left of 28", "sisa dari 28"), &pj_600_10, C_INK2);
  lv_obj_t *c3 = card(s, 188, 168, 122, 62, false);
  image(c3, &centang_44, 70, 9);
  chip(c3, 10, 7, TX("THIS WEEK", "MINGGU INI"), C_OK);
  l_week = label(c3, 10, 20, "", &pj_800_22, C_INK);
  label(c3, 10, 45, TX("doses taken", "dosis diminum"), &pj_600_10, C_INK2);
}

static void build_alarm(lv_obj_t *s) {
  topbar(s, TX("* alarm", "* alarm"), C_WARN, S.next_dose);
  image(s, &lonceng_100, 22, 44);
  char b[48];
  snprintf(b, sizeof b, TX("DAY %d - MORNING DOSE", "HARI %d - DOSIS PAGI"), S.day);
  chip(s, 140, 46, b, C_WARN);
  label(s, 140, 60, TX("Time for your\nmedicine", "Waktunya\nminum obat"), &pj_800_22, C_INK);
  snprintf(b, sizeof b, TX("%d caplets - take with water", "%d kaplet - minum dengan air"), S.caplets_per_dose);
  label(s, 140, 112, b, &pj_600_10, C_INK2);
  lv_obj_t *c = card(s, 140, 132, 170, 38, false);
  label(c, 12, 4, TX("Respond within", "Tanggapi dalam"), &pj_600_10, C_INK2);
  l_alarm_cd = label(c, 12, 17, "", &pj_700_13, C_INK);
  button(s, 12, 186, 200, 42, TX("I'm ready  >", "Saya siap  >"), UI_ACT_READY, 0);
  button(s, 220, 186, 88, 42, TX("Snooze 5'", "Tunda 5'"), UI_ACT_SNOOZE, 1);
}

static lv_point_t br[4][3] = {{{20, 14}, {20, 0}, {34, 0}}, {{116, 0}, {130, 0}, {130, 14}},
                              {{20, 100}, {20, 114}, {34, 114}}, {{116, 114}, {130, 114}, {130, 100}}};

static void build_face(lv_obj_t *s) {
  topbar(s, TX("Step 1 of 3", "Langkah 1/3"), C_INK2, TX("Face check", "Cek wajah"));
  lv_obj_t *v = card(s, 10, 32, 150, 198, true);
  lv_obj_set_style_bg_color(v, lv_color_hex(0x3B5C9E), 0);
  lv_obj_set_style_bg_grad_color(v, lv_color_hex(0x1B2F63), 0);
  lv_obj_t *head = lv_obj_create(v);
  lv_obj_remove_style_all(head);
  lv_obj_set_size(head, 60, 74);
  lv_obj_set_pos(head, 45, 49);
  lv_obj_set_style_radius(head, LV_RADIUS_CIRCLE, 0);
  lv_obj_set_style_bg_color(head, lv_color_hex(0x9DB5E6), 0);
  lv_obj_set_style_bg_opa(head, LV_OPA_50, 0);
  lv_obj_t *body = lv_obj_create(v);
  lv_obj_remove_style_all(body);
  lv_obj_set_size(body, 110, 80);
  lv_obj_set_pos(body, 20, 150);
  lv_obj_set_style_radius(body, 50, 0);
  lv_obj_set_style_bg_color(body, lv_color_hex(0x9DB5E6), 0);
  lv_obj_set_style_bg_opa(body, LV_OPA_40, 0);
  for (int i = 0; i < 4; i++) {
    lv_obj_t *ln = lv_line_create(v);
    lv_line_set_points(ln, br[i], 3);
    lv_obj_set_pos(ln, 0, 30);
    lv_obj_set_style_line_width(ln, 4, 0);
    lv_obj_set_style_line_color(ln, C_BLUE, 0);
    lv_obj_set_style_line_rounded(ln, true, 0);
  }
  lv_obj_t *scan = lv_obj_create(v);
  lv_obj_remove_style_all(scan);
  lv_obj_set_size(scan, 82, 2);
  lv_obj_set_pos(scan, 34, 96);
  lv_obj_set_style_bg_color(scan, C_OK, 0);
  lv_obj_set_style_bg_opa(scan, LV_OPA_COVER, 0);
  lv_anim_t a;                                  // garis pindai naik-turun
  lv_anim_init(&a);
  lv_anim_set_var(&a, scan);
  lv_anim_set_values(&a, 40, 140);
  lv_anim_set_time(&a, 1400);
  lv_anim_set_playback_time(&a, 1400);
  lv_anim_set_repeat_count(&a, LV_ANIM_REPEAT_INFINITE);
  lv_anim_set_exec_cb(&a, [](void *o, int32_t v) { lv_obj_set_y((lv_obj_t *)o, v); });
  lv_anim_start(&a);

  chip(s, 172, 44, "ESP32-CAM", C_BLUE);
  label(s, 172, 58, TX("Look at the\ncamera", "Lihat ke\nkamera"), &pj_800_16, C_INK);
  arc_face = ring(s, 172, 104, 64, 7, C_OK, 0);
  l_face = label(s, 0, 0, "", &pj_800_16, C_INK);
  lv_obj_align_to(l_face, arc_face, LV_ALIGN_CENTER, 0, 0);
  label(s, 244, 116, TX("Matching\nregistered\npatient...", "Mencocokkan\nwajah\npasien..."), &pj_600_10, C_INK2);
  label(s, 172, 182, TX("Photo kept only as proof\nof intake for your PMO.", "Foto hanya disimpan sebagai\nbukti minum untuk PMO."),
        &pj_600_10, C_MUT);
}

static void build_ppg(lv_obj_t *s) {
  topbar(s, TX("Step 2 of 3", "Langkah 2/3"), C_INK2, TX("* finger detected", "* jari terdeteksi"));
  lv_obj_t *h = card(s, 10, 32, 300, 96, true);
  image(h, &jantung_92, 4, 2);
  chip(h, 102, 9, TX("HEART RATE", "DETAK JANTUNG"), C_BLUE);
  l_hr = label(h, 102, 22, "", &pj_800_40, C_INK);
  label(h, 160, 40, "bpm", &pj_700_13, C_INK2);
  chart = lv_chart_create(h);
  lv_obj_set_pos(chart, 98, 62);
  lv_obj_set_size(chart, 194, 30);
  lv_chart_set_type(chart, LV_CHART_TYPE_LINE);
  lv_chart_set_point_count(chart, 64);
  lv_chart_set_range(chart, LV_CHART_AXIS_PRIMARY_Y, 0, 100);
  lv_chart_set_div_line_count(chart, 0, 0);
  lv_chart_set_update_mode(chart, LV_CHART_UPDATE_MODE_SHIFT);
  lv_obj_set_style_bg_opa(chart, LV_OPA_TRANSP, 0);
  lv_obj_set_style_border_width(chart, 0, 0);
  lv_obj_set_style_pad_all(chart, 0, 0);
  lv_obj_set_style_size(chart, 0, LV_PART_INDICATOR);
  lv_obj_set_style_line_width(chart, 2, LV_PART_ITEMS);
  ser = lv_chart_add_series(chart, C_BLUE, LV_CHART_AXIS_PRIMARY_Y);

  lv_obj_t *c1 = card(s, 10, 136, 96, 94, false);
  image(c1, &tetes_34, 58, 4);
  chip(c1, 10, 8, "SpO2", C_BLUE);
  l_spo2 = label(c1, 10, 26, "", &pj_800_30, C_INK);
  label(c1, 10, 64, TX("* normal", "* normal"), &pj_700_9, C_OK);
  lv_obj_t *c2 = card(s, 112, 136, 96, 94, false);
  chip(c2, 10, 8, TX("BLOOD PRESS.*", "TEKANAN DARAH*"), C_BLUE);
  l_bp = label(c2, 10, 28, "", &pj_800_22, C_INK);
  label(c2, 10, 62, TX("mmHg - estimate", "mmHg - estimasi"), &pj_600_10, C_INK2);
  lv_obj_t *c3 = card(s, 214, 136, 96, 94, false);
  chip(c3, 10, 8, TX("GLUCOSE*", "GULA DARAH*"), C_BLUE);
  l_glu = label(c3, 10, 28, "", &pj_800_22, C_INK);
  label(c3, 10, 62, TX("mg/dL - estimate", "mg/dL - estimasi"), &pj_600_10, C_INK2);
}

static void build_dispense(lv_obj_t *s) {
  topbar(s, TX("Step 3 of 3", "Langkah 3/3"), C_INK2, TX("Dispensing", "Mengeluarkan"));
  lv_obj_t *h = card(s, 10, 32, 132, 198, true);
  char b[40];
  snprintf(b, sizeof b, TX("BLISTER - ROW %d", "BLISTER - BARIS %d"), S.blister_row);
  chip(h, 12, 9, b, C_BLUE);
  for (int r = 0; r < 7; r++)
    for (int c = 0; c < 4; c++) {
      lv_obj_t *d = lv_obj_create(h);
      lv_obj_remove_style_all(d);
      lv_obj_set_size(d, 20, 12);
      lv_obj_set_pos(d, 16 + c * 28, 172 - r * 22);
      lv_obj_set_style_radius(d, 6, 0);
      lv_obj_set_style_bg_opa(d, LV_OPA_COVER, 0);
      cells[r * 4 + c] = d;
    }
  chip(s, 156, 44, TX("DISPENSING", "MENGELUARKAN"), C_BLUE);
  l_disp = label(s, 156, 58, "", &pj_800_40, C_INK);
  label(s, 156, 106, TX("Plunger pressing caplet...", "Pelatuk menekan kaplet..."), &pj_600_10, C_INK2);
  bar_disp = lv_bar_create(s);
  lv_obj_set_pos(bar_disp, 156, 126);
  lv_obj_set_size(bar_disp, 152, 8);
  lv_obj_set_style_bg_color(bar_disp, lv_color_white(), LV_PART_MAIN);
  lv_obj_set_style_bg_opa(bar_disp, LV_OPA_20, LV_PART_MAIN);
  lv_obj_set_style_bg_color(bar_disp, C_BLUE, LV_PART_INDICATOR);
  lv_obj_set_style_bg_grad_color(bar_disp, C_OK, LV_PART_INDICATOR);
  lv_obj_set_style_bg_grad_dir(bar_disp, LV_GRAD_DIR_HOR, LV_PART_INDICATOR);
  image(s, &pil_58, 246, 150);
  label(s, 156, 154, TX("Collect from\nthe tray below", "Ambil dari\nbaki di bawah"), &pj_600_10, C_INK2);
  label(s, 156, 208, TX("Please don't open the device.", "Jangan buka alat."), &pj_600_10, C_MUT);
}

static void build_done(lv_obj_t *s) {
  image(s, &centang_84, 118, 20);
  lv_obj_t *t = label(s, 0, 0, TX("Dose complete", "Dosis selesai"), &pj_800_22, C_INK);
  lv_obj_align(t, LV_ALIGN_TOP_MID, 0, 110);
  l_done1 = label(s, 0, 0, "", &pj_600_11, lv_color_hex(0xCFFBEA));
  lv_obj_align(l_done1, LV_ALIGN_TOP_MID, 0, 140);
  lv_obj_t *c = card(s, 40, 162, 240, 58, false);
  lv_obj_set_style_bg_color(c, lv_color_hex(0x2F9C7C), 0);
  lv_obj_set_style_bg_grad_color(c, lv_color_hex(0x0F4F45), 0);
  label(c, 14, 8, TX("Sent to your PMO", "Terkirim ke PMO"), &pj_600_10, lv_color_hex(0xCFFBEA));
  l_done2 = label(c, 14, 24, "", &pj_800_16, C_INK);
  lv_obj_t *bk = button(s, 250, 8, 60, 24, TX("Home", "Beranda"), UI_ACT_HOME, 1);
  lv_obj_set_style_text_font(bk, &pj_700_9, 0);
}

static void build_refill(lv_obj_t *s) {
  topbar(s, NULL, C_INK2, TX("* blister empty", "* blister habis"));
  image(s, &wadah_96, 16, 36);
  chip(s, 124, 44, TX("REFILL - FOR PMO", "ISI ULANG - UNTUK PMO"), C_BLUE);
  label(s, 124, 58, TX("Insert a new\nblister holder", "Masukkan wadah\nblister baru"), &pj_800_16, C_INK);
  row(s, 124, 104, 186, TX("1  Clip blister, domes front", "1  Jepit blister, kubah depan"), NULL, C_INK, (ui_action_t)-1);
  row(s, 124, 138, 186, TX("2  Slide into top slot", "2  Masukkan ke celah atas"), NULL, C_INK, (ui_action_t)-1);
  row(s, 124, 172, 186, TX("3  Confirm 28 caplets", "3  Konfirmasi 28 kaplet"), NULL, C_INK, (ui_action_t)-1);
  button(s, 16, 196, 96, 32, TX("Start  >", "Mulai  >"), UI_ACT_REFILL_START, 0);
}

static void build_missed(lv_obj_t *s) {
  topbar(s, NULL, C_INK2, S.clock);
  image(s, &lonceng_100, 18, 40);
  chip(s, 126, 46, TX("DOSE MISSED", "DOSIS TERLEWAT"), lv_color_hex(0xFFC2CC));
  label(s, 126, 60, TX("Your PMO has\nbeen notified", "PMO kamu sudah\ndiberi tahu"), &pj_800_16, C_INK);
  lv_obj_t *d = label(s, 126, 104, TX("Morning dose not taken within 60 min. You can still take it now.",
                                      "Dosis pagi belum diminum dalam 60 menit. Masih bisa diminum sekarang."),
                      &pj_600_10, lv_color_hex(0xFFD9DF));
  lv_obj_set_width(d, 184);
  lv_label_set_long_mode(d, LV_LABEL_LONG_WRAP);
  button(s, 126, 150, 184, 38, TX("Take it now  >", "Minum sekarang  >"), UI_ACT_TAKE_NOW, 2);
  button(s, 126, 196, 184, 30, TX("Call PMO", "Hubungi PMO"), UI_ACT_CALL_PMO, 1);
}

static void build_settings(lv_obj_t *s) {
  label(s, 12, 7, TX("Settings", "Pengaturan"), &pj_800_16, C_INK);
  lv_obj_t *v = lv_label_create(s);
  lv_label_set_text(v, "v1.0");
  lv_obj_set_style_text_font(v, &pj_700_9, 0);
  lv_obj_set_style_text_color(v, C_INK2, 0);
  lv_obj_align(v, LV_ALIGN_TOP_RIGHT, -12, 11);
  row(s, 12, 32, 296, TX("Language", "Bahasa"), S.lang_id ? "Bahasa" : "English", C_BLUE, UI_ACT_LANGUAGE);
  row(s, 12, 66, 296, "Wi-Fi", S.wifi, C_OK, (ui_action_t)-1);
  lv_obj_t *r = row(s, 12, 100, 296, TX("Alarm volume", "Volume alarm"), NULL, C_INK, (ui_action_t)-1);
  lv_obj_t *sw = lv_switch_create(r);
  lv_obj_set_size(sw, 34, 18);
  lv_obj_align(sw, LV_ALIGN_RIGHT_MID, -8, 0);
  lv_obj_add_state(sw, LV_STATE_CHECKED);
  lv_obj_set_style_bg_color(sw, C_DEEP, LV_PART_INDICATOR | LV_STATE_CHECKED);
  row(s, 12, 134, 296, TX("Calibrate plunger & holder", "Kalibrasi pelatuk & wadah"), ">", C_BLUE, UI_ACT_CALIBRATE);
  row(s, 12, 168, 296, TX("Re-enroll face", "Daftar ulang wajah"), ">", C_BLUE, UI_ACT_ENROLL_FACE);
  row(s, 12, 202, 296, TX("Device ID", "ID alat"), S.device_id, C_MUT, (ui_action_t)-1);
}

// ------------------------------------------------------------------ API
static void clear_refs(void) {
  l_clock = l_temp = l_hum = l_batt = l_next = l_minutes = l_caps = l_day = l_dayof = l_left = l_week = NULL;
  arc_next = l_alarm_cd = arc_face = l_face = l_hr = l_spo2 = l_bp = l_glu = chart = NULL;
  ser = NULL;
  l_disp = bar_disp = l_done1 = l_done2 = NULL;
  memset(cells, 0, sizeof cells);
}

void ui_show(ui_screen_t s) {
  styles();
  clear_refs();
  const lv_img_dsc_t *bg = s == UI_MISSED ? &bg_red : (s == UI_DONE ? &bg_green : &bg_blue);
  lv_obj_t *n = base(bg);
  switch (s) {
    case UI_BOOT: build_boot(n); break;
    case UI_HOME: build_home(n); break;
    case UI_ALARM: build_alarm(n); break;
    case UI_FACE: build_face(n); break;
    case UI_PPG: build_ppg(n); break;
    case UI_DISPENSE: build_dispense(n); break;
    case UI_DONE: build_done(n); break;
    case UI_REFILL: build_refill(n); break;
    case UI_MISSED: build_missed(n); break;
    default: build_settings(n); break;
  }
  cur = s;
  lv_scr_load_anim(n, LV_SCR_LOAD_ANIM_FADE_ON, 250, 0, true);   // hapus layar lama
  scr = n;
  ui_refresh();
}

ui_screen_t ui_current(void) { return cur; }
ui_state_t *ui_state(void) { return &S; }
void ui_set_action_cb(void (*cb)(ui_action_t)) { act_cb = cb; }

static void set(lv_obj_t *l, const char *fmt, ...) {
  if (!l) return;
  char b[64];
  va_list ap;
  va_start(ap, fmt);
  vsnprintf(b, sizeof b, fmt, ap);
  va_end(ap);
  lv_label_set_text(l, b);
}

void ui_refresh(void) {
  set(l_clock, "%s", S.clock);
  set(l_temp, "%dC", S.temp_c);
  set(l_hum, "%d%%", S.humidity);
  set(l_batt, "%d%%", S.battery);
  set(l_next, "%s", S.next_dose);
  set(l_minutes, TX("in %d minutes", "%d menit lagi"), S.minutes_to_dose);
  set(l_caps, TX("%d caplets - 4FDC", "%d kaplet - KDT"), S.caplets_per_dose);
  set(l_day, TX("Day %d", "Hari %d"), S.day);
  set(l_dayof, TX("of %d - %d%% done", "dari %d - %d%% selesai"), S.total_days, S.day * 100 / (S.total_days ? S.total_days : 1));
  set(l_left, "%d", S.blister_left);
  set(l_week, "%d/7", S.week_taken);
  if (arc_next) lv_arc_set_value(arc_next, 100 - (S.minutes_to_dose > 30 ? 30 : S.minutes_to_dose) * 100 / 30 / 4 * 3);
  set(l_alarm_cd, TX("%02d:%02d min - PMO notified after", "%02d:%02d mnt - lalu PMO diberi tahu"), S.alarm_left_s / 60,
      S.alarm_left_s % 60);
  if (arc_face) lv_arc_set_value(arc_face, S.face_progress);
  set(l_face, "%d%%", S.face_progress);
  if (l_face && arc_face) lv_obj_align_to(l_face, arc_face, LV_ALIGN_CENTER, 0, 0);
  set(l_hr, "%d", S.hr);
  set(l_spo2, "%d%%", S.spo2);
  set(l_bp, "%d/%d", S.bp_sys, S.bp_dia);
  set(l_glu, "%d", S.glucose);
  set(l_disp, TX("%d of %d", "%d dari %d"), S.disp_i, S.disp_n);
  if (bar_disp) lv_bar_set_value(bar_disp, S.disp_n ? S.disp_i * 100 / S.disp_n : 0, LV_ANIM_ON);
  for (int i = 0; i < 28; i++) {
    if (!cells[i]) continue;
    bool empty = S.taken_mask & (1UL << i);
    bool now = (i / 4 + 1 == S.blister_row) && !empty && ((i % 4) == ((S.disp_i - 1) % 4));
    lv_obj_set_style_bg_color(cells[i], empty ? lv_color_hex(0x30487E) : (now ? C_OK : C_RED), 0);
    lv_obj_set_style_shadow_width(cells[i], now ? 10 : 0, 0);
    lv_obj_set_style_shadow_color(cells[i], C_OK, 0);
  }
  set(l_done1, TX("%d caplets taken - %s - face verified", "%d kaplet diminum - %s - wajah cocok"), S.disp_n, S.done_time);
  set(l_done2, TX("Streak %d days - %d to go", "Beruntun %d hari - %d lagi"), S.streak, S.total_days - S.day);
}

void ui_ppg_push(int16_t v) {
  if (chart && ser) lv_chart_set_next_value(chart, ser, v);
}

void ui_init(void) {
  memset(&S, 0, sizeof S);
  strcpy(S.clock, "06:52");
  strcpy(S.next_dose, "07:00");
  strcpy(S.done_time, "07:04");
  strcpy(S.wifi, "* ARTA-Home");
  strcpy(S.device_id, "dev-ARTAC-0071");
  S.temp_c = 27; S.humidity = 58; S.battery = 86;
  S.minutes_to_dose = 8; S.caplets_per_dose = 3;
  S.day = 47; S.total_days = 180; S.blister_left = 19; S.week_taken = 7;
  S.alarm_left_s = 3552; S.face_progress = 75;
  S.hr = 78; S.spo2 = 98; S.bp_sys = 118; S.bp_dia = 76; S.glucose = 105; S.finger = true;
  S.disp_i = 2; S.disp_n = 3; S.blister_row = 2; S.taken_mask = 0x1F;   // baris 1 + kolom 1 baris 2 sudah kosong
  S.streak = 12;
  ui_show(UI_BOOT);
}
