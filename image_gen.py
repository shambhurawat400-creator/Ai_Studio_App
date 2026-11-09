"""
Free Pro Storybook Studio — Fully Automated Multi-Provider Version (Nano Banana + Hugging Face + Pollinations)
"""

import hashlib
import logging
import os
import base64
import time
import urllib.parse
from datetime import datetime
from io import BytesIO

import requests
import streamlit as st
from PIL import Image

logger = logging.getLogger(__name__)

NANO_BANANA_MODEL_CANDIDATES = ["gemini-2.5-flash-image", "gemini-2.5-flash-image-preview", "imagen-3.0-generate-002"]
HF_MODEL_OPTIONS = {
    "⚡ Fast (FLUX.1-schnell)": "black-forest-labs/FLUX.1-schnell",
    "💎 Best Quality (FLUX.1-dev)": "black-forest-labs/FLUX.1-dev",
}

def get_gemini_client():
    try:
        from google import genai
    except ImportError:
        return None
    api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception:
        return None

def get_hf_api_key() -> str:
    key = os.environ.get("HF_API_KEY", "")
    if not key:
        try:
            key = st.secrets.get("HF_API_KEY", "")
        except Exception:
            pass
    return key

def generate_with_nano_banana(client, prompt: str, aspect_ratio: str):
    from google.genai import types
    for model_name in NANO_BANANA_MODEL_CANDIDATES:
        try:
            config = types.GenerateContentConfig(image_config=types.ImageConfig(aspect_ratio=aspect_ratio))
            response = client.models.generate_content(model=model_name, contents=[prompt], config=config)
            for part in response.candidates[0].content.parts:
                if getattr(part, "inline_data", None) is not None:
                    return part.inline_data.data, None
        except Exception as e:
            logger.warning("Nano Banana model %s failed: %s", model_name, e)
    return None, "Nano Banana generation failed across all candidates."

def generate_with_huggingface(prompt: str, negative_prompt: str, model_id: str, width: int, height: int):
    hf_key = get_hf_api_key()
    if not hf_key:
        return None, "HF_API_KEY set nahi hai."
    try:
        from huggingface_hub import InferenceClient
        client = InferenceClient(provider="auto", api_key=hf_key)
        kwargs = {"negative_prompt": negative_prompt, "width": width, "height": height}
        kwargs["num_inference_steps"] = 30 if "dev" in model_id.lower() else 4
        pil_image = client.text_to_image(prompt, model=model_id, **kwargs)
        buf = BytesIO()
        pil_image.save(buf, format="PNG")
        return buf.getvalue(), None
    except Exception as e:
        return None, str(e)

def build_pollinations_url(prompt: str, neg_prompt: str, width: int, height: int, seed: int) -> str:
    encoded_prompt = urllib.parse.quote(prompt)
    encoded_neg = urllib.parse.quote(neg_prompt)
    # nologo=true ensures watermark is removed from the corner
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={seed}&model=flux&nologo=true&private=true&enhance=false&negative={encoded_neg}"

def render_image_page(supabase=None, user=None):
    st.subheader("🎨 Automated Storybook & YouTube Thumbnail Studio")
    st.write("Nano Banana, Hugging Face aur Pollinations automation pipeline ke zariye images generate karein:")

    gemini_active = bool(get_gemini_client())
    hf_active = bool(get_hf_api_key())
    
    st.caption(f"🤖 Nano Banana Status: {'✅ Active' if gemini_active else '⚠️ Inactive'}")
    st.caption(f"🧠 Hugging Face Status: {'✅ Active' if hf_active else '⚠️ Inactive (Optional)'}")
    st.caption("🆓 Pollinations Status: ✅ Always Available (Watermark Free)")

    img_prompt = st.text_area("✨ Prompt Box (मुख्य विवरण):", placeholder="90s Studio Ghibli style anime scene...")
    neg_prompt = st.text_area("🚫 Negative Prompt:", value="blurry, distorted face, low quality, bad anatomy, watermark, logo")

    col1, col2, col3 = st.columns(3)
    with col1:
        ratio_option = st.selectbox("📐 Aspect Ratio", ["Landscape (16:9)", "Portrait (9:16)", "Square (1:1)"])
        if "16:9" in ratio_option:
            w, h, ar_str = 1024, 576, "16:9"
        elif "9:16" in ratio_option:
            w, h, ar_str = 576, 1024, "9:16"
        else:
            w, h, ar_str = 768, 768, "1:1"
    with col2:
        style_option = st.selectbox("🎭 Style", ["Storybook Illustration", "2D Animation", "Cinematic", "Ghibli Anime"])
    with col3:
        num_images = st.slider("🔢 Number of Images", 1, 4, 1)

    if st.button("🚀 Start Automated Generation 🎬", type="primary", use_container_width=True):
        if not img_prompt.strip():
            st.warning("⚠️ कृपया प्रॉम्प्ट दर्ज करें!")
            return

        with st.spinner("🔄 Automation pipeline active hai... Images generate ho rahi hain..."):
            final_prompt = f"{img_prompt.strip()}, {style_option} style, high resolution, masterpiece"
            
            generated_images = []
            for i in range(num_images):
                img_bytes = None
                used_provider = None
                err_log = []

                # Step 1: Try Nano Banana (Gemini)
                if gemini_active and not img_bytes:
                    b, err = generate_with_nano_banana(get_gemini_client(), final_prompt, ar_str)
                    if b:
                        img_bytes = b
                        used_provider = "Nano Banana (Gemini)"
                    else:
                        err_log.append(f"Nano: {err}")

                # Step 2: Try Hugging Face if Step 1 failed
                if hf_active and not img_bytes:
                    b, err = generate_with_huggingface(final_prompt, neg_prompt, HF_MODEL_OPTIONS["⚡ Fast (FLUX.1-schnell)"], w, h)
                    if b:
                        img_bytes = b
                        used_provider = "Hugging Face (FLUX)"
                    else:
                        err_log.append(f"HF: {err}")

                # Step 3: Ultimate Fallback to Pollinations (Watermark Free)
                if not img_bytes:
                    seed_val = int(time.time()) + i
                    url = build_pollinations_url(final_prompt, neg_prompt, w, h, seed_val)
                    try:
                        resp = requests.get(url, timeout=60)
                        if resp.status_code == 200 and len(resp.content) > 1000:
                            img_bytes = resp.content
                            used_provider = "Pollinations (Watermark Free)"
                    except Exception as e:
                        err_log.append(f"Pollinations: {str(e)}")

                generated_images.append({"bytes": img_bytes, "provider": used_provider, "errors": err_log})

            success_count = sum(1 for item in generated_images if item["bytes"] is not None)
            if success_count > 0:
                st.success(f"✨ Safaltapoorvak {success_count}/{num_images} images generate ho gayi hain!")
                cols = st.columns(min(num_images, 2))
                for idx, item in enumerate(generated_images):
                    with cols[idx % len(cols)]:
                        if item["bytes"]:
                            st.image(item["bytes"], caption=f"#{idx+1} | Provider: {item['provider']}", use_container_width=True)
                            st.download_button(
                                label=f"📥 Download #{idx+1}",
                                data=item["bytes"],
                                file_name=f"auto_story_image_{idx+1}.png",
                                mime="image/png",
                                key=f"dl_auto_{idx}_{datetime.now().microsecond}"
                            )
                        else:
                            st.error(f"Image #{idx+1} fail ho gayi.")
                            with st.expander("Debug Errors"):
                                st.write(item["errors"])
            else:
                st.error("🚨 Sabhi providers fail ho gaye. Kripya apna internet connection ya prompt check karein.")
