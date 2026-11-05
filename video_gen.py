#!/usr/bin/env python3
"""
Video Generation & Editing Module — GEMINI OMNI FLASH EDITION
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
    """Retrieves API key strictly from Streamlit secrets or environment variables."""
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

def detect_mime_type(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    mime_map = {
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".webp": "image/webp", ".mp4": "video/mp4", ".mp3": "audio/mpeg", ".wav": "audio/wav"
    }
    return mime_map.get(ext, mimetypes.guess_type(file_path)[0] or "application/octet-stream")

def upload_file(file_path, display_name=None):
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("Error: GEMINI_API_KEY set nahi hai.")
    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=300 * 1000))
    file_obj = client.files.upload(file=file_path, config=types.UploadFileConfig(display_name=display_name or os.path.basename(file_path), mime_type=detect_mime_type(file_path)))
    file_dict = json.loads(file_obj.model_dump_json())
    if "uri" in file_dict and file_dict["uri"]:
        file_dict["uri"] = strip_query_params(file_dict["uri"])
    return file_dict

def wait_for_active(file_name, max_attempts=60):
    api_key = get_api_key()
    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=30 * 1000))
    for _ in range(max_attempts):
        file_obj = client.files.get(name=file_name)
        state = file_obj.state
        if state == types.FileState.ACTIVE or str(state) == "ACTIVE":
            return json.loads(file_obj.model_dump_json())
        elif state == types.FileState.FAILED or str(state) == "FAILED":
            raise RuntimeError("File processing failed on backend.")
        time.sleep(3)
    raise TimeoutError("Timeout waiting for file to become ACTIVE.")

def resolve_or_upload_asset(asset_path, mime_type):
    if not asset_path:
        return None, None
    if "files/" in asset_path:
        return strip_query_params(asset_path), mime_type
    if os.path.exists(asset_path):
        meta = upload_file(asset_path)
        meta = wait_for_active(meta.get("name"))
        return strip_query_params(meta.get("uri")), meta.get("mimeType") or meta.get("mime_type")
    raise FileNotFoundError(f"Asset not found: {asset_path}")

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
# Streamlit UI Integration (`render_video_page`)
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

    if st.button("Generate Video 🎥", type="primary", use_container_width=True):
        if not prompt.strip():
            st.warning("कृपया पहले वीडियो का प्रॉम्प्ट दर्ज करें!")
            return

        with st.spinner("वीडियो जनरेट हो रहा है... कृपया प्रतीक्षा करें (इसमें कुछ समय लग सकता है)..."):
            try:
                video_uri = generate_video_interaction(
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                    duration=duration_sec,
                    resolution=resolution
                )
                st.success("वीडियो सफलतापूर्वक जनरेट हो गया है! ✅")
                
                # Download and display video
                video_bytes = download_video_bytes(video_uri)
                st.video(video_bytes)
                
                st.download_button(
                    label="📥 Download Video (.mp4)",
                    data=video_bytes,
                    file_name="gemini_generated_video.mp4",
                    mime="video/mp4"
                )
            except Exception as e:
                st.error(f"Error: {sanitize_error(e)}")
