/*
 * ============================================
 *  ESP32 OLED Player — پخش انیمیشن روی SSD1306
 *  خروجیِ ابزار «OLED Video Converter»
 * ============================================
 *
 *  1) فایل خروجی ابزار را با نام oled_frames.h کنار همین فایل کپی کنید.
 *  2) کتابخانه‌های Adafruit SSD1306 و Adafruit GFX را نصب کنید.
 *  3) برد ESP32 را انتخاب و آپلود کنید. تمام!
 *
 *  سیم‌کشی (I2C):
 *    OLED VCC -> 3V3      OLED GND -> GND
 *    OLED SDA -> GPIO21   OLED SCL -> GPIO22
 */

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "oled_frames.h"   // ← فایل تولیدشده توسط ابزار

#define SCREEN_WIDTH    128
#define SCREEN_HEIGHT   64
#define OLED_RESET      -1    // ریست مشترک با برد
#define SCREEN_ADDRESS  0x3C  // آدرس I2C ماژول (بعضی ماژول‌ها 0x3D)

#define FRAME_DELAY_MS  100   // 100ms ≈ 10 FPS — برای کندترشدن، عدد را زیاد کنید

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

void setup() {
  Serial.begin(115200);

  Wire.begin(21, 22);  // SDA, SCL — پیش‌فرض ESP32

  if (!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println(F("SSD1306 not found!"));
    for (;;);  // توقف
  }

  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(20, 28);
  display.print(F("Loading..."));
  display.display();
  delay(500);
}

void loop() {
  // پخش بی‌نهایت همه‌ی فریم‌ها
  for (int i = 0; i < TOTAL_FRAMES; i++) {
    display.drawBitmap(0, 0, frames[i], SCREEN_WIDTH, SCREEN_HEIGHT, SSD1306_WHITE);
    display.display();
    delay(FRAME_DELAY_MS);
  }
}
