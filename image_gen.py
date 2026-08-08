"""
Free Pro Storybook Studio (Pro Version)
------------------------------------------
Production-hardened rewrite:
- Character Profile Manager for visual consistency across generations
  (description auto-injected into every prompt + deterministic seed
  derived from the character name)
- Fixed buggy seed/key handling for saved images
- Higher quality tiers with sane max-resolution caps
- Image load verification with graceful fallback
- use_container_width instead of deprecated use_column_width
"""

import hashlib
import time
import urllib.parse
from datetime import datetime

import requests
import streamlit as st

MAX_DIMENSION = 2048  # safety cap so we never request an absurd/failing size


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def stable_seed_from_name(name: str, salt: int = 0) -> int:
    """
    Deterministic seed derived from a character name (+ optional salt for
    slight variation between shots of the same character). Using a hash
    instead of a random/microsecond value means every image generated for
    this character starts from the same point, which is the closest a
    prompt-only free model can get to visual consistency.
    """
    digest = hashlib.sha256(f"{name}-{salt}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 1_000_000


def build_image_url(prompt: str, neg_prompt: str, width: int, height: int, seed: int) -> str:
    encoded_prompt = urllib.parse.quote(prompt)
    encoded_neg = urllib.parse.quote(neg_prompt)
    return (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?width={width}&height={height}&seed={seed}&model=flux&nologo=true&negative={encoded_neg}"
    )


def image_url_is_reachable(url: str, timeout: float = 8.0) -> bool:
    try:
        resp = requests.head(url, timeout=timeout, allow_redirects=True)
        if resp.status_code == 405:  # some servers don't support HEAD; fall back to GET
            resp = requests.get(url, timeout=timeout, stream=True)
        return resp.status_code == 200
    except requests.RequestException:
        return False


# ---------------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------------

def render_image_page():
    st.subheader("🎨 Free Pro Storybook Studio")
    st.write("बिना किसी खर्च के शानदार क्वालिटी, साफ़ चेहरों और **consistent characters** वाली इमेज बनाएं:")

    if "image_history" not in st.session_state:
        st.session_state.image_history = []
    if "saved_projects" not in st.session_state:
        st.session_state.saved_projects = []
    if "characters" not in st.session_state:
        st.session_state.characters = []  # list of {"name": str, "description": str}

    # --- Character Profile Manager ---
    with st.expander("🎭 Character Profile Manager (Consistency के लिए)", expanded=False):
        st.write("एक बार कैरेक्टर की पूरी बनावट (चेहरा, बाल, कपड़े, उम्र, खास पहचान) describe करो — हर image में वही description अपने-आप जुड़ेगा:")
        char_name = st.text_input("कैरेक्टर का नाम:", placeholder="जैसे: Grandma Kamla")
        char_desc = st.text_area(
            "कैरेक्टर का पूरा विवरण (जितना detailed, उतना consistent result):",
            placeholder="60 year old Indian woman, curly grey hair tied in a bun, wrinkled kind face, wearing a faded pink saree, round glasses, gentle smile",
            height=90,
        )
        if st.button("💾 Save Character"):
            if char_name.strip() and char_desc.strip():
                existing_names = [c["name"] for c in st.session_state.characters]
                if char_name.strip() in existing_names:
                    st.warning("⚠️ इस नाम का कैरेक्टर पहले से मौजूद है — अलग नाम चुनें।")
                else:
                    st.session_state.characters.append({"name": char_name.strip(), "description": char_desc.strip()})
                    st.success(f"🎉 '{char_name}' कैरेक्टर सेव हो गया!")
            else:
                st.warning("⚠️ कृपया नाम और विवरण दोनों भरें!")

        if st.session_state.characters:
            st.markdown("**सेव किए गए कैरेक्टर्स:**")
            for c in st.session_state.characters:
                st.text(f"• {c['name']} — {c['description'][:70]}{'...' if len(c['description']) > 70 else ''}")

    st.markdown("---")

    # --- Prompt inputs ---
    img_prompt = st.text_area(
        "✨ Prompt Box (मुख्य विवरण):",
        placeholder="An old grandmother crying, a sad man reading a letter, village room, detailed faces...",
    )

    character_names = ["— कोई नहीं (No Character) —"] + [c["name"] for c in st.session_state.characters]
    selected_character_name = st.selectbox("🎭 Character चुनें (Consistency के लिए):", character_names)

    neg_prompt = st.text_area(
        "🚫 Negative Prompt (जो चीज़ें इमेज में नहीं चाहिए):",
        value="blurry, distorted face, low quality, bad anatomy, dark shadows, ugly, extra limbs, deformed hands",
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
        if "16:9" in ratio_option:
            base_width, base_height = 1280, 720
        elif "9:16" in ratio_option:
            base_width, base_height = 720, 1280
        else:
            base_width, base_height = 1024, 1024

    with col2:
        quality_mode = st.selectbox("⚡ Quality Mode", ["Standard", "HD Quality", "Ultra HD Quality"])
        quality_multiplier = {"Standard": 1.0, "HD Quality": 1.3, "Ultra HD Quality": 1.6}[quality_mode]
        width = min(int(base_width * quality_multiplier), MAX_DIMENSION)
        height = min(int(base_height * quality_multiplier), MAX_DIMENSION)

    with col3:
        num_images = st.slider("🔢 Number of Images", 1, 4, 1)

    if st.button("🚀 Generate Free Images Now", type="primary", use_container_width=True):
        if not img_prompt.strip():
            st.warning("⚠️ कृपया पहले प्रॉम्प्ट बॉक्स में इमेज का विवरण (Prompt) दर्ज करें!")
            return

        progress_text = "✨ AI फ्री मॉडल से बेहतरीन क्वालिटी तैयार कर रहा है..."
        my_bar = st.progress(0, text=progress_text)
        for percent_complete in range(100):
            time.sleep(0.008)
            my_bar.progress(percent_complete + 1, text=f"{progress_text} ({percent_complete + 1}%)")
        my_bar.empty()

        with st.spinner("🖼️ इमेज लोड हो रही है..."):
            free_boost = "extremely detailed faces, sharp focus, clean lines, vibrant colors, masterpiece, 8k resolution"

            style_tags_map = {
                "Indian Storybook Illustration (बेस्ट)": f"classic Indian storybook vector illustration, beautifully drawn characters and room background, {free_boost}",
                "2D Animation / Cartoon": f"professional 2d animation cell, clean outlines, vibrant clear lighting, {free_boost}",
                "Cinematic Story Frame": f"cinematic story frame, warm ambient lighting, highly detailed background, {free_boost}",
                "Classic Oil Painting": f"classic oil painting on canvas, rich textured brushwork, masterpiece, {free_boost}",
                "Watercolor Art": f"soft watercolor painting style, artistic brush strokes, clear background, {free_boost}",
            }
            current_style_tag = style_tags_map.get(style_option, free_boost)

            # Inject character description for consistency, if selected
            character_desc = ""
            if selected_character_name != "— कोई नहीं (No Character) —":
                character_desc = next(
                    (c["description"] for c in st.session_state.characters if c["name"] == selected_character_name),
                    "",
                )

            clean_input = img_prompt.strip()
            prompt_parts = [clean_input]
            if character_desc:
                prompt_parts.append(f"character appearance: {character_desc}")
            prompt_parts.append(current_style_tag)
            final_prompt = ", ".join(prompt_parts)

            final_neg = neg_prompt.strip() if neg_prompt.strip() else "blurry, low quality"

            generated = []  # list of {"url": str, "seed": int}
            for i in range(num_images):
                if character_desc:
                    # Deterministic seed tied to the character name -> consistent look
                    # across every image generated for this character, with a small
                    # per-shot offset so multiple images aren't pixel-identical.
                    seed_val = stable_seed_from_name(selected_character_name, salt=i)
                else:
                    seed_val = datetime.now().microsecond + i

                url = build_image_url(final_prompt, final_neg, width, height, seed_val)
                generated.append({"url": url, "seed": seed_val})

            st.success(f"✨ शानदार क्वालिटी की {num_images} इमेज तैयार हैं!")

            cols = st.columns(min(num_images, 2))
            for idx, item in enumerate(generated):
                url, seed_val = item["url"], item["seed"]
                with cols[idx % len(cols)]:
                    if image_url_is_reachable(url):
                        st.image(url, caption=f"Style: {style_option} | #{idx + 1}", use_container_width=True)
                    else:
                        st.warning(f"⚠️ Image #{idx + 1} load नहीं हो पाई (server busy/timeout). Link try karo:")
                    st.markdown(f"[📥 Download / Open Image {idx + 1}]({url})")

                    if st.button(f"💾 Save Project #{idx + 1}", key=f"save_{seed_val}_{idx}"):
                        project_data = {
                            "prompt": img_prompt,
                            "character": selected_character_name,
                            "style": style_option,
                            "url": url,
                        }
                        if project_data not in st.session_state.saved_projects:
                            st.session_state.saved_projects.append(project_data)
                            st.success("📁 प्रोजेक्ट सफलतापूर्वक सेव हो गया!")

            st.session_state.image_history.insert(0, {
                "prompt": img_prompt,
                "character": selected_character_name,
                "style": style_option,
                "url": generated[0]["url"],
            })

    st.markdown("---")
    tab1, tab2 = st.tabs(["📂 Saved Projects", "📜 Generation History"])

    with tab1:
        st.subheader("आपके सेव किए गए प्रोजेक्ट्स")
        if st.session_state.saved_projects:
            for p_idx, proj in enumerate(st.session_state.saved_projects):
                char_label = proj.get("character", "—")
                st.write(f"**{p_idx + 1}. Style:** {proj['style']} | **Character:** {char_label} | **Prompt:** {proj['prompt']}")
                st.image(proj["url"], width=300)
                st.markdown(f"[🔗 Direct Link]({proj['url']})")
                st.write("---")
        else:
            st.info("कोई प्रोजेक्ट सेव नहीं है।")

    with tab2:
        st.subheader("पिछली जनरेट की गई इमेजेस (History)")
        if st.session_state.image_history:
            for h_idx, hist in enumerate(st.session_state.image_history[:5]):
                char_label = hist.get("character", "—")
                st.write(f"**Style:** {hist['style']} | **Character:** {char_label} | **Prompt:** {hist['prompt']}")
                st.image(hist["url"], width=250)
                st.write("---")
        else:
            st.info("इतिहास (History) खाली है।")
