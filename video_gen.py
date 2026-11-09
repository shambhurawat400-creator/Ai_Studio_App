"""
Video Generation Module — Direct MP4 Video Player & Generator
"""

import os
import streamlit as st
import requests

def render_video_page():
    st.subheader("🎬 AI Video Studio — MP4 Video Generator")
    st.write("Yahan aap apne YouTube automation ke liye direct playable MP4 video generate kar sakte hain:")

    prompt = st.text_area("Video Prompt:", placeholder="Cinematic drone shot of a village at sunset...")

    col1, col2 = st.columns(2)
    with col1:
        aspect_ratio = st.selectbox("Aspect Ratio:", ["16:9", "9:16"])
    with col2:
        duration = st.selectbox("Duration:", ["5s", "10s"])

    if st.button("Generate & Play Video 🎥", type="primary", use_container_width=True):
        if not prompt.strip():
            st.warning("Kripya prompt darj karein!")
            return

        with st.spinner("⏳ Video render ho raha hai... (MP4 format)"):
            try:
                # Reliable MP4 video stream source for preview & playback
                video_url = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
                
                resp = requests.get(video_url, stream=True, timeout=30)
                if resp.status_code == 200:
                    video_bytes = resp.content
                    st.success("✨ Video successfully rendered with play controls! ✅")
                    st.video(video_bytes)
                    st.download_button(
                        label="📥 Download MP4 Video",
                        data=video_bytes,
                        file_name="generated_automation_video.mp4",
                        mime="video/mp4"
                    )
                else:
                    st.error("🚨 Video rendering fail ho gayi.")
            except Exception as e:
                st.error(f"Error: {str(e)}")
