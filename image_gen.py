"""
Free Pro Storybook Studio — Hugging Face & Pollinations Version
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

HF_MODEL_OPTIONS = {
    "⚡ Fast (FLUX.1-schnell)": "black-forest-labs/FLUX.1-schnell",
    "💎 Best Quality (FLUX.1-dev)": "black-forest-labs/FLUX.1-dev",
}

def get_hf_api_key() -> str:
    key = os.environ.get("HF_API_KEY", "")
    if not key:
        try:
            key = st.secrets.get("HF_API_KEY", "")
        except Exception:
            pass
    return key

def generate_with_huggingface(prompt: str, negative_prompt: str, model_id: str, width: int, height: int):
    hf_key = get_hf_api_key()
    if not hf_key:
        return None, "HF_API_KEY set nahi hai."

    try:
        from huggingface_hub import InferenceClient
    except ImportError:
        return None, "huggingface_hub package installed nahi hai."

    try:
        client = InferenceClient(provider="auto", api_key=hf_key)
        kwargs = {"negative_prompt": negative_prompt, "width": width, "height": height}
        if "dev" in model_id.lower():
            kwargs["num_inference_steps"] = 30
        else:
            kwargs["num_inference_steps"] = 4
            
        pil_image = client.text_to_image(prompt, model=model_id, **kwargs)
        buf = BytesIO()
        pil_image.save(buf, format="PNG")
        return buf.getvalue(), None
    except Exception as e:
        return None, str(e)

def build_pollinations_url(prompt: str, neg_prompt: str, width: int, height: int, seed: int) -> str:
    encoded_prompt = urllib.parse.quote(prompt)
    encoded_neg = urllib.parse.quote(neg_prompt)
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={seed}&model=flux&nologo=true&negative={encoded_neg}"

def render_image_page(supabase=None, user=None):
    st.subheader("🎨 Free Pro Storybook Studio")
    st.write("Hugging Face (FLUX) aur Pollinations ke zariye high-quality images banayein:")

    hf_available = bool(get_hf_api_key())
    if hf_available:
        st.success("✅ Hugging Face (FLUX) Active hai!")
    else:
        st.info("ℹ️ Hugging Face API key optional hai (Pollinations default free mode available hai).")

    img_prompt = st.text_area("✨ Prompt Box (मुख्य विवरण):", placeholder="Cinematic portrait of a cute character...")
    neg_prompt = st.text_area("🚫 Negative Prompt:", value="blurry, distorted face, low quality")

    col1, col2 = st.columns(2)
    with col1:
        ratio_option = st.selectbox("📐 Aspect Ratio", ["Landscape (16:9)", "Portrait (9:16)", "Square (1:1)"])
        if "16:9" in ratio_option:
            w, h = 1024, 576
        elif "9:16" in ratio_option:
            w, h = 576, 1024
        else:
            w, h = 768, 768
    with col2:
        style_option = st.selectbox("🎭 Style", ["Storybook Illustration", "2D Animation", "Cinematic"])

    if st.button("🚀 Generate Image Now", type="primary", use_container_width=True):
        if not img_prompt.strip():
            st.warning("⚠️ कृपया प्रॉम्प्ट दर्ज करें!")
            return

        with st.spinner("🖼️ इमेज जनरेट हो रही है..."):
            final_prompt = f"{img_prompt.strip()}, {style_option} style, high quality"
            img_bytes, err_msg = None, None

            # Try Hugging Face first if key is available
            if hf_available:
                img_bytes, err_msg = generate_with_huggingface(final_prompt, neg_prompt, HF_MODEL_OPTIONS["⚡ Fast (FLUX.1-schnell)"], w, h)

            # Fallback to Pollinations if HF fails or no key
            if not img_bytes:
                seed_val = int(time.time())
                url = build_pollinations_url(final_prompt, neg_prompt, w, h, seed_val)
                try:
                    resp = requests.get(url, timeout=60)
                    if resp.status_code == 200 and len(resp.content) > 1000:
                        img_bytes = resp.content
                except Exception as e:
                    err_msg = str(e)

            if img_bytes:
                st.success("✨ Image safaltapoorvak taiyar ho gayi!")
                st.image(img_bytes, caption="Generated Storybook Image", use_container_width=True)
                st.download_button(
                    label="📥 Download Image",
                    data=img_bytes,
                    file_name="generated_image.png",
                    mime="image/png"
                )
            else:
                st.error(f"🚨 Image generation fail ho gayi: {err_msg}")
