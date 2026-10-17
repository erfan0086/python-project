<div align="center">

# 🎬 OLED Video Converter

**Turn any video into a 128×64 monochrome animation for SSD1306 OLED displays.**

Upload a video in your browser, tweak a few settings, and download a ready-to-compile
`.h` header for your ESP32 or Arduino project — no coding required.

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![Gradio](https://img.shields.io/badge/UI-Gradio-FF4E75?logo=gradio&logoColor=white)
![OpenCV](https://img.shields.io/badge/Video-OpenCV-5C3EE8?logo=opencv&logoColor=white)
![Display](https://img.shields.io/badge/OLED-128x64-2DD2B3)

</div>

---

## How it works

```
🎬 your video  ──▶  🖥️ web app  ──▶  📄 oled_frames.h  ──▶  📺 ESP32 + SSD1306
```

1. Each frame is resized to **128×64** and converted to black & white with a threshold you control.
2. Every frame is packed into **1024 bytes** (8 pixels per byte, MSB first) — the exact format
   [`Adafruit_GFX::drawBitmap()`](https://learn.adafruit.com/monochrome-oled-breakouts) expects.
3. All frames are written into a single PROGMEM-ready header file with a pointer array.

## Quick start

```bash
git clone https://github.com/erfan0086/python-project.git
cd python-project
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:7860**, drop in a video, hit **Convert** and download the `.h` file. 🎉

## Settings

| Setting | What it does | Tip |
|---|---|---|
| **Max frames** | How many frames to extract | 20–60 is plenty for PROGMEM |
| **Frame skip** | Keep 1 frame out of every N | `2` ≈ half the frames |
| **B/W threshold** | Cutoff between black and white | Raise it if the video looks all white |
| **Invert** | Swap black ↔ white | Useful for dark scenes |

## Play it on an ESP32

Copy the downloaded file to your sketch folder as `oled_frames.h`, install the
**Adafruit SSD1306** and **Adafruit GFX** libraries, then:

```cpp
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "oled_frames.h"

Adafruit_SSD1306 display(128, 64, &Wire, -1);

void setup() {
  Wire.begin(21, 22);                      // SDA, SCL
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
}

void loop() {
  for (int i = 0; i < TOTAL_FRAMES; i++) {
    display.drawBitmap(0, 0, frames[i], 128, 64, SSD1306_WHITE);
    display.display();
    delay(100);                            // ~10 FPS
  }
}
```

**Wiring:** `VCC → 3V3` · `GND → GND` · `SDA → GPIO21` · `SCL → GPIO22`

---

<div align="center">

Made with ❤️ and a tiny 128×64 OLED · If you find this useful, give it a ⭐

</div>
