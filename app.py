import streamlit as st
from gtts import gTTS
import requests
import os
import tempfile
import subprocess
from PIL import Image
import imageio_ffmpeg as ffmpeg

st.set_page_config(page_title="Auto Video Generator", layout="centered")

st.title("🎬 Auto Video Generator (Stable Version)")
st.write("Paste text → auto voice + image → MP4 video")

# ----------------------------
# Input
# ----------------------------
text = st.text_area("✍️ Enter your content", height=200)

# ----------------------------
# Helpers
# ----------------------------
def generate_image(prompt, path):
    try:
        url = "https://image.pollinations.ai/prompt/" + prompt
        img = requests.get(url, timeout=20).content
        with open(path, "wb") as f:
            f.write(img)
    except:
        Image.new("RGB", (1280, 720), color=(0, 0, 0)).save(path)

def text_to_audio(text, path):
    tts = gTTS(text=text, lang="en")
    tts.save(path)

def split_scenes(text):
    sentences = text.split(".")
    return [s.strip() for s in sentences if len(s.strip()) > 5]

# ----------------------------
# Core: FFmpeg video creation
# ----------------------------
def create_video(text):
    scenes = split_scenes(text)
    temp_dir = tempfile.mkdtemp()
    video_list_file = os.path.join(temp_dir, "list.txt")
    ffmpeg_path = ffmpeg.get_ffmpeg_exe()

    segment_paths = []

    for i, scene in enumerate(scenes):
        audio_path = os.path.join(temp_dir, f"audio_{i}.mp3")
        image_path = os.path.join(temp_dir, f"img_{i}.jpg")
        segment_path = os.path.join(temp_dir, f"seg_{i}.mp4")

        # Generate assets
        text_to_audio(scene, audio_path)
        generate_image(scene[:60], image_path)

        # Create video segment from image + audio
        cmd = [
            ffmpeg_path,
            "-y",
            "-loop", "1",
            "-i", image_path,
            "-i", audio_path,
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            segment_path
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        segment_paths.append(segment_path)

    # Create concat list
    with open(video_list_file, "w") as f:
        for p in segment_paths:
            f.write(f"file '{p}'\n")

    output_path = os.path.join(temp_dir, "output.mp4")

    # Concatenate segments
    cmd_concat = [
        ffmpeg_path,
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", video_list_file,
        "-c", "copy",
        output_path
    ]
    subprocess.run(cmd_concat, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return output_path

# ----------------------------
# UI
# ----------------------------
if st.button("🚀 Generate Video"):
    if not text.strip():
        st.warning("Please enter some text.")
    else:
        with st.spinner("Generating video..."):
            try:
                video_file = create_video(text)
                st.success("✅ Video created!")
                st.video(video_file)

                with open(video_file, "rb") as f:
                    st.download_button(
                        "⬇ Download Video",
                        data=f,
                        file_name="video.mp4",
                        mime="video/mp4"
                    )
            except Exception as e:
                st.error("Something went wrong.")
                st.code(str(e))
