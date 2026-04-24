import streamlit as st
from gtts import gTTS
import os
import tempfile
import subprocess
import imageio_ffmpeg as ffmpeg
from PIL import Image
import requests

st.set_page_config(page_title="Avatar Video Generator")

st.title("🎬 AI Avatar Video Generator (With Lip Sync Style)")

# ---------------- INPUT ----------------
text = st.text_area("Enter script", height=200)
avatar = st.file_uploader("Upload Avatar Image", type=["png", "jpg", "jpeg"])

# ---------------- EXPAND TEXT ----------------
def expand_text(text):
    return f"""
    This is a cinematic narration:

    {text}

    Explain in detail with storytelling style.
    """

# ---------------- AUDIO ----------------
def text_to_audio(text, path):
    gTTS(text=text, lang="en").save(path)

# ---------------- VIDEO GENERATION ----------------
def create_video(text, avatar_path):
    temp = tempfile.mkdtemp()
    ff = ffmpeg.get_ffmpeg_exe()

    audio_path = os.path.join(temp, "audio.mp3")
    video_path = os.path.join(temp, "output.mp4")

    text_to_audio(text, audio_path)

    # If no avatar uploaded
    if avatar_path is None:
        img = Image.new("RGB", (1280, 720), color=(0, 0, 0))
        avatar_file = os.path.join(temp, "avatar.jpg")
        img.save(avatar_file)
    else:
        avatar_file = avatar_path

    # 🔥 SIMPLE LIP-SYNC STYLE EFFECT (zoom + audio sync)
    cmd = [
        ff, "-y",
        "-loop", "1",
        "-i", avatar_file,
        "-i", audio_path,
        "-vf",
        "zoompan=z='min(zoom+0.0015,1.2)':d=1",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        "-shortest",
        video_path
    ]

    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if not os.path.exists(video_path):
        return None

    return video_path

# ---------------- UI ----------------
if st.button("🎥 Generate Avatar Video"):

    if not text.strip():
        st.warning("Enter script first")
    else:
        script = expand_text(text)

        with st.spinner("Creating video..."):
            video = create_video(script, avatar)

        if video:
            st.success("✅ Video Ready!")
            st.video(video)

            with open(video, "rb") as f:
                st.download_button("⬇ Download", f, "avatar_video.mp4")
        else:
            st.error("❌ Failed to generate video")
