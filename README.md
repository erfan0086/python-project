<div align="center">

# 🎬 OLED Video Converter

**Turn any video into a 128×64 monochrome OLED animation for ESP32 & Arduino.**

Upload a video → tweak the settings → download a ready-to-compile `.h` file. No coding required.

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![Gradio](https://img.shields.io/badge/Gradio-Web%20UI-FF4E75?logo=gradio&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-Video%20Processing-5C3EE8?logo=opencv&logoColor=white)

</div>

---

## ✨ Features

- 🎥 **Any video format** — MP4, AVI, MOV... anything OpenCV can read
- ⚙️ **Full control** — frame count, frame skip, B/W threshold, color inversion
- 📦 **Single header output** — all frames packed into one PROGMEM-ready `.h` file
- 🔌 **Plug & play** — works directly with `Adafruit_GFX::drawBitmap()` and U8g2
- 🌐 **Simple web UI** — powered by Gradio, runs in your browser

## 🚀 Getting Started

```bash
git clone https://github.com/erfan0086/python-project.git
cd python-project
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:7860** in your browser. That's it! 🎉

## ⚙️ Settings

| Option | Description | Tip |
|---|---|---|
| **Max frames** | Number of frames to extract | 20–60 works well |
| **Frame skip** | Keep 1 out of every N frames | `2` for normal videos |
| **B/W threshold** | Cutoff between black & white pixels | Raise it for bright scenes |
| **Invert** | Swap black ↔ white | Great for dark backgrounds |

## 🔌 Using the Output on ESP32

1. Save the downloaded file as `oled_frames.h` next to your Arduino sketch.
2. Install the **Adafruit SSD1306** and **Adafruit GFX** libraries.
3. Play the animation:

```cpp
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "oled_frames.h"

Adafruit_SSD1306 display(128, 64, &Wire, -1);

void setup() {
  Wire.begin(21, 22);  // SDA, SCL
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
}

void loop() {
  for (int i = 0; i < TOTAL_FRAMES; i++) {
    display.drawBitmap(0, 0, frames[i], 128, 64, SSD1306_WHITE);
    display.display();
    delay(100);  // ~10 FPS
  }
}
```

**Wiring:** `VCC → 3V3` · `GND → GND` · `SDA → GPIO21` · `SCL → GPIO22`

## 📦 Output Format

Each 128×64 frame is packed into **1024 bytes** (row-major, 8 pixels per byte, MSB first) — exactly what `drawBitmap()` expects:

```cpp
static const unsigned char PROGMEM frame_0[] = {
  0xFF, 0x81, 0xA5, 0x81, ...
};

const unsigned char* const frames[] PROGMEM = { frame_0, frame_1, /* ... */ };
```

## 📁 Project Structure

```
python-project/
├── app.py              # Gradio web app
├── requirements.txt    # Dependencies
└── README.md
```

---

<div align="center">

Made with ❤️ and a tiny 128×64 OLED — if you like it, give it a ⭐!

</div>
