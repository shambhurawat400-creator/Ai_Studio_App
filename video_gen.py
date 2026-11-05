#!/usr/bin/env python3
"""
Video Generation & Editing Module — GEMINI OMNI FLASH EDITION WITH LIVE PROGRESS
"""

import os
import json
import mimetypes
import re
import subprocess
import sys
import time
import urllib.parse
import uuid
import streamlit as st
from google import genai
from google.genai import types, errors

DEFAULT_MODEL = "gemini-omni-1.2-flash"

def get_api_key():
    api_key = None
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY", "")
    return api_key

def strip_query_params(url):
    if not url:
        return ""
    parsed = urllib.parse.urlparse(url)
    return urllib.parse.urlunparse(parsed._replace(query=""))

def sanitize_error(err):
    if not err:
        return ""
    if isinstance(err, errors.APIError):
        parts = []
        if getattr(err, "code", None):
            parts.append(str(err.code))
        if getattr(err, "status", None):
            parts.append(f"({err.status})")
        if getattr(err, "message", None):
            parts.append(f": {err.message}")
        err_str = " ".join(parts) if parts else str(err)
    else:
        err_str = str(err)
    key = get_api_key()
    if key and len(key) >= 8:
        err_str = err_str.replace(key, "[REDACTED_KEY]")
    return err_str

def generate_video_interaction(prompt, aspect_ratio="16:9", duration="10s", resolution="720p", model=DEFAULT_MODEL):
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY set nahi hai!")
    
    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=600 * 1000))
    input_parts = [{"type": "text", "text": prompt}]
    video_config = {"type": "video", "delivery": "uri", "aspect_ratio": aspect_ratio, "duration": duration, "resolution": resolution}
    
    interaction = client.interactions.create(
        model=model,
        input=input_parts,
        response_format=video_config
    )
    if not interaction.output_video or not interaction.output_video.uri:
        raise RuntimeError("Video generation fail ho gayi — koi video output nahi mila.")
    return interaction.output_video.uri

def download_video_bytes(uri):
    api_key = get_api_key()
    client = genai.Client(api_key=api_key)
    return client.files.download(file=uri)

# ---------------------------------------------------------------------------
# Streamlit UI Integration with 16:9 Live Percentage Progress Frame
# ---------------------------------------------------------------------------

def render_video_page():
    st.subheader("🎬 AI Video Studio — Gemini Omni Flash")
    st.write("यहाँ से आप टेक्स्ट प्रॉम्प्ट के ज़रिए शानदार सिनेमाई वीडियो जनरेट कर सकते हैं:")

    api_key = get_api_key()
    if not api_key:
        st.error("🚨 GEMINI_API_KEY set nahi hai. Kripya Streamlit Secrets mein key save karein.")
        return

    prompt = st.text_area("वीडियो का विवरण (Prompt) दर्ज करें:", placeholder="जैसे: Cinematic drone shot of a futuristic neon city at night...")

    col1, col2, col3 = st.columns(3)
    with col1:
        aspect_ratio = st.selectbox("Aspect Ratio:", ["16:9", "9:16"])
    with col2:
        duration_sec = st.selectbox("Duration:", ["5s", "10s", "15s"])
    with col3:
        resolution = st.selectbox("Resolution:", ["720p", "1080p", "4k"])

    # 16:9 Preview Frame Container
    st.markdown("### 🖼️ Preview Frame (16:9)")
    frame_container = st.empty()

    # Default empty or placeholder box inside 16:9 ratio wrapper
    frame_container.markdown(
        """
        <div style="width: 100%; aspect-ratio: 16/9; background-color: #0e1117; border: 2px dashed #30333d; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: #808495;">
            Video preview yahan dikhega...
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("Generate Video 🎥", type="primary", use_container_width=True):
        if not prompt.strip():
            st.warning("कृपया पहले वीडियो का प्रॉम्प्ट दर्ज करें!")
            return

        # Live Percentage Progress Simulation inside 16:9 Frame
        progress_bar = st.progress(0, text="वीडियो जनरेशन शुरू हो रहा है... 0%")
        
        try:
            # Simulated smooth percentage ticks while background API processes
            for pct in range(10, 90, 15):
                time.sleep(1.2)
                progress_bar.progress(pct, text=f"वीडियो तैयार हो रहा है... {pct}%")
                frame_container.markdown(
                    f"""
                    <div style="width: 100%; aspect-ratio: 16/9; background-color: #1a1c24; border: 2px solid #ff4b4b; border-radius: 10px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #ffffff; font-family: sans-serif;">
                        <h3 style="margin: 0; color: #ff4b4b;">Processing... {pct}%</h3>
                        <p style="margin: 5px 0 0 0; font-size: 14px; color: #a3a8b8;">Gemini Omni Flash rendering video</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # Actual API Call
            video_uri = generate_video_interaction(
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                duration=duration_sec,
                resolution=resolution
            )
            
            progress_bar.progress(100, text="वीडियो सफलतापर्वक तैयार हो गया है! 100%")
            time.sleep(0.5)
            progress_bar.empty()
            
            # Download and display final video inside the 16:9 container frame
            video_bytes = download_video_bytes(video_uri)
            
            with frame_container.container():
                st.video(video_bytes)
            
            st.success("वीडियो सफलतापूर्वक जनरेट हो गया है! ✅")
            st.download_button(
                label="📥 Download Video (.mp4)",
                data=video_bytes,
                file_name="gemini_generated_video.mp4",
                mime="video/mp4"
            )
        except Exception as e:
            progress_bar.empty()
            st.error(f"Error: {sanitize_error(e)}")
