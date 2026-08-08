"""
Free Pro Storybook Studio (Pro Version 2 — Nano Banana & Hugging Face Edition)
------------------------------------------------------------------
- Primary image provider: Google Nano Banana (Gemini 2.5 Flash Image)
- Secondary/Fallback provider: Hugging Face Inference API / Pollinations (Enhanced Quality)
- Real character consistency integrated.
"""

import hashlib
import logging
import os
import time
import urllib.parse
from datetime import datetime
from io import BytesIO

import requests
import streamlit as st
from PIL import Image

logger = logging.getLogger(__name__)

NANO_BANANA_MODEL_CANDIDATES = ["gemini-2.5-flash-image", "gemini-2.5-flash-image-preview"]
MAX_DIMENSION = 2048  

# ---------------------------------------------------------------------------
# API Keys Configuration (यहाँ अपनी Hugging Face और Gemini की API Key सेट करें)
# ---------------------------------------------------------------------------
# अपनी Hugging Face की API Key यहाँ स्ट्रिंग में डालें या st.secrets का उपयोग करें:
HUGGING_FACE_API_KEY = "YAHAN_APNI_HUGGING_FACE_API_KEY_DAALEIN"


# ---------------------------------------------------------------------------
# Nano Banana (Gemini) client Integration
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def get_gemini_client():
    try:
        from google import genai
    except ImportError:
        return None

    api_key = "AQ.Ab8RN6JtgZXZ2tJeH__RkR4dKJDmZal3w5HJdUo3DI1cuUobLA"
    
    if not api_key:
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
            logger.warning("Could not decode reference image, skipping it: %s", e)

    last_error = None
    for model_name in NANO_BANANA_MODEL_CANDIDATES:
        for use_config in (True, False):
            try:
                if use_config:
                    config = types.GenerateContentConfig(image_config=types.ImageConfig(aspect_ratio=aspect_ratio))
                    response = client.models.generate_content(model=model_name, contents=contents, config=config)
                else:
                    response = client.models.generate_content(model=model_name, contents=contents)

                for part in response.candidates[0].content.parts:
                    if getattr(part, "inline_data", None) is not None:
                        return part.inline_data.data, None
                last_error = f"[{model_name}] Response mila lekin usmein koi image data nahi tha."
            except Exception as e:
                last_error = f"[{model_name}] {type(e).__name__}: {e}"
                logger.warning("Nano Banana attempt failed: %s", last_error)

    return None, last_error


# ---------------------------------------------------------------------------
# Hugging Face Inference API Integration (Image/Video Generation)
# ---------------------------------------------------------------------------

def generate_with_huggingface(prompt: str, negative_prompt: str):
    """
    Hugging Face API के जरिए हाई-क्वालिटी इमेज जनरेट करने का फंक्शन।
    यहाँ Stable Diffusion XL या Flux मॉडल का उपयोग किया जा रहा है ताकि चेहरा और बैकग्राउंड साफ़ आएं।
    """
    global HUGGING_FACE_API_KEY
    if not HUGGING_FACE_API_KEY or HUGGING_FACE_API_KEY == "YAHAN_APNI_HUGGING_FACE_API_KEY_DAALEIN":
        try:
            HUGGING_FACE_API_KEY = st.secrets.get("HF_API_KEY", "")
        except Exception:
            pass

    if not HUGGING_FACE_API_KEY:
        return None, "Hugging Face API Key missing."

    # बेहतरीन क्वालिटी वाले मॉडल का एंडपॉइंट (FLUX.1-schnell या SDXL)
    API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {HUGGING_FACE_API_KEY}"}
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "negative_prompt": negative_prompt,
            "num_inference_steps": 30
        }
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 200 and len(response.content) > 1000:
            return response.content, None
        else:
            return None, f"HF API Error Status: {response.status_code}, {response.text}"
    except Exception as e:
        return None, str(e)


# ---------------------------------------------------------------------------
# Enhanced Pollinations Fallback (ब्लर और फटे हुए चेहरों की समस्या दूर करने के लिए)
# ---------------------------------------------------------------------------

def stable_seed_from_name(name: str, salt: int = 0) -> int:
    digest = hashlib.sha256(f"{name}-{salt}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 1_000_000


def build_pollinations_url(prompt: str, neg_prompt: str, width: int, height: int, seed: int) -> str:
    # प्रॉम्प्ट को एन्हांस किया ताकि आँखें, चेहरे और बैकग्राउंड साफ़ आएं
    enhanced_prompt = f"{prompt}, highly detailed sharp focus, clear expressive face, detailed eyes, sharp background, masterpiece"
    encoded_prompt = urllib.parse.quote(enhanced_prompt)
    encoded_neg = urllib.parse.quote(neg_prompt)
    return (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?width={width}&height={height}&seed={seed}&model=flux&nologo=true&enhance=true&negative={encoded_neg}"
    )


def fetch_image_bytes(url: str, timeout: float = 90.0, max_retries: int = 2):
    last_error = None
    for _ in range(max_retries):
        try:
            resp = requests.get(url, timeout=timeout)
            if resp.status_code == 200 and resp.content and len(resp.content) > 1000:
                return resp.content
            last_error = f"status={resp.status_code}"
        except requests.RequestException as e:
            last_error = str(e)
        time.sleep(2)
    logger.warning("Pollinations fetch failed: %s", last_error)
    return None


def short_hash(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()[:10]


# ---------------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------------

def render_image_page():
    st.subheader("🎨 Free Pro Storybook Studio")
    st.write("Nano Banana, Hugging Face और Enhanced Quality के साथ शानदार इमेज बनाएं:")

    gemini_client = get_gemini_client()
    if gemini_client:
        st.caption("✅ Nano Banana (high quality) active")
    else:
        st.warning("⚠️ Gemini client initialize nahi ho paaya. Please check API key.")

    provider_choice = st.radio(
        "🔀 Image Provider चुनो:",
        [
            "🤖 Auto (Nano Banana -> Hugging Face -> Pollinations)",
            "✨ सिर्फ Nano Banana (high quality)",
            "🧠 सिर्फ Hugging Face API",
            "🆓 सिर्फ Enhanced Pollinations"
        ],
        horizontal=False,
    )

    if "image_history" not in st.session_state:
        st.session_state.image_history = []
    if "saved_projects" not in st.session_state:
        st.session_state.saved_projects = []
    if "characters" not in st.session_state:
        st.session_state.characters = []

    # --- Character Profile Manager ---
    with st.expander("🎭 Character Profile Manager (Consistency के लिए)", expanded=False):
        char_name = st.text_input("कैरेक्टर का नाम:", placeholder="जैसे: Grandma Kamla")
        char_desc = st.text_area(
            "कैरेक्टर का पूरा विवरण:",
            placeholder="60 year old Indian woman, curly grey hair, wrinkled kind face, faded pink saree, round glasses",
            height=90,
        )
        char_ref_upload = st.file_uploader("(Optional) खुद की reference image अपलोड करो:", type=["png", "jpg", "jpeg"])

        if st.button("💾 Save Character"):
            if char_name.strip() and char_desc.strip():
                existing_names = [c["name"] for c in st.session_state.characters]
                if char_name.strip() in existing_names:
                    st.warning("⚠️ इस नाम का कैरेक्टर पहले से मौजूद है।")
                else:
                    ref_bytes = char_ref_upload.getvalue() if char_ref_upload else None
                    st.session_state.characters.append({
                        "name": char_name.strip(),
                        "description": char_desc.strip(),
                        "reference_image": ref_bytes,
                    })
                    st.success(f"🎉 '{char_name}' कैरेक्टर सेव हो गया!")
            else:
                st.warning("⚠️ कृपया नाम और विवरण दोनों भरें!")

    st.markdown("---")

    img_prompt = st.text_area(
        "✨ Prompt Box (मुख्य विवरण):",
        placeholder="An old grandmother crying, a sad man reading a letter, village room, detailed faces...",
    )

    character_names = ["— कोई नहीं (No Character) —"] + [c["name"] for c in st.session_state.characters]
    selected_character_name = st.selectbox("🎭 Character चुनें (Consistency के लिए):", character_names)

    neg_prompt = st.text_area(
        "🚫 Negative Prompt (चेहरा, आँखें और बैकग्राउंड साफ़ रखने के लिए):",
        value="blurry, distorted face, low quality, bad anatomy, dark shadows, ugly, extra limbs, deformed hands, out of focus background",
    )

    st.markdown("### 🎭 Style Selection (शैलियों का चयन)")
    style_option = st.selectbox("चुनें अपना पसंदीदा आर्ट स्टाइल:", [
        "Indian Storybook Illustration (बेस्ट)",
        "2D Animation / Cartoon",
        "Cinematic Story Frame",
        "Classic Oil Painting",
        "Watercolor Art",
    ])

    col1, col2, col3 = st.columns(3)
    with col1:
        ratio_option = st.selectbox("📐 Aspect Ratio", ["Landscape (16:9)", "Portrait (9:16)", "Square (1:1)"])
        aspect_ratio_str = {"Landscape (16:9)": "16:9", "Portrait (9:16)": "9:16", "Square (1:1)": "1:1"}[ratio_option]
        if "16:9" in ratio_option:
            base_width, base_height = 1280, 720
        elif "9:16" in ratio_option:
            base_width, base_height = 720, 1280
        else:
            base_width, base_height = 1024, 1024

    with col2:
        quality_mode = st.selectbox("⚡ Quality Mode", ["Standard", "HD Quality", "Ultra HD Quality"])
        quality_multiplier = {"Standard": 1.0, "HD Quality": 1.3, "Ultra HD Quality": 1.6}[quality_mode]
        fallback_width = min(int(base_width * quality_multiplier), MAX_DIMENSION)
        fallback_height = min(int(base_height * quality_multiplier), MAX_DIMENSION)

    with col3:
        num_images = st.slider("🔢 Number of Images", 1, 4, 1)

    if st.button("🚀 Generate Images Now", type="primary", use_container_width=True):
        if not img_prompt.strip():
            st.warning("⚠️ कृपया पहले प्रॉम्प्ट बॉक्स में इमेज का विवरण (Prompt) दर्ज करें!")
            return

        with st.spinner("🖼️ इमेज बन रही है... (कृपया प्रतीक्षा करें)"):
            free_boost = "extremely detailed sharp faces, clear eyes, crisp background, vibrant colors, masterwork, ultra high resolution"
            style_tags_map = {
                "Indian Storybook Illustration (बेस्ट)": f"classic Indian storybook illustration, beautifully drawn characters and clear detailed room background, {free_boost}",
                "2D Animation / Cartoon": f"professional 2d animation cell, clean sharp outlines, vibrant lighting, {free_boost}",
                "Cinematic Story Frame": f"cinematic story frame, warm sharp ambient lighting, highly detailed background, {free_boost}",
                "Classic Oil Painting": f"classic oil painting on canvas, rich textured brushwork, masterpiece, {free_boost}",
                "Watercolor Art": f"soft watercolor painting style, artistic brush strokes, clear background, {free_boost}",
            }
            current_style_tag = style_tags_map.get(style_option, free_boost)

            character = None
            if selected_character_name != "— कोई नहीं (No Character) —":
                character = next((c for c in st.session_state.characters if c["name"] == selected_character_name), None)

            clean_input = img_prompt.strip()
            prompt_parts = [clean_input]
            if character:
                prompt_parts.append(f"the main character must match this description exactly: {character['description']}")
            prompt_parts.append(current_style_tag)
            final_prompt = ", ".join(prompt_parts)
            final_neg = neg_prompt.strip() if neg_prompt.strip() else "blurry, low quality"

            generated = []

            for i in range(num_images):
                img_bytes = None
                provider = None
                url = None
                err_msg = None

                use_nano_banana = gemini_client and "Nano Banana" in provider_choice
                use_hf = "Hugging Face" in provider_choice or "Auto" in provider_choice
                use_pollinations = "Pollinations" in provider_choice or "Auto" in provider_choice

                # 1. Try Nano Banana
                if use_nano_banana or "Auto" in provider_choice:
                    if gemini_client:
                        ref_bytes = character.get("reference_image") if character else None
                        img_bytes, err_msg = generate_with_nano_banana(gemini_client, final_prompt, aspect_ratio_str, ref_bytes)
                        if img_bytes:
                            provider = "Nano Banana"
                            if character and not character.get("reference_image"):
                                character["reference_image"] = img_bytes

                # 2. Try Hugging Face API if Nano Banana failed or chosen
                if not img_bytes and (use_hf or "Auto" in provider_choice):
                    img_bytes, err_msg = generate_with_huggingface(final_prompt, final_neg)
                    if img_bytes:
                        provider = "Hugging Face API"

                # 3. Fallback to Enhanced Pollinations if others failed
                if not img_bytes and (use_pollinations or "Auto" in provider_choice):
                    seed_val = stable_seed_from_name(selected_character_name, salt=i) if character else datetime.now().microsecond + i
                    url = build_pollinations_url(final_prompt, final_neg, fallback_width, fallback_height, seed_val)
                    img_bytes = fetch_image_bytes(url)
                    if img_bytes:
                        provider = "Enhanced Pollinations (Free)"

                generated.append({"bytes": img_bytes, "provider": provider, "url": url, "error": err_msg})

            success_count = sum(1 for g in generated if g["bytes"] is not None)
            if success_count == 0:
                st.error("🚨 कोई भी इमेज generate नहीं हो पाई। कृपया अपनी API Key जांचें या थोड़ी देर बाद प्रयास करें।")
            else:
                st.success(f"✨ {success_count}/{num_images} इमेज तैयार हैं!")

            cols = st.columns(min(num_images, 2))
            for idx, item in enumerate(generated):
                img_bytes, provider, url, err_msg = item["bytes"], item["provider"], item["url"], item["error"]
                with cols[idx % len(cols)]:
                    if img_bytes:
                        caption = f"Style: {style_option} | #{idx + 1} | {provider}"
                        st.image(img_bytes, caption=caption, use_container_width=True)
                        h = short_hash(img_bytes)
                        st.download_button(
                            label=f"📥 Download Image {idx + 1}",
                            data=img_bytes,
                            file_name=f"storybook_image_{idx + 1}.png",
                            mime="image/png",
                            key=f"download_{idx}_{h}",
                        )
                    else:
                        st.warning(f"⚠️ Image #{idx + 1} generate नहीं हो पाई।")
                        if err_msg:
                            with st.expander("❌ Error Details"):
                                st.code(err_msg)

    st.markdown("---")
    tab1, tab2 = st.tabs(["📂 Saved Projects", "📜 Generation History"])

    with tab1:
        st.subheader("आपके सेव किए गए प्रोजेक्ट्स")
        if st.session_state.saved_projects:
            for p_idx, proj in enumerate(st.session_state.saved_projects):
                st.write(f"**{p_idx + 1}. Style:** {proj['style']} | **Character:** {proj.get('character', '—')}")
                st.image(proj["image"], width=300)
        else:
            st.info("कोई प्रोजेक्ट सेव नहीं है।")

    with tab2:
        st.subheader("पिछली जनरेट की गई इमेजेस")
        if st.session_state.image_history:
            for h_idx, hist in enumerate(st.session_state.image_history[:5]):
                st.image(hist["image"], width=250)
        else:
            st.info("इतिहास (History) खाली है।")
