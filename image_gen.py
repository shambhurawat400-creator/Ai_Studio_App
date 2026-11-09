"""
Free Pro Storybook Studio — Nano Banana Priority Version
"""

import hashlib
import logging
import os
import base64
import time
import urllib.parse
from io import BytesIO

import requests
import streamlit as st
from PIL import Image

logger = logging.getLogger(__name__)

NANO_BANANA_MODEL_CANDIDATES = ["gemini-2.5-flash-image", "gemini-2.5-flash-image-preview"]
MAX_DIMENSION = 2048

@st.cache_resource(show_spinner=False)
def get_gemini_client():
    try:
        from google import genai
    except ImportError:
        return None

    api_key = None
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        logger.error("Failed to init Gemini client: %s", e)
        return None

def generate_with_nano_banana(client, prompt_text: str, aspect_ratio: str, reference_image_bytes):
    from google.genai import types

    contents = [prompt_text]
    if reference_image_bytes:
        try:
            contents.append(Image.open(BytesIO(reference_image_bytes)))
        except Exception as e:
            logger.warning("Could not decode reference image: %s", e)

    last_error = None
    for model_name in NANO_BANANA_MODEL_CANDIDATES:
        try:
            config = types.GenerateContentConfig(image_config=types.ImageConfig(aspect_ratio=aspect_ratio))
            response = client.models.generate_content(model=model_name, contents=contents, config=config)
            
            for part in response.candidates[0].content.parts:
                if getattr(part, "inline_data", None) is not None:
                    return part.inline_data.data, None
            last_error = f"[{model_name}] Response mila lekin image data nahi tha."
        except Exception as e:
            last_error = f"[{model_name}] {type(e).__name__}: {e}"
            logger.warning("Nano Banana attempt failed: %s", last_error)

    return None, last_error

def render_image_page(supabase=None, user=None):
    st.subheader("🎨 Nano Banana Storybook Studio")
    st.write("Gemini Nano Banana (Image Generation) ke zariye high-quality images banayein:")

    gemini_client = get_gemini_client()
    if gemini_client:
        st.success("✅ Nano Banana (Gemini) Active hai!")
    else:
        st.error("⚠️ GEMINI_API_KEY set nahi hai ya image generation supported nahi hai.")

    img_prompt = st.text_area("✨ Prompt Box (मुख्य विवरण):", placeholder="Cinematic portrait of a cute character...")
    
    col1, col2 = st.columns(2)
    with col1:
        ratio_option = st.selectbox("📐 Aspect Ratio", ["16:9", "9:16", "1:1"])
    with col2:
        style_option = st.selectbox("🎭 Style", ["Storybook Illustration", "2D Animation", "Cinematic"])

    if st.button("🚀 Generate with Nano Banana", type="primary", use_container_width=True):
        if not gemini_client:
            st.error("🚨 Pehle apni valid GEMINI_API_KEY Streamlit Secrets mein set karein.")
            return
        if not img_prompt.strip():
            st.warning("⚠️ कृपया प्रॉम्प्ट दर्ज करें!")
            return

        with st.spinner("🍌 Nano Banana (Gemini) image generate kar raha hai..."):
            final_prompt = f"{img_prompt.strip()}, {style_option} style, high quality"
            img_bytes, err_msg = generate_with_nano_banana(gemini_client, final_prompt, ratio_option, None)

            if img_bytes:
                st.success("✨ Image safaltapoorvak taiyar ho gayi!")
                st.image(img_bytes, caption="Nano Banana Generated Image", use_container_width=True)
                st.download_button(
                    label="📥 Download Image",
                    data=img_bytes,
                    file_name="nano_banana_image.png",
                    mime="image/png"
                )
            else:
                st.error("🚨 Nano Banana image generation fail ho gayi.")
                if err_msg:
                    with st.expander("❌ Error Details"):
                        st.code(err_msg)
