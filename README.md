# Video to OLED Bitmap Converter

Convert any video into a ready-to-compile C header (`.h`) full of 128×64 monochrome frames for SSD1306 OLED displays.

This project extracts frames from a video, converts each one into compact bitmap data (8 pixels per byte, MSB first), and packs everything into a single `PROGMEM`-friendly header file that you can drop straight into an ESP32 / Arduino sketch. A simple Gradio web UI handles the whole process in your browser.

> Perfect for playing video clips on a 0.96" SSD1306 OLED with an ESP32 — no coding required.

* * *

## ✨ Features

- Convert any video format that OpenCV supports (MP4, AVI, MOV, ...)
- Simple web UI powered by Gradio — runs in your browser
- Adjustable max frames, frame skip, B/W threshold and color inversion
- Single `PROGMEM`-ready `.h` file with all frames + pointer array
- Compatible with `Adafruit_GFX::drawBitmap()` and U8g2
- Live progress bar during conversion

* * *

## 📁 Project Structure

```
python-project/
├── converter.py     # Main converter app (Gradio)
├── requirements.txt # Python dependencies
├── .gitignore
└── README.md
```

* * *

## ⚙️ Prerequisites

- Python 3.8+
- pip

* * *

## 🚀 Install

```
git clone https://github.com/erfan0086/python-project.git
cd python-project

pip install -r requirements.txt
```

* * *

## ▶️ Run

```
python converter.py
```

Then open **http://127.0.0.1:7860** in your browser:

1. Upload a video
2. Set the options
3. Hit **Convert** and download the generated `.h` file

* * *

## 🔧 Settings

Available in the web UI:

| Parameter | Description |
| --- | --- |
| `Max frames` | Maximum number of frames to extract (20–60 fits well in flash) |
| `Frame skip` | Keep 1 frame out of every N (`2` = half the frames) |
| `B/W threshold` | Cutoff value between black and white pixels (50–200) |
| `Invert colors` | Swap black ↔ white, useful for dark scenes |

* * *

## 📦 Output Format

Each 128×64 frame is packed into 1024 bytes (8 pixels per byte, row-major, MSB first) — exactly the layout `Adafruit_GFX::drawBitmap()` expects:

```
static const unsigned char PROGMEM frame_0[] = {
  0xFF, 0x81, 0xA5, 0x81, ...
};

const unsigned char* const frames[] PROGMEM = {
  frame_0,
  frame_1,
  ...
};
```

* * *

## 📺 Play It on an ESP32

Copy the downloaded file to your sketch folder as `oled_frames.h`, install the **Adafruit SSD1306** and **Adafruit GFX** libraries, then:

```
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

Wiring: `VCC → 3V3` · `GND → GND` · `SDA → GPIO21` · `SCL → GPIO22`

* * *

## 📊 Status Output

After conversion the app prints a summary:

```
✅ Done!

• Total frames: 40
• Resolution: 128×64
• Source FPS: 30.0
• Your .h file is ready to download
```
