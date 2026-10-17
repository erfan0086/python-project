import gradio as gr
import cv2
import numpy as np
import tempfile
import os

def frame_to_oled_bitmap(frame, width=128, height=64, threshold=128, invert=False):
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
                    byte |= (1 << (7 - bit))
            bitmap.append(byte)
    return bitmap


def process_video(video_path, max_frames, frame_skip, threshold, invert, progress=gr.Progress()):
    if video_path is None:
        return None, "Please upload a video first."

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None, "Error: could not open video!"

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    frames_data = []
    frame_count = 0
    saved_count = 0

    progress(0, desc="Processing frames...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % int(frame_skip) != 0:
            frame_count += 1
            continue

        bitmap = frame_to_oled_bitmap(frame, threshold=int(threshold), invert=invert)
        frames_data.append(bitmap)
        saved_count += 1
        frame_count += 1

        if total_frames > 0:
            progress(min(saved_count / max(1, int(max_frames) if max_frames else total_frames), 0.99))

        if max_frames and saved_count >= int(max_frames):
            break

    cap.release()

    if saved_count == 0:
        return None, "No frames extracted!"

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".h", mode="w", encoding="utf-8")

    temp_file.write("// ============================================\n")
    temp_file.write("// Auto-generated OLED Animation Frames\n")
    temp_file.write("// Resolution : 128 x 64\n")
    temp_file.write(f"// Total Frames: {saved_count}\n")
    temp_file.write("// Compatible with Adafruit_SSD1306 / U8g2\n")
    temp_file.write("// ============================================\n\n")

    temp_file.write("#pragma once\n\n")
    temp_file.write("#define OLED_WIDTH      128\n")
    temp_file.write("#define OLED_HEIGHT     64\n")
    temp_file.write(f"#define TOTAL_FRAMES   {saved_count}\n\n")

    for i, bitmap in enumerate(frames_data):
        temp_file.write(f"static const unsigned char PROGMEM frame_{i}[] = {{\n")

        for j in range(0, len(bitmap), 16):
            line = bitmap[j:j+16]
            hex_values = ", ".join(f"0x{b:02X}" for b in line)
            temp_file.write(f"  {hex_values},\n")

        temp_file.write("};\n\n")

    temp_file.write("// Pointer array to all frames\n")
    temp_file.write("const unsigned char* const frames[] PROGMEM = {\n")
    for i in range(saved_count):
        temp_file.write(f"  frame_{i},\n")
    temp_file.write("};\n")

    temp_file.close()

    info = (
        "✅ Done!\n\n"
        f"• Total frames: {saved_count}\n"
        f"• Resolution: 128×64\n"
        f"• Source FPS: {fps:.1f}\n"
        "• Your .h file is ready to download"
    )
    return temp_file.name, info


with gr.Blocks(title="OLED Video to Bitmap Converter") as demo:
    gr.Markdown("# 🎬 Video → OLED Bitmap Converter\nUpload a video → tweak the settings → download a ready-to-use `.h` file for your ESP32")

    with gr.Row():
        with gr.Column():
            video_input = gr.Video(label="Upload video")

            max_frames = gr.Number(label="Max frames", value=40, precision=0)
            frame_skip = gr.Slider(label="Frame skip", minimum=1, maximum=10, step=1, value=2)
            threshold = gr.Slider(label="B/W threshold", minimum=50, maximum=200, step=1, value=128)
            invert = gr.Checkbox(label="Invert colors", value=False)

            process_btn = gr.Button("🚀 Convert", variant="primary")

        with gr.Column():
            status = gr.Textbox(label="Status", lines=6)
            download_file = gr.File(label="Download .h file")

    process_btn.click(
        fn=process_video,
        inputs=[video_input, max_frames, frame_skip, threshold, invert],
        outputs=[download_file, status]
    )

if __name__ == "__main__":
    demo.launch()
