import streamlit as st
from gtts import gTTS
import requests
import os
import tempfile
import subprocess
from PIL import Image
import imageio_ffmpeg as ffmpeg

st.set_page_config(page_title="Cinematic AI Video Generator")

st.title("🎬 Cinematic AI Video Generator (Final Stable)")
st.write("Fully stable version (no crashes, no missing files)")

# -----------------------
# INPUT
# -----------------------
text = st.text_area("Enter topic / script", height=200)

# -----------------------
# SCRIPT EXPANSION
# -----------------------
def expand_text(text):
    base = f"""
    This is a cinematic documentary narration:

    {text}

    Explain in storytelling style with examples and smooth flow.
    """

    expanded = base
    for _ in range(6):
        expanded += " " + base

    return expanded

# -----------------------
# SCENE SPLIT
# -----------------------
def split_scenes(text):
    sentences = text.split(".")
    scenes = []
    chunk = ""

    for s in sentences:
        s = s.strip()
        if not s:
            continue

        if len(chunk) < 180:
            chunk += s + ". "
        else:
            if len(chunk.strip()) > 10:
                scenes.append(chunk.strip())
            chunk = s + ". "

    if len(chunk.strip()) > 10:
        scenes.append(chunk.strip())

    return scenes

# -----------------------
# IMAGE
# -----------------------
def generate_image(prompt, path):
    try:
        url = "https://image.pollinations.ai/prompt/" + prompt
        img = requests.get(url, timeout=20).content
        with open(path, "wb") as f:
            f.write(img)
    except:
        Image.new("RGB", (1280, 720), color=(0, 0, 0)).save(path)

# -----------------------
# AUDIO
# -----------------------
def text_to_audio(text, path):
    clean = text.strip()

    if not clean or len(clean) < 5:
        clean = "Cinematic scene"

    try:
        gTTS(text=clean, lang="en").save(path)
    except:
        gTTS(text="Audio fallback", lang="en").save(path)

# -----------------------
# VIDEO CREATION (FIXED)
# -----------------------
def create_video(script):
    scenes = split_scenes(script)

    temp = tempfile.mkdtemp()
    ff = ffmpeg.get_ffmpeg_exe()

    segments = []

    for i, scene in enumerate(scenes):

        scene = scene.strip()
        if not scene:
            continue

        img = f"{temp}/img{i}.jpg"
        aud = f"{temp}/aud{i}.mp3"
        vid = f"{temp}/seg{i}.mp4"

        generate_image(scene[:50], img)
        text_to_audio(scene, aud)

        safe_text = scene[:50].replace(":", "").replace("'", "").replace('"', "")

        cmd = [
            ff, "-y",
            "-loop", "1", "-i", img,
            "-i", aud,
            "-vf", f"drawtext=text='{safe_text}':x=10:y=h-40:fontsize=24:fontcolor=white",
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-shortest",
            vid
        ]

        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        segments.append(vid)

    # 🔥 SAFE FINAL OUTPUT PATH (NO COPY)
    final_output = os.path.join(temp, "final_video.mp4")

    listfile = os.path.join(temp, "list.txt")

    with open(listfile, "w") as f:
        for s in segments:
            f.write(f"file '{s}'\n")

    result = subprocess.run([
        ff, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", listfile,
        "-c", "copy",
        final_output
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # -----------------------
    # CRITICAL CHECK
    # -----------------------
    if not os.path.exists(final_output):
        st.error("❌ Video generation failed (FFmpeg issue). Try shorter text.")
        return None

    return final_output

# -----------------------
# UI
# -----------------------
if st.button("🎥 Generate Cinematic Video"):

    if not text.strip():
        st.warning("Please enter text")
    else:
        with st.spinner("Expanding script..."):
            script = expand_text(text)

        with st.spinner("Creating video..."):
            video_file = create_video(script)

        if video_file:
            st.success("✅ Video Ready!")
            st.video(video_file)

            with open(video_file, "rb") as f:
                st.download_button(
                    "⬇ Download Video",
                    data=f,
                    file_name="cinematic.mp4",
                    mime="video/mp4"
                )
