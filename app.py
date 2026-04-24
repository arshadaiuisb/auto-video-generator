import streamlit as st
from gtts import gTTS
import requests, os, tempfile, subprocess
from PIL import Image
import imageio_ffmpeg as ffmpeg

st.set_page_config(page_title="Cinematic Video Generator")

st.title("🎬 Cinematic AI Video Generator (Stable)")
st.write("Generate 5+ minute cinematic videos automatically")

# -----------------------
# INPUT
# -----------------------
text = st.text_area("Enter topic / text", height=200)

# -----------------------
# SAFE SCRIPT EXPANSION (NO AI MODEL)
# -----------------------
def expand_text(text):
    base = f"""
    This is a cinematic educational narration:

    {text}

    Explain this in a detailed, engaging, storytelling style with examples.
    """

    expanded = base
    for _ in range(8):  # increase length (controls video duration)
        expanded += " " + base

    return expanded

# -----------------------
# SCENE SPLIT
# -----------------------
def split_scenes(text):
    sentences = text.split(".")
    scenes, chunk = [], ""

    for s in sentences:
        if len(chunk) < 200:
            chunk += s + ". "
        else:
            scenes.append(chunk.strip())
            chunk = s + ". "

    if chunk:
        scenes.append(chunk.strip())

    return scenes

# -----------------------
# IMAGE GENERATOR
# -----------------------
def generate_image(prompt, path):
    try:
        url = "https://image.pollinations.ai/prompt/" + prompt
        img = requests.get(url, timeout=20).content
        with open(path, "wb") as f:
            f.write(img)
    except:
        Image.new("RGB", (1280, 720), color=(0,0,0)).save(path)

# -----------------------
# VOICE
# -----------------------
def text_to_audio(text, path):
    gTTS(text=text, lang="en").save(path)

# -----------------------
# VIDEO CREATOR (FFmpeg)
# -----------------------
def create_video(script):
    scenes = split_scenes(script)
    temp = tempfile.mkdtemp()
    ff = ffmpeg.get_ffmpeg_exe()

    segments = []

    for i, scene in enumerate(scenes):
        img = f"{temp}/img{i}.jpg"
        aud = f"{temp}/aud{i}.mp3"
        vid = f"{temp}/seg{i}.mp4"

        generate_image(scene[:50], img)
        text_to_audio(scene, aud)

        # SAFE subtitle text (avoid crash)
        safe_text = scene[:50].replace(":", "").replace("'", "").replace('"', "")

        cmd = [
            ff, "-y",
            "-loop", "1", "-i", img,
            "-i", aud,
            "-vf", f"drawtext=text='{safe_text}':x=10:y=h-40:fontsize=24:fontcolor=white",
            "-c:v", "libx264", "-tune", "stillimage",
            "-c:a", "aac",
            "-shortest",
            vid
        ]

        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        segments.append(vid)

    # CONCAT ALL SEGMENTS
    listfile = f"{temp}/list.txt"
    with open(listfile, "w") as f:
        for s in segments:
            f.write(f"file '{s}'\n")

    output = f"{temp}/final.mp4"

    subprocess.run([
        ff, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", listfile,
        "-c", "copy",
        output
    ])

    return output

# -----------------------
# UI BUTTON
# -----------------------
if st.button("🎥 Generate Cinematic Video"):
    if not text.strip():
        st.warning("Please enter some text")
    else:
        with st.spinner("Expanding script..."):
            script = expand_text(text)

        with st.spinner("Creating video (this may take time)..."):
            video = create_video(script)

        st.success("✅ Video Ready!")
        st.video(video)

        with open(video, "rb") as f:
            st.download_button(
                "⬇ Download Video",
                data=f,
                file_name="cinematic_video.mp4",
                mime="video/mp4"
            )
