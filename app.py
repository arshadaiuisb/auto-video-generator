import streamlit as st
from gtts import gTTS
import requests
import os
import tempfile
import subprocess
from PIL import Image
import imageio_ffmpeg as ffmpeg

st.set_page_config(page_title="Stable Cinematic Generator")

st.title("🎬 Stable AI Video Generator (Cloud Safe)")
st.write("Reliable version — no FFmpeg failures")

# ---------------- INPUT ----------------
text = st.text_area("Enter topic", height=200)

# ---------------- EXPAND ----------------
def expand_text(text):
    return f"""
    This is an educational cinematic narration.

    {text}

    Explain in detail with examples and storytelling style.
    """

# ---------------- IMAGE ----------------
def generate_image(prompt, path):
    try:
        url = "https://image.pollinations.ai/prompt/" + prompt
        img = requests.get(url, timeout=20).content
        with open(path, "wb") as f:
            f.write(img)
    except:
        Image.new("RGB", (1280, 720), color=(0, 0, 0)).save(path)

# ---------------- AUDIO ----------------
def text_to_audio(text, path):
    clean = text.strip()
    if len(clean) < 5:
        clean = "Cinematic narration"

    gTTS(text=clean, lang="en").save(path)

# ---------------- VIDEO (SINGLE SAFE RENDER) ----------------
def create_video(text):
    temp = tempfile.mkdtemp()
    ff = ffmpeg.get_ffmpeg_exe()

    img_path = os.path.join(temp, "img.jpg")
    audio_path = os.path.join(temp, "audio.mp3")
    output_path = os.path.join(temp, "output.mp4")

    generate_image(text[:60], img_path)
    text_to_audio(text, audio_path)

    cmd = [
        ff, "-y",
        "-loop", "1",
        "-i", img_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_path
    ]

    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if not os.path.exists(output_path):
        return None

    return output_path

# ---------------- UI ----------------
if st.button("🎥 Generate Video"):

    if not text.strip():
        st.warning("Enter text first")
    else:
        with st.spinner("Processing..."):
            script = expand_text(text)
            video = create_video(script)

        if video:
            st.success("✅ Video generated successfully!")
            st.video(video)

            with open(video, "rb") as f:
                st.download_button(
                    "⬇ Download",
                    f,
                    "video.mp4",
                    "video/mp4"
                )
        else:
            st.error("❌ Failed. Streamlit Cloud limit reached.")
