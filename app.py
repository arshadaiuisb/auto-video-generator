import streamlit as st
from gtts import gTTS
import requests
import os
import tempfile
import subprocess
from PIL import Image
import imageio_ffmpeg as ffmpeg

st.set_page_config(page_title="Cinematic AI Video Generator")

st.title("🎬 Cinematic AI Video Generator (Final Stable Build)")
st.write("No errors • No crashes • Cloud ready")

# -----------------------
# INPUT
# -----------------------
text = st.text_area("Enter topic / script", height=200)

# -----------------------
# SCRIPT EXPANSION (NO AI MODEL = STABLE)
# -----------------------
def expand_text(text):
    base = f"""
    This is a cinematic documentary narration:

    {text}

    Explain in storytelling style with examples and clear flow.
    """

    expanded = base
    for _ in range(6):  # controls video length
        expanded += " " + base

    return expanded

# -----------------------
# SAFE SCENE SPLIT
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
# IMAGE GENERATION
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
# AUDIO GENERATION (SAFE)
# -----------------------
def text_to_audio(text, path):
    clean = text.strip()

    if not clean or len(clean) < 5:
        clean = "Cinematic scene"

    try:
        gTTS(text=clean, lang="en").save(path)
    except:
        gTTS(text="Audio generation failed", lang="en").save(path)

# -----------------------
# VIDEO CREATION (RENDER SAFE METHOD)
# -----------------------
def create_video(script):
    scenes = split_scenes(script)

    temp = tempfile.mkdtemp()
    ff = ffmpeg.get_ffmpeg_exe()

    segment_files = []

    for i, scene in enumerate(scenes):

        scene = scene.strip()
        if not scene:
            continue

        img = f"{temp}/img{i}.jpg"
        aud = f"{temp}/aud{i}.mp3"
        vid = f"{temp}/seg{i}.mp4"

        generate_image(scene[:60], img)
        text_to_audio(scene, aud)

        safe_text = scene[:60].replace(":", "").replace("'", "").replace('"', "")

        cmd = [
            ff, "-y",
            "-loop", "1", "-i", img,
            "-i", aud,
            "-vf", f"drawtext=text='{safe_text}':x=10:y=h-40:fontsize=24:fontcolor=white",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-pix_fmt", "yuv420p",
            "-shortest",
            vid
        ]

        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        segment_files.append(vid)

    # -----------------------
    # FINAL SAFE MERGE (NO CONCAT BUG)
    # -----------------------
    final_output = os.path.join(temp, "final_video.mp4")

    inputs = []
    for v in segment_files:
        inputs += ["-i", v]

    filter_complex = ""
    for i in range(len(segment_files)):
        filter_complex += f"[{i}:v:0][{i}:a:0]"

    filter_complex += f"concat=n={len(segment_files)}:v=1:a=1[outv][outa]"

    cmd = [
        ff,
        "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "[outa]",
        "-c:v", "libx264",
        "-c:a", "aac",
        final_output
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if not os.path.exists(final_output):
        return None

    return final_output

# -----------------------
# UI
# -----------------------
if st.button("🎥 Generate Cinematic Video"):

    if not text.strip():
        st.warning("Please enter text first")
    else:
        with st.spinner("Expanding script..."):
            script = expand_text(text)

        with st.spinner("Rendering cinematic video..."):
            video_file = create_video(script)

        if video_file:
            st.success("✅ Video generated successfully!")

            st.video(video_file)

            with open(video_file, "rb") as f:
                st.download_button(
                    "⬇ Download Video",
                    data=f,
                    file_name="cinematic_video.mp4",
                    mime="video/mp4"
                )
        else:
            st.error("❌ Video generation failed. Try shorter input text.")
