import streamlit as st
from gtts import gTTS
import requests, os, tempfile, subprocess
from PIL import Image
import imageio_ffmpeg as ffmpeg
from transformers import pipeline

st.set_page_config(page_title="Cinematic Video Generator")

st.title("🎬 Cinematic AI Video Generator")

text = st.text_area("Enter topic / text", height=200)

# -----------------------
# AI Script Generator
# -----------------------
generator = pipeline("text2text-generation", model="google/flan-t5-base")

def expand_text(text):
    prompt = f"""
    Create a detailed cinematic documentary-style script (5-8 minutes).
    Use emotional storytelling, explanations, and smooth narration.

    {text}
    """
    return generator(prompt, max_length=1200)[0]['generated_text']

# -----------------------
# Scene Split
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
# Image Generator
# -----------------------
def generate_image(prompt, path):
    try:
        url = "https://image.pollinations.ai/prompt/" + prompt
        img = requests.get(url, timeout=20).content
        with open(path, "wb") as f:
            f.write(img)
    except:
        Image.new("RGB", (1280,720)).save(path)

# -----------------------
# Voice
# -----------------------
def text_to_audio(text, path):
    gTTS(text=text, lang="en").save(path)

# -----------------------
# Video Creator
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

        cmd = [
            ff,"-y",
            "-loop","1","-i",img,
            "-i",aud,
            "-vf",f"drawtext=text='{scene[:60]}':x=10:y=h-40:fontsize=24:fontcolor=white",
            "-c:v","libx264","-tune","stillimage",
            "-c:a","aac","-shortest",
            vid
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        segments.append(vid)

    # concat
    listfile = f"{temp}/list.txt"
    with open(listfile,"w") as f:
        for s in segments:
            f.write(f"file '{s}'\n")

    out = f"{temp}/final.mp4"

    subprocess.run([
        ff,"-y","-f","concat","-safe","0",
        "-i",listfile,"-c","copy",out
    ])

    return out

# -----------------------
# UI
# -----------------------
if st.button("🎥 Generate Cinematic Video"):
    if not text:
        st.warning("Enter text")
    else:
        with st.spinner("Generating cinematic script..."):
            script = expand_text(text)

        with st.spinner("Rendering video..."):
            video = create_video(script)

        st.success("Done!")
        st.video(video)

        with open(video,"rb") as f:
            st.download_button("Download", f, "cinematic.mp4")
