"""
Free Pro Storybook Studio (Pro Version 3 — Nano Banana + Hugging Face + Pollinations)
--------------------------------------------------------------------------------------
Three image providers, best-to-worst:
  1. Nano Banana (Gemini 2.5 Flash Image) — ChatGPT/Midjourney-tier quality.
     Free-tier gated to a daily limit for non-Pro users (see billing_pro.py).
  2. Hugging Face Inference API (FLUX.1-schnell) — close to Nano Banana
     quality, free with a personal HF token, no daily cap from our side.
  3. Pollinations — always-available, no key needed, lowest quality, used
     as the final fallback so the app never fails to produce something.

No API keys are hardcoded anywhere — both Gemini and Hugging Face keys are
read only from st.secrets / environment variables.
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

try:
    from billing_pro import is_pro_user, check_and_consume_usage, FREE_NANO_BANANA_DAILY_LIMIT
except ImportError:
    is_pro_user = None
    check_and_consume_usage = None
    FREE_NANO_BANANA_DAILY_LIMIT = 3

logger = logging.getLogger(__name__)

NANO_BANANA_MODEL_CANDIDATES = ["gemini-2.5-flash-image", "gemini-2.5-flash-image-preview"]
HF_MODEL_OPTIONS = {
    "⚡ Fast (FLUX.1-schnell)": "black-forest-labs/FLUX.1-schnell",
    "💎 Best Quality (FLUX.1-dev — thoda slow)": "black-forest-labs/FLUX.1-dev",
}
HF_MODEL_ID = HF_MODEL_OPTIONS["⚡ Fast (FLUX.1-schnell)"]  # default
MAX_DIMENSION = 2048


# ---------------------------------------------------------------------------
# Nano Banana (Gemini) client
# ---------------------------------------------------------------------------

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
    """Returns (image_bytes_or_None, error_message_or_None)."""
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
# Hugging Face Inference API (FLUX)
# ---------------------------------------------------------------------------

def get_hf_api_key() -> str:
    key = os.environ.get("HF_API_KEY", "")
    if not key:
        try:
            key = st.secrets.get("HF_API_KEY", "")
        except Exception:
            pass
    return key


def generate_with_huggingface(prompt: str, negative_prompt: str, model_id: str, width: int, height: int, max_retries: int = 2):
    """
    Returns (image_bytes_or_None, error_message_or_None, model_actually_used_or_None).
    Uses the official huggingface_hub client (handles HF's Inference
    Providers routing/auth correctly — raw REST calls to the old
    api-inference.huggingface.co endpoint no longer work).
    If the requested model is gated/inaccessible, automatically falls back
    to FLUX.1-schnell (ungated) so the user doesn't hit a hard failure.
    """
    hf_key = get_hf_api_key()
    if not hf_key:
        return None, "HF_API_KEY set nahi hai.", None

    try:
        from huggingface_hub import InferenceClient
    except ImportError:
        return None, "huggingface_hub package installed nahi hai (requirements.txt check karo).", None

    models_to_try = [model_id]
    fallback_id = HF_MODEL_OPTIONS["⚡ Fast (FLUX.1-schnell)"]
    if model_id != fallback_id:
        models_to_try.append(fallback_id)

    last_error = None
    for try_model in models_to_try:
        is_dev_model = "dev" in try_model.lower()
        kwargs_full = {
            "negative_prompt": negative_prompt,
            "width": min(width, 1536),
            "height": min(height, 1536),
        }
        if is_dev_model:
            kwargs_full["num_inference_steps"] = 30
            kwargs_full["guidance_scale"] = 3.5
        else:
            kwargs_full["num_inference_steps"] = 4

        for attempt in range(max_retries):
            try:
                client = InferenceClient(provider="auto", api_key=hf_key)
                try:
                    pil_image = client.text_to_image(prompt, model=try_model, **kwargs_full)
                except TypeError:
                    pil_image = client.text_to_image(prompt, model=try_model)
                buf = BytesIO()
                pil_image.save(buf, format="PNG")
                data = buf.getvalue()
                if len(data) > 1000:
                    return data, None, try_model
                last_error = "Response mila lekin image data khali tha."
            except Exception as e:
                last_error = f"[{try_model}] {type(e).__name__}: {e}"
                is_access_error = any(s in str(e).lower() for s in ["gated", "403", "not authorized", "access"])
                logger.warning("HF attempt failed: %s", last_error)
                if is_access_error:
                    break  # don't retry the same gated model, move to fallback model immediately
                time.sleep(3)

    return None, last_error, None


# ---------------------------------------------------------------------------
# Pollinations fallback (always free, no key)
# ---------------------------------------------------------------------------

def stable_seed_from_name(name: str, salt: int = 0) -> int:
    digest = hashlib.sha256(f"{name}-{salt}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 1_000_000


def build_pollinations_url(prompt: str, neg_prompt: str, width: int, height: int, seed: int) -> str:
    # Note: `prompt` already includes style/quality tags from the caller — don't add more here,
    # since a bloated prompt dilutes attention on the specific scene (characters, count, setting)
    # and free models like this one have weaker prompt adherence to begin with.
    encoded_prompt = urllib.parse.quote(prompt)
    encoded_neg = urllib.parse.quote(neg_prompt)
    boosted_width = min(int(width * 1.15), MAX_DIMENSION)
    boosted_height = min(int(height * 1.15), MAX_DIMENSION)
    return (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?width={boosted_width}&height={boosted_height}&seed={seed}&model=flux&nologo=true&negative={encoded_neg}"
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

PROVIDER_AUTO = "🤖 Auto (Nano Banana → Hugging Face → Pollinations)"
PROVIDER_NANO = "✨ सिर्फ Nano Banana (high quality)"
PROVIDER_HF = "🧠 सिर्फ Hugging Face (FLUX)"
PROVIDER_POLLINATIONS = "🆓 सिर्फ Pollinations (unlimited, free)"


def render_image_page(supabase=None, user=None):
    st.subheader("🎨 Free Pro Storybook Studio")
    st.write("Nano Banana, Hugging Face (FLUX) aur Pollinations ke saath — jo bhi best available ho, wahi use hoga:")

    gemini_client = get_gemini_client()
    hf_available = bool(get_hf_api_key())
    user_is_pro = bool(supabase and user and is_pro_user and is_pro_user(supabase, user))

    status_bits = []
    if gemini_client:
        limit_note = "unlimited (Pro)" if user_is_pro else f"{FREE_NANO_BANANA_DAILY_LIMIT}/din (Free)"
        status_bits.append(f"✅ Nano Banana active — {limit_note}")
    else:
        status_bits.append("⚠️ Nano Banana off (GEMINI_API_KEY set nahi hai)")
    status_bits.append("✅ Hugging Face active" if hf_available else "⚠️ Hugging Face off (HF_API_KEY set nahi hai)")
    status_bits.append("✅ Pollinations always available")
    for bit in status_bits:
        st.caption(bit)

    provider_choice = st.radio(
        "🔀 Image Provider चुनो:",
        [PROVIDER_AUTO, PROVIDER_NANO, PROVIDER_HF, PROVIDER_POLLINATIONS],
        horizontal=False,
    )

    hf_model_choice = HF_MODEL_OPTIONS["⚡ Fast (FLUX.1-schnell)"]
    if provider_choice in (PROVIDER_AUTO, PROVIDER_HF) and hf_available:
        hf_quality_label = st.selectbox(
            "🧠 Hugging Face Quality:", list(HF_MODEL_OPTIONS.keys()),
            index=1, help="Best Quality (dev) prompts ko zyada sahi follow karta hai, khaas kar multiple characters wali scenes mein.",
        )
        hf_model_choice = HF_MODEL_OPTIONS[hf_quality_label]
        if "dev" in hf_model_choice.lower():
            st.caption("⚠️ FLUX.1-dev gated hai — pehli baar use karne se pehle [model page](https://huggingface.co/black-forest-labs/FLUX.1-dev) पर jaake license ek baar accept karna hoga.")

    if "image_history" not in st.session_state:
        st.session_state.image_history = []
    if "saved_projects" not in st.session_state:
        st.session_state.saved_projects = []
    if "characters" not in st.session_state:
        st.session_state.characters = []

    # --- Character Profile Manager ---
    with st.expander("🎭 Character Profile Manager (Consistency के लिए)", expanded=False):
        st.write("Pehli image apne-aap reference ban jaayegi (Nano Banana ke liye) — future images usi look ko follow karengi:")
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

        if st.session_state.characters:
            st.markdown("**सेव किए गए कैरेक्टर्स:**")
            for c in st.session_state.characters:
                ref_status = "🖼️ reference set" if c.get("reference_image") else "— अभी तक reference नहीं"
                st.text(f"• {c['name']} — {ref_status}")

    st.markdown("---")

    img_prompt = st.text_area(
        "✨ Prompt Box (मुख्य विवरण):",
        placeholder="An old grandmother crying, a sad man reading a letter, village room, detailed faces...",
    )

    character_names = ["— कोई नहीं (No Character) —"] + [c["name"] for c in st.session_state.characters]
    selected_character_name = st.selectbox("🎭 Character चुनें (Consistency के लिए):", character_names)

    neg_prompt = st.text_area(
        "🚫 Negative Prompt (चेहरा, आँखें और बैकग्राउंड साफ़ रखने के लिए):",
        value="blurry, distorted face, asymmetrical face, low quality, bad anatomy, dark shadows, ugly, extra limbs, deformed hands, extra fingers, out of focus background, grainy, watermark, text, oversaturated, back view, from behind, faces hidden, looking away, silhouette",
    )
    st.caption("💡 Tip 1: 'four teenage boys' jaisa count likhna naamon (Rahul, Sonu...) se zyada reliably सही number of log dikhayega.")
    st.caption("💡 Tip 2: Hugging Face mein complex/multi-character scenes ke liye 'Best Quality (FLUX.1-dev)' chuno — 'Fast (schnell)' speed ke liye bana hai, detailed instructions utni achhi tarah follow nahi karta.")

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

        with st.spinner("🖼️ इमेज बन रही है... (कृपया प्रतीक्षा करें, HD/Ultra HD mein zyada time lag sakta hai)"):
            free_boost = "sharp detailed faces, clean background, vibrant colors, high quality"
            style_tags_map = {
                "Indian Storybook Illustration (बेस्ट)": f"Indian storybook illustration style, {free_boost}",
                "2D Animation / Cartoon": f"2d animation cartoon style, clean outlines, {free_boost}",
                "Cinematic Story Frame": f"cinematic frame, warm ambient lighting, {free_boost}",
                "Classic Oil Painting": f"oil painting style, textured brushwork, {free_boost}",
                "Watercolor Art": f"watercolor painting style, soft brush strokes, {free_boost}",
            }
            current_style_tag = style_tags_map.get(style_option, free_boost)

            character = None
            if selected_character_name != "— कोई नहीं (No Character) —":
                character = next((c for c in st.session_state.characters if c["name"] == selected_character_name), None)

            clean_input = img_prompt.strip()
            prompt_parts = ["Front-facing camera shot, all characters facing toward the viewer with clearly visible faces (not walking away, not a back view, not a silhouette)", clean_input]
            if character:
                prompt_parts.append(f"the main character must match this description exactly: {character['description']}")
                if character.get("reference_image"):
                    prompt_parts.append("keep the character's face, hairstyle and outfit consistent with the provided reference image")
            prompt_parts.append(f"aspect ratio {aspect_ratio_str}")
            prompt_parts.append(current_style_tag)
            final_prompt = ", ".join(prompt_parts)
            final_neg = neg_prompt.strip() if neg_prompt.strip() else "blurry, low quality"

            # Which providers are allowed to be tried, in priority order, based on the radio choice
            if provider_choice == PROVIDER_AUTO:
                try_order = ["nano_banana", "huggingface", "pollinations"]
            elif provider_choice == PROVIDER_NANO:
                try_order = ["nano_banana"]
            elif provider_choice == PROVIDER_HF:
                try_order = ["huggingface"]
            else:
                try_order = ["pollinations"]

            generated = []

            for i in range(num_images):
                img_bytes = None
                provider = None
                url = None
                err_msg = None

                for step in try_order:
                    if img_bytes:
                        break

                    if step == "nano_banana":
                        if not gemini_client:
                            continue
                        if not user_is_pro and supabase and user and check_and_consume_usage:
                            allowed, _ = check_and_consume_usage(supabase, user.id, "nano_banana", FREE_NANO_BANANA_DAILY_LIMIT)
                            if not allowed:
                                err_msg = f"Free plan ki daily limit ({FREE_NANO_BANANA_DAILY_LIMIT} images) khatam ho gayi. Kal reset hogi, ya Upgrade to Pro se unlimited use karo."
                                continue
                        ref_bytes = character.get("reference_image") if character else None
                        img_bytes, err_msg = generate_with_nano_banana(gemini_client, final_prompt, aspect_ratio_str, ref_bytes)
                        if img_bytes:
                            provider = "Nano Banana"
                            if character and not character.get("reference_image"):
                                character["reference_image"] = img_bytes

                    elif step == "huggingface":
                        img_bytes, err_msg, model_used = generate_with_huggingface(final_prompt, final_neg, hf_model_choice, fallback_width, fallback_height)
                        if img_bytes:
                            provider = "Hugging Face (FLUX)"
                            if model_used and "dev" not in model_used.lower() and "dev" in hf_model_choice.lower():
                                provider += " — schnell pe auto-fallback (dev accessible nahi tha)"

                    elif step == "pollinations":
                        seed_val = stable_seed_from_name(selected_character_name, salt=i) if character else datetime.now().microsecond + i
                        url = build_pollinations_url(final_prompt, final_neg, fallback_width, fallback_height, seed_val)
                        img_bytes = fetch_image_bytes(url)
                        if img_bytes:
                            provider = "Pollinations (Free)"

                generated.append({"bytes": img_bytes, "provider": provider, "url": url, "error": err_msg})

            success_count = sum(1 for g in generated if g["bytes"] is not None)
            if success_count == 0:
                st.error("🚨 कोई भी इमेज generate नहीं हो पाई। API keys check karo ya thodi der baad try karo.")
            else:
                st.success(f"✨ {success_count}/{num_images} इमेज तैयार हैं!")

            cols = st.columns(min(num_images, 2))
            for idx, item in enumerate(generated):
                img_bytes, provider, url, err_msg = item["bytes"], item["provider"], item["url"], item["error"]
                with cols[idx % len(cols)]:
                    if img_bytes:
                        caption = f"Style: {style_option} | #{idx + 1}"
                        if provider:
                            caption += f" | {provider}"
                        st.image(img_bytes, caption=caption, use_container_width=True)
                        h = short_hash(img_bytes)
                        st.download_button(
                            label=f"📥 Download Image {idx + 1}",
                            data=img_bytes,
                            file_name=f"storybook_image_{idx + 1}.png",
                            mime="image/png",
                            key=f"download_{idx}_{h}",
                        )
                        if st.button(f"💾 Save Project #{idx + 1}", key=f"save_{idx}_{h}"):
                            st.session_state.saved_projects.append({
                                "prompt": img_prompt,
                                "character": selected_character_name,
                                "style": style_option,
                                "image": img_bytes,
                            })
                            st.success("📁 प्रोजेक्ट सफलतापूर्वक सेव हो गया!")
                    else:
                        st.warning(f"⚠️ Image #{idx + 1} generate नहीं हो पाई।")
                        if err_msg:
                            with st.expander("❌ Error Details"):
                                st.code(err_msg)
                        if url:
                            st.markdown(f"[🔗 Direct link try karo]({url})")

            if success_count > 0:
                first_ok = next(g for g in generated if g["bytes"] is not None)
                st.session_state.image_history.insert(0, {
                    "prompt": img_prompt,
                    "character": selected_character_name,
                    "style": style_option,
                    "image": first_ok["bytes"],
                })

    st.markdown("---")
    tab1, tab2 = st.tabs(["📂 Saved Projects", "📜 Generation History"])

    with tab1:
        st.subheader("आपके सेव किए गए प्रोजेक्ट्स")
        if st.session_state.saved_projects:
            for p_idx, proj in enumerate(st.session_state.saved_projects):
                st.write(f"**{p_idx + 1}. Style:** {proj['style']} | **Character:** {proj.get('character', '—')} | **Prompt:** {proj['prompt']}")
                st.image(proj["image"], width=300)
                st.write("---")
        else:
            st.info("कोई प्रोजेक्ट सेव नहीं है।")

    with tab2:
        st.subheader("पिछली जनरेट की गई इमेजेस")
        if st.session_state.image_history:
            for h_idx, hist in enumerate(st.session_state.image_history[:5]):
                st.write(f"**Style:** {hist['style']} | **Character:** {hist.get('character', '—')} | **Prompt:** {hist['prompt']}")
                st.image(hist["image"], width=250)
                st.write("---")
        else:
            st.info("इतिहास (History) खाली है।")
