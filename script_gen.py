"""
AI Video & Story Script Writer & Chatbot Hub (Pro Version with Groq & GitHub Fallback)
------------------------------------------------------------------------------------
- Dual AI Providers: Primary Groq with automatic Fallback to GitHub Models API
- Cached clients (not rebuilt on every rerun)
- Strict instruction-following: system prompt + optional custom instructions
- Retry logic for transient API failures
- Sanitized filenames for downloads
- Chat history trimmed to avoid unbounded token growth
"""

import re
import time
import logging

import streamlit as st
from groq import Groq
from openai import OpenAI  # GitHub Models OpenAI compatible client ke liye

logger = logging.getLogger(__name__)

MODEL_NAME = "llama-3.1-8b-instant"
GITHUB_MODEL_NAME = "gpt-4o-mini"  # GitHub Models par available standard fast model
MAX_CHAT_HISTORY_MESSAGES = 20  # keep last N messages so context doesn't grow unbounded
MAX_RETRIES = 2


# ---------------------------------------------------------------------------
# Client setup (Groq & GitHub Fallback)
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def get_groq_client() -> Groq | None:
    """Build the Groq client once per session."""
    import os
    api_key = None
    try:
        api_key = st.secrets.get("GROQ_API_KEY")
    except Exception:
        pass
    if not api_key:
        api_key = os.environ.get("GROQ_API_KEY")

    if not api_key:
        return None

    try:
        return Groq(api_key=api_key)
    except Exception as e:
        logger.error("Failed to initialize Groq client: %s", e)
        return None


@st.cache_resource(show_spinner=False)
def get_github_client() -> OpenAI | None:
    """Build the GitHub Models client as a fallback option."""
    import os
    token = None
    try:
        token = st.secrets.get("GITHUB_TOKEN")
    except Exception:
        pass
    if not token:
        token = os.environ.get("GITHUB_TOKEN")

    if not token:
        return None

    try:
        # GitHub Models OpenAI-compatible endpoint use karta hai
        return OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=token
        )
    except Exception as e:
        logger.error("Failed to initialize GitHub client: %s", e)
        return None


def call_ai_with_fallback(groq_client, messages, max_tokens=4000, temperature=0.7):
    """
    Pehle Groq se call karne ki koshish karega. Agar Groq fail hota hai 
    ya limit khatam hoti hai, toh automatically GitHub Models API par switch ho jayega.
    """
    github_client = get_github_client()
    last_error = None

    # 1. Try Groq First
    if groq_client:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = groq_client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response, "Groq"
            except Exception as e:
                last_error = e
                logger.warning(f"Groq attempt {attempt} failed: {e}")
                time.sleep(1.0)

    # 2. Fallback to GitHub Models if Groq fails or unavailable
    if github_client:
        logger.info("Switching to GitHub Models API fallback...")
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = github_client.chat.completions.create(
                    model=GITHUB_MODEL_NAME,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response, "GitHub Models"
            except Exception as e:
                last_error = e
                logger.warning(f"GitHub fallback attempt {attempt} failed: {e}")
                time.sleep(1.0)

    # Agar dono fail ho jayein
    raise RuntimeError(f"All AI providers failed. Last error: {str(last_error)}")


def sanitize_filename(text: str) -> str:
    text = text.strip()[:40]
    return re.sub(r"[^\w\-]+", "_", text) or "script"


# ---------------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------------

def render_script_page(groq_client=None):
    st.subheader("📜 AI Video & Story Script Writer & Chatbot Hub")
    st.write("यहाँ से आप यूट्यूब, शॉर्ट्स या लंबी कहानियों के लिए स्क्रिप्ट तैयार कर सकते हैं और AI चैटबॉट से बात कर सकते हैं:")

    active_groq = groq_client or get_groq_client()
    github_client_check = get_github_client()

    if not active_groq and not github_client_check:
        st.error("🚨 ना तो GROQ_API_KEY सेट है और ना ही GITHUB_TOKEN! कृपया secrets.toml में कम से कम एक की ज़रूर सेट करें।")

    app_mode = st.radio("फीचर चुनें:", ["✍️ Pro Script Writer", "💬 AI Assistant Chatbot"], horizontal=True)

    if app_mode == "✍️ Pro Script Writer":
        _render_script_writer(active_groq)
    else:
        _render_chatbot(active_groq)


# ---------------------------------------------------------------------------
# Script Writer
# ---------------------------------------------------------------------------

def _build_system_prompt(script_type: str, tone_style: str, extra_instructions: str) -> str:
    base = (
        "You are a world-class professional scriptwriter. "
        "Follow the user's instructions with strict precision. "
        f"Format: {script_type}. Tone: {tone_style}. "
        "Include vivid visual & audio cues (e.g., [Camera Pan], [SFX: Heavy Wind], [Dark Lighting]). "
        "Write engaging dialogue and maintain strong narrative flow. "
        "Do NOT add content, themes, or characters that are not implied by the user's topic. "
        "Do NOT include meta-commentary, disclaimers, or notes about being an AI. "
        "Write entirely in rich, natural Hindi/Hinglish unless the user specifies another language."
    )
    if extra_instructions.strip():
        base += f"\n\nAdditional mandatory instructions from the user (follow these exactly, they override defaults if they conflict): {extra_instructions.strip()}"
    return base


def _render_script_writer(active_groq):
    topic = st.text_input(
        "स्क्रिप्ट का टॉपिक/विषय दर्ज करें:",
        placeholder="जैसे: Horror story near a haunted well in an ancient village",
    )

    col1, col2 = st.columns(2)
    with col1:
        script_type = st.selectbox("प्लेटफॉर्म/प्रकार:", [
            "YouTube Video (Full Cinematic Script)",
            "Instagram Reel / YouTube Shorts (Fast-Paced)",
            "Horror Story / Suspense Storytelling",
            "Motivational / Documentary Speech",
        ])
    with col2:
        tone_style = st.selectbox("टोन और अंदाज़ (Tone):", [
            "Suspense & Thrilling (रहस्यमयी और डरावना)",
            "Emotional & Dramatic (भावुक और गहरा)",
            "Energetic & Hype (जोशीला और रोमांचक)",
            "Informative & Engaging (दिल्चस्प और जानकारीपूर्ण)",
        ])

    length_option = st.selectbox("लंबाई और विस्तार (Length & Depth):", [
        "मध्यम स्क्रिप्ट (1000 - 2000 शब्द)",
        "लंबी कहानी / वीडियो (3000 - 5000 शब्द)",
        "महाकाव्य / बड़ी सीरीज़ (8000+ शब्द)",
    ])

    extra_instructions = st.text_area(
        "🎯 कोई खास/सटीक निर्देश (Optional — जो भी exact command doge, wahi follow hoga):",
        placeholder="जैसे: सिर्फ Hindi mein likho, flashback mat dalna, ek narrator character rakhna...",
        height=90,
    )

    if st.button("Generate Pro Cinematic Script ✍️🎬", type="primary", use_container_width=True):
        if not topic.strip():
            st.warning("कृपया पहले टॉपिक दर्ज करें!")
            return
        if not active_groq and not get_github_client():
            st.error("🚨 कोई भी AI Client उपलब्ध नहीं है!")
            return

        with st.spinner("प्रो AI डायरेक्टर स्क्रिप्ट, विजुअल क्यूज और डायलॉग तैयार कर रहा है..."):
            try:
                if "8000+" in length_option:
                    parts, words_per_part = 5, "लगभग 1500-2000 शब्दों का विस्तार, गहरे विवरण के साथ"
                elif "3000 - 5000" in length_option:
                    parts, words_per_part = 3, "लगभग 1200-1500 शब्दों का विस्तार"
                else:
                    parts, words_per_part = 1, "लगभग 1000 शब्दों का संपूर्ण विस्तार"

                system_prompt = _build_system_prompt(script_type, tone_style, extra_instructions)
                full_script = ""
                previous_context = ""
                used_provider = ""

                for i in range(1, parts + 1):
                    if parts > 1:
                        user_prompt = (
                            f"Write Part {i} of {parts} on the topic: '{topic}'. "
                            f"Length requirement: {words_per_part}. "
                            f"Continue directly from this previous context (maintain continuity, do not repeat it): "
                            f"'{previous_context[-400:]}'"
                        )
                    else:
                        user_prompt = (
                            f"Write a complete script on the topic: '{topic}'. "
                            f"Length requirement: {words_per_part}. "
                            "Include a strong hook at the start."
                        )

                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ]

                    response, provider = call_ai_with_fallback(active_groq, messages, max_tokens=4000, temperature=0.8)
                    used_provider = provider

                    part_content = response.choices[0].message.content
                    if not part_content or not part_content.strip():
                        raise RuntimeError(f"Part {i} के लिए खाली response मिला — दोबारा कोशिश करें।")

                    full_script += f"\n\n==================== [ सीन / भाग {i} ] ====================\n\n" + part_content
                    previous_context = part_content

                st.success(f"✨ स्क्रिप्ट सफलतापूर्वक तैयार है! (Powered by: {used_provider})")
                st.text_area("प्रो सिनेमैटिक स्क्रिप्ट:", value=full_script, height=480)

                st.download_button(
                    label="📥 Download Pro Script as Text File",
                    data=full_script,
                    file_name=f"pro_script_{sanitize_filename(topic)}.txt",
                    mime="text/plain",
                )

            except Exception as e:
                logger.exception("Script generation failed")
                st.error(f"Error: {str(e)}")


# ---------------------------------------------------------------------------
# Chatbot
# ---------------------------------------------------------------------------

CHATBOT_SYSTEM_PROMPT = (
    "You are a precise, helpful AI assistant. Follow the user's instructions exactly as given — "
    "do not add unrelated information, do not change the requested format or language, and do not "
    "pad your answers with unnecessary content. If a request is ambiguous, make a reasonable "
    "assumption and proceed rather than refusing."
)


def _render_chatbot(active_groq):
    st.subheader("💬 AI Assistant & Chatbot")
    st.write("यहाँ आप AI से किसी भी तरह की मदद, आइडिया या सवाल पूछ सकते हैं:")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_query := st.chat_input("अपना सवाल यहाँ पूछें..."):
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        if not active_groq and not get_github_client():
            st.error("🚨 AI Client उपलब्ध नहीं है!")
            return

        with st.chat_message("assistant"):
            with st.spinner("AI सोच रहा है..."):
                try:
                    trimmed_history = st.session_state.messages[-MAX_CHAT_HISTORY_MESSAGES:]
                    messages = [{"role": "system", "content": CHATBOT_SYSTEM_PROMPT}] + [
                        {"role": m["role"], "content": m["content"]} for m in trimmed_history
                    ]

                    chat_response, provider = call_ai_with_fallback(active_groq, messages, max_tokens=2000, temperature=0.7)
                    bot_reply = chat_response.choices[0].message.content
                    
                    st.markdown(bot_reply)
                    st.caption(f"⚡ Responded via: {provider}")
                    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                except Exception as e:
                    logger.exception("Chat completion failed")
                    st.error(f"Chat Error: {str(e)}")
