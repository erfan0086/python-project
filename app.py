# -*- coding: utf-8 -*-
"""
🎬 OLED Video Converter — تبدیل ویدیو به انیمیشن نمایشگر OLED ۱۲۸×۶۴

این ابزار ویدیوی ورودی را به فریم‌های بیت‌مپ تک‌رنگ (Monochrome) با فرمت
سازگار با کتابخانه‌های Adafruit_SSD1306 و U8g2 تبدیل می‌کند و یک فایل
هدر C/C++ (‏.h) آماده‌ی استفاده روی ESP32 / Arduino تحویل می‌دهد.

اجرا:
    pip install -r requirements.txt
    python app.py
"""

import os
import tempfile
from typing import List, Tuple

import cv2
import gradio as gr
import numpy as np

# ─────────────────────────────── تنظیمات ثابت ───────────────────────────────

OLED_WIDTH = 128
OLED_HEIGHT = 64
BYTES_PER_FRAME = OLED_WIDTH * OLED_HEIGHT // 8   # 1024 بایت برای هر فریم
PREVIEW_FRAMES = 12                               # تعداد فریم‌های پیش‌نمایش در UI


# ───────────────────────────── تبدیل تصویر ─────────────────────────────

def frame_to_oled_bitmap(
    frame: np.ndarray,
    width: int = OLED_WIDTH,
    height: int = OLED_HEIGHT,
    threshold: int = 128,
    invert: bool = False,
) -> Tuple[List[int], np.ndarray]:
    """یک فریم BGR را به بایت‌های بیت‌مپ OLED تبدیل می‌کند.

    فرمت خروجی: ردیفی (Horizontal)، ۸ پیکسل در هر بایت، MSB اول —
    دقیقاً همان فرمتی که ``Adafruit_GFX::drawBitmap`` انتظار دارد.

    Args:
        frame:     فریم ورودی به‌صورت آرایه‌ی NumPy در قالب BGR.
        width:     عرض هدف (پیش‌فرض ۱۲۸).
        height:    ارتفاع هدف (پیش‌فرض ۶۴).
        threshold: آستانه‌ی سیاه‌وسفیدکردن (۰ تا ۲۵۵).
        invert:    در صورت ``True`` رنگ‌ها معکوس می‌شوند.

    Returns:
        تاپل ``(bitmap_bytes, binary_image)``؛ بایت‌ها برای فایل هدر و
        تصویر دودویی برای پیش‌نمایش.
    """
    resized = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)

    if invert:
        binary = cv2.bitwise_not(binary)

    bitmap = []
    for y in range(height):
        for x in range(0, width, 8):
            byte = 0
            for bit in range(8):
                if x + bit < width and binary[y, x + bit] > 0:
                    byte |= 1 << (7 - bit)
            bitmap.append(byte)

    return bitmap, binary


def build_header(frames_data: List[List[int]]) -> str:
    """متن کامل فایل هدر C (‏.h) شامل همه‌ی فریم‌ها و آرایه‌ی اشاره‌گرها را می‌سازد."""
    saved_count = len(frames_data)

    lines = [
        "// ============================================",
        "// Auto-generated OLED Animation Frames",
        "// Tool       : OLED Video Converter",
        f"// Resolution : {OLED_WIDTH} x {OLED_HEIGHT}",
        f"// Total Frames: {saved_count}",
        f"// Bytes/Frame: {BYTES_PER_FRAME}",
        "// Compatible : Adafruit_SSD1306 / U8g2",
        "// ============================================",
        "",
        "#pragma once",
        "",
        "#include <Arduino.h>",
        "",
        f"#define OLED_WIDTH   {OLED_WIDTH}",
        f"#define OLED_HEIGHT  {OLED_HEIGHT}",
        f"#define TOTAL_FRAMES {saved_count}",
        f"#define FRAME_BYTES  {BYTES_PER_FRAME}",
        "",
    ]

    for i, bitmap in enumerate(frames_data):
        lines.append(f"static const unsigned char PROGMEM frame_{i}[] = {{")
        for j in range(0, len(bitmap), 16):
            row = bitmap[j: j + 16]
            lines.append("  " + ", ".join(f"0x{b:02X}" for b in row) + ",")
        lines.append("};")
        lines.append("")

    lines.append("// Pointer array to all frames")
    lines.append("const unsigned char* const frames[] PROGMEM = {")
    for i in range(saved_count):
        lines.append(f"  frame_{i},")
    lines.append("};")
    lines.append("")

    return "\n".join(lines)


# ───────────────────────────── پردازش اصلی ─────────────────────────────

def process_video(
    video_path,
    max_frames,
    frame_skip,
    threshold,
    invert,
    progress=gr.Progress(),
):
    """پردازش کامل ویدیو: خواندن فریم‌ها، تبدیل، ساخت فایل .h و پیش‌نمایش."""
    if video_path is None:
        return None, None, "⚠️ لطفاً ابتدا یک ویدیو آپلود کنید."

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None, None, "❌ خطا در باز کردن ویدیو! فرمت فایل را بررسی کنید."

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 0.0

    max_frames = max(1, int(max_frames or 0))
    frame_skip = max(1, int(frame_skip or 1))

    if total_frames > 0:
        expected = min(max_frames, (total_frames + frame_skip - 1) // frame_skip)
    else:
        expected = max_frames
    expected = max(1, expected)

    progress(0, desc="در حال پردازش فریم‌ها...")

    frames_data: List[List[int]] = []
    previews: List[np.ndarray] = []
    frame_index = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_index % frame_skip != 0:
            frame_index += 1
            continue
        frame_index += 1

        bitmap, binary = frame_to_oled_bitmap(
            frame, threshold=int(threshold), invert=bool(invert)
        )
        frames_data.append(bitmap)
        previews.append(binary)

        progress(
            min(0.99, len(frames_data) / expected),
            desc=f"فریم {len(frames_data)} از {expected}",
        )

        if len(frames_data) >= max_frames:
            break

    cap.release()

    if not frames_data:
        return None, None, "❌ هیچ فریمی استخراج نشد! ویدیوی دیگری امتحان کنید."

    # ── ساخت و ذخیره‌ی فایل هدر ──
    header_content = build_header(frames_data)
    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".h",
        mode="w",
        encoding="utf-8",
        prefix="oled_frames_",
    )
    temp_file.write(header_content)
    temp_file.close()

    # ── پیش‌نمایش گرافیکی (انتخاب یکنواخت بین همه‌ی فریم‌ها) ──
    count = len(previews)
    pick = sorted(set(np.linspace(0, count - 1, min(PREVIEW_FRAMES, count)).astype(int)))
    gallery = [
        cv2.resize(
            previews[i],
            (OLED_WIDTH * 3, OLED_HEIGHT * 3),
            interpolation=cv2.INTER_NEAREST,
        )
        for i in pick
    ]

    size_kb = count * BYTES_PER_FRAME / 1024
    info = (
        "✅ پردازش با موفقیت انجام شد!\n\n"
        f"• 🎞️ تعداد فریم نهایی: {count}\n"
        f"• 📐 رزولوشن: {OLED_WIDTH}×{OLED_HEIGHT} — {BYTES_PER_FRAME} بایت در هر فریم\n"
        f"• ⏱️ FPS ویدیوی اصلی: {fps:.1f}\n"
        f"• 💾 حجم تخمینی فایل: ~{size_kb:.0f} KB\n"
        f"• 📄 فایل .h آماده است؛ آن را با نام oled_frames.h کنار اسکچ ESP32 کپی کنید."
    )
    return temp_file.name, gallery, info


# ───────────────────────────── رابط کاربری ─────────────────────────────

CUSTOM_CSS = """
.hero { text-align: center; }
.gradio-container { max-width: 1080px !important; margin: 0 auto !important; }
footer { visibility: hidden; }
"""

with gr.Blocks(title="OLED Video to Bitmap Converter") as demo:

    gr.HTML(
        """
        <div dir="rtl" class="hero">
            <h1>🎬 تبدیل ویدیو به بیت‌مپ OLED</h1>
            <p style="font-size: 1.1rem; opacity: .85;">
                ویدیو رو آپلود کن → تنظیمات رو بذار → فایل <code>.h</code> رو بگیر و روی
                <b>ESP32 + SSD1306</b> پخش کن ✨
            </p>
        </div>
        """
    )

    with gr.Row():
        with gr.Column(scale=1):
            video_input = gr.Video(label="🎥 آپلود ویدیو")

            gr.Markdown("### ⚙️ تنظیمات")
            max_frames = gr.Number(
                label="حداکثر تعداد فریم", value=40, precision=0, minimum=1
            )
            frame_skip = gr.Slider(
                label="رد کردن فریم (Frame Skip)",
                minimum=1, maximum=10, step=1, value=2,
                info="مثلاً ۲ یعنی هر از هر ۲ فریم، ۱ فریم برمی‌دارد",
            )
            threshold = gr.Slider(
                label="آستانه‌ی سیاه‌وسفید (Threshold)",
                minimum=50, maximum=200, step=1, value=128,
            )
            invert = gr.Checkbox(label="معکوس کردن رنگ (Invert)", value=False)

            process_btn = gr.Button("🚀 شروع تبدیل", variant="primary", size="lg")

        with gr.Column(scale=1):
            status = gr.Textbox(label="📋 وضعیت", lines=7)
            preview = gr.Gallery(
                label="🖼️ پیش‌نمایش فریم‌ها روی OLED",
                columns=3,
                height=290,
                object_fit="contain",
            )
            download_file = gr.File(label="📥 دانلود فایل .h")

    gr.Markdown(
        """
---
### 🔌 نحوه‌ی استفاده روی ESP32
۱. فایل دانلودشده را با نام `oled_frames.h` کنار اسکچ Arduino کپی کنید.
۲. نمونه‌کد پخش را از پوشه‌ی [`examples/ESP32_OLED_Player.ino`](examples/ESP32_OLED_Player.ino) بردارید.
۳. آپلود کنید و لذت ببرید! 🎉
        """
    )

    process_btn.click(
        fn=process_video,
        inputs=[video_input, max_frames, frame_skip, threshold, invert],
        outputs=[download_file, preview, status],
    )


if __name__ == "__main__":
    demo.queue().launch(
        server_name=os.getenv("GRADIO_SERVER_NAME", "0.0.0.0"),
        server_port=int(os.getenv("GRADIO_SERVER_PORT", "7860")),
        share=os.getenv("GRADIO_SHARE", "0") == "1",  # لینک عمومی: GRADIO_SHARE=1
        theme=gr.themes.Soft(primary_hue="emerald", neutral_hue="slate"),
        css=CUSTOM_CSS,
    )
