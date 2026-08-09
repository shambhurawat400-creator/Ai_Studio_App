"""
AI Character Video Generator (Pro Version — Hugging Face Wan2.2)
--------------------------------------------------------------------
- Real generation via Hugging Face's free Inference Providers (Wan2.2-TI2V-5B),
  no dummy/placeholder video.
- No fully-free unlimited video provider exists (video is far more
  compute-heavy than images) — this uses the same HF_API_KEY/credits as
  the image studio, so it will fail once monthly HF credits run out.
  That's a real limit, not a bug; the error message says so clearly.
- Honest limitation: true photo-to-video (animating the exact uploaded
  face) isn't reliably available on free providers yet. The uploaded
  photo is used only as descriptive context in the prompt, not as a
  pixel-accurate animation source. This is explained in the UI.
"""

import logging
import time

import streamlit as st

logger = logging.getLogger(__name__)

VIDEO_MODEL_ID = "Wan-AI/Wan2.2-TI2V-5B"


def get_hf_api_key() -> str:
    import os
    key = os.environ.get("HF_API_KEY", "")
    if not key:
        try:
            key = st.secrets.get("HF_API_KEY", "")
        except Exception:
            pass
    return key


def generate_video_with_huggingface(prompt: str, max_retries: int = 1):
    """Returns (video_bytes_or_None, error_message_or_None)."""
    hf_key = get_hf_api_key()
    if not hf_key:
        return None, "HF_API_KEY set nahi hai."

    try:
        from huggingface_hub import InferenceClient
    except ImportError:
        return None, "huggingface_hub package installed nahi hai (requirements.txt check karo)."

    last_error = None
    for attempt in range(max_retries):
        try:
            client = InferenceClient(provider="auto", api_key=hf_key)
            video_bytes = client.text_to_video(prompt, model=VIDEO_MODEL_ID)
            if video_bytes and len(video_bytes) > 1000:
                return video_bytes, None
            last_error = "Response mila lekin video data khali tha."
        except Exception as e:
            last_error = f"{type(e).__name__}: {e}"
            if "402" in str(e) or "credit" in str(e).lower():
                last_error += " — HF ki monthly free credits khatam ho gayi hain (video generation images se zyada credits leta hai). Agle mahine reset hongi, ya billing add karo HF settings mein."
            elif "gated" in str(e).lower() or "403" in str(e):
                last_error += " — is model ka license accept karna hoga huggingface.co par."
            logger.warning("HF video attempt failed: %s", last_error)
            time.sleep(3)

    return None, last_error


def render_video_page(supabase=None, user=None):
    st.subheader("🎬 AI Character Video Generator")
    st.write("Prompt se real animated video banao — Hugging Face ke free (credit-based) Wan2.2 model se:")

    hf_available = bool(get_hf_api_key())
    if hf_available:
        st.caption("✅ Hugging Face (Wan2.2) active — same HF credits jo image generation use karta hai.")
    else:
        st.warning("⚠️ HF_API_KEY set nahi hai. Settings/secrets mein daalo pehle.")

    uploaded_img = st.file_uploader("1️⃣ फोटो अपलोड करें (सिर्फ reference/context के लिए):", type=["jpg", "png", "jpeg"])
    if uploaded_img:
        st.caption("ℹ️ Ye photo video mein exactly animate nahi hogi — free providers abhi pixel-accurate photo-to-video reliably support nahi karte. Photo sirf tumhare reference ke liye hai; niche description mein jitna zyada detail doge (chehra, kapde, umar), utna behtar match milega.")
        st.image(uploaded_img, width=200)

    character_dialogue = st.text_area("💬 डायलॉग / सीन विवरण:", placeholder="जैसे: रुको राहुल! उस कुएं के पास मत जाओ...")
    motion_prompt = st.text_area("🏃 बॉडी मूवमेंट और VFX विवरण:", placeholder="Slow camera zoom in, dark horror atmosphere, blowing wind")

    col1, col2 = st.columns(2)
    with col1:
        voice_style = st.selectbox("🎙️ माहौल/टोन:", ["Old Woman (बूढ़ी औरत)", "Young Man (युवक)", "Horror Ghost (भूतिया)", "Story Narrator"])
    with col2:
        motion_speed = st.selectbox("⚡ मूवमेंट स्पीड:", ["Smooth & Cinematic", "Fast & Dynamic", "Slow Motion"])

    if st.button("Generate Video 🎥🚀", type="primary", use_container_width=True):
        if not (character_dialogue.strip() or motion_prompt.strip()):
            st.warning("⚠️ कृपया कम से कम dialogue/scene ya motion description likho!")
            return
        if not hf_available:
            st.error("🚨 HF_API_KEY set nahi hai, video generate nahi ho sakta.")
            return

        speed_tags = {
            "Smooth & Cinematic": "smooth cinematic camera movement",
            "Fast & Dynamic": "fast dynamic energetic movement",
            "Slow Motion": "slow motion dramatic movement",
        }[motion_speed]

        prompt_parts = []
        if character_dialogue.strip():
            prompt_parts.append(character_dialogue.strip())
        if motion_prompt.strip():
            prompt_parts.append(motion_prompt.strip())
        prompt_parts.append(speed_tags)
        prompt_parts.append(f"mood: {voice_style}")
        final_prompt = ", ".join(prompt_parts)

        with st.spinner("🎬 Video generate ho raha hai... (isme 1-3 minute lag sakte hain, video generation image se dheema hota hai)"):
            video_bytes, err_msg = generate_video_with_huggingface(final_prompt)

            if video_bytes:
                st.success("🎉 Video safaltapoorvak taiyaar hai!")
                st.video(video_bytes)
                st.download_button(
                    label="📥 Download Video",
                    data=video_bytes,
                    file_name="generated_video.mp4",
                    mime="video/mp4",
                )
            else:
                st.error("🚨 Video generate nahi ho paya.")
                if err_msg:
                    with st.expander("❌ Error Details"):
                        st.code(err_msg)
