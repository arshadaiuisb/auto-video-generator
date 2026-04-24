import streamlit as st
from gtts import gTTS
from moviepy.editor import *
import requests
import os
import tempfile

st.set_page_config(page_title="Auto Video Generator", layout="centered")

st.title("🎬 Auto Video Generator (NotebookLM Style Clone)")
st.write("Paste your script or document and generate a video automatically.")

# ----------------------------
# Input Text
# ----------------------------
text = st.text_area("✍️ Enter your content here", height=200)

# ----------------------------
# Helper: Generate Image
# ----------------------------
def generate_image(prompt, path):
    try:
        url = "https://image.pollinations.ai/prompt/" + prompt
        img = requests.get(url).content
        with open(path, "wb") as f:
            f.write(img)
    except:
        # fallback blank image
        from PIL import Image
        Image.new("RGB", (1280, 720), color=(0, 0, 0)).save(path)

# ----------------------------
# Helper: Text to Speech
# ----------------------------
def text_to_audio(text, path):
    tts = gTTS(text=text, lang="en")
    tts.save(path)

# ----------------------------
# Split into scenes (simple logic)
# ----------------------------
def split_scenes(text):
    sentences = text.split(".")
    scenes = [s.strip() for s in sentences if len(s.strip()) > 5]
    return scenes

# ----------------------------
# Video Generator Core
# ----------------------------
def create_video(text):

    scenes = split_scenes(text)

    clips = []
    temp_dir = tempfile.mkdtemp()

    for i, scene in enumerate(scenes):

        audio_path = os.path.join(temp_dir, f"audio_{i}.mp3")
        image_path = os.path.join(temp_dir, f"img_{i}.jpg")

        # voice
        text_to_audio(scene, audio_path)
        audio = AudioFileClip(audio_path)

        # image
        generate_image(scene[:60], image_path)
        img_clip = ImageClip(image_path).set_duration(audio.duration)

        # combine
        video = img_clip.set_audio(audio)
        clips.append(video)

    final_video = concatenate_videoclips(clips, method="compose")

    output_path = os.path.join(temp_dir, "output.mp4")
    final_video.write_videofile(output_path, fps=24)

    return output_path

# ----------------------------
# UI Button
# ----------------------------
if st.button("🚀 Generate Video"):

    if not text.strip():
        st.warning("Please enter some text first.")
    else:
        with st.spinner("Creating your video..."):

            video_file = create_video(text)

        st.success("✅ Video Generated Successfully!")
        st.video(video_file)

        with open(video_file, "rb") as f:
            st.download_button(
                label="⬇ Download Video",
                data=f,
                file_name="generated_video.mp4",
                mime="video/mp4"
            )
