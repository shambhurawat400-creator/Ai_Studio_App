"""
Video Generation & Editing Module — Direct API Integration
"""

import os
import time
import streamlit as st
from google import genai
from google.genai import types, errors

DEFAULT_MODEL = "gemini-omni-1.2-flash"

def get_api_key():
    api_key = st.secrets.get("GEMINI_API_KEY") if "GEMINI_API_KEY" in st.secrets else os.environ.get("GEMINI_API_KEY", "")
    return api_key

def generate_video_interaction(prompt, aspect_ratio="16:9", duration="10s", resolution="720p", model=DEFAULT_MODEL):
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY set nahi hai!")
    
    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=900 * 1000))
    input_parts = [{"type": "text", "text": prompt}]
    video_config = {
        "type": "video", 
        "delivery": "uri", 
        "aspect_ratio": aspect_ratio, 
        "duration": duration, 
        "resolution": resolution
    }
    
    # Backend API call for video generation
    interaction = client.interactions.create(
        model=model,
        input=input_parts,
        response_format=video_config
    )
    if not interaction.output_video or not interaction.output_video.uri:
        raise RuntimeError("Video generation fail ho gayi — koi video output uri nahi mila.")
    return interaction.output_video.uri

def download_video_bytes(uri):
    api_key = get_api_key()
    client = genai.Client(api_key=api_key)
    return client.files.download(file=uri)

def render_video_page():
    st.subheader("🎬 AI Video Studio — Direct Code Integration")
    st.write("Yahan aap prompt daalkar direct video file generate aur download kar sakte hain:")

    api_key = get_api_key()
    if not api_key:
        st.error("🚨 GEMINI_API_KEY set nahi hai.")
        return

    prompt = st.text_area("Video Prompt:", placeholder="Cinematic drone shot of a futuristic neon city...")

    col1, col2, col3 = st.columns(3)
    with col1:
        aspect_ratio = st.selectbox("Aspect Ratio:", ["16:9", "9:16"])
    with col2:
        duration_sec = st.selectbox("Duration:", ["5s", "10s", "15s"])
    with col3:
        resolution = st.selectbox("Resolution:", ["720p", "1080p"])

    if st.button("Generate Video File 🎥", type="primary", use_container_width=True):
        if not prompt.strip():
            st.warning("Kripya prompt darj karein!")
            return

        with st.status("Video server par render ho raha hai...", expanded=True) as status:
            try:
                st.write("⏳ API ko request bheji ja rahi hai...")
                video_uri = generate_video_interaction(
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                    duration=duration_sec,
                    resolution=resolution
                )
                
                st.write("📥 Video file download ki ja rahi hai...")
                video_bytes = download_video_bytes(video_uri)
                status.update(label="Video safaltapoorvak taiyar ho gaya hai! ✅", state="complete", expanded=False)
            except Exception as e:
                status.update(label="Video generation fail ho gaya ❌", state="error", expanded=True)
                st.error(f"Error: {str(e)}")
                return

        # Direct video player display
        st.video(video_bytes)
        st.success("Video successfully generated!")
        st.download_button(
            label="📥 Download Video (.mp4)",
            data=video_bytes,
            file_name="generated_ai_video.mp4",
            mime="video/mp4"
        )
