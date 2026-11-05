"""
AI Video & Story Script Writer & Chatbot Hub — ULTRA-FAST FLASH-LITE EDITION
"""

import io
import random
import re
import time
import logging

import streamlit as st
from google import genai
from google.genai import errors

logger = logging.getLogger(__name__)

GEMINI_MODEL_NAME = "gemini-3.5-flash-lite"

MAX_CHAT_HISTORY_MESSAGES = 20


# ---------------------------------------------------------------------------
# Gemini Client Setup
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def get_gemini_client() -> genai.Client | None:
    import os
    api_key = None
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        logger.error("Failed to init Gemini client: %s", e)
        return None


# ---------------------------------------------------------------------------
# Robust & Fast Streaming Response
# ---------------------------------------------------------------------------

def stream_gemini_response(messages, max_tokens=8000, temperature=0.7):
    client = get_gemini_client()
    if not client:
        raise RuntimeError("Gemini API Key set nahi hai! Streamlit Secrets mein GEMINI_API_KEY add karein.")

    contents = []
    system_instruction = None
    
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content")
        if role == "system":
            system_instruction = content
        elif role == "user":
            contents.append(f"User: {content}")
        elif role == "assistant":
            contents.append(f"Model: {content}")

    try:
        config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        if system_instruction:
            config["system_instruction"] = system_instruction

        response = client.models.generate_content_stream(
            model=GEMINI_MODEL_NAME,
            contents="\n".join(contents),
            config=config,
        )
        
        for chunk in response:
            if getattr(chunk, "text", None):
                yield chunk.text
                
    except Exception as e:
        logger.error("Gemini generation error: %s", e)
        raise RuntimeError(f"Gemini Error: {str(e)}")


def sanitize_filename(text: str) -> str:
    text = text.strip()[:40]
    return re.sub(r"[^\w\-]+", "_", text) or "script"


def word_stats(text: str):
    words = len(text.split())
    minutes = max(1, round(words / 130))
    return words, minutes


def export_docx_bytes(title: str, body: str) -> bytes:
    from docx import Document
    doc = Document()
    doc.add_heading(title or "Script", level=1)
    for para in body.split("\n"):
        doc.add_paragraph(para)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------------

def render_script_page(groq_client=None):
    st.subheader("📜 AI Video & Story Script Writer & Chatbot Hub — Ultra-Fast")
    st.write("यहाँ से आप यूट्यूब, शॉर्ट्स या लंबी कहानियों के लिए स्क्रिप्ट तैयार कर सकते हैं और AI चैटबॉट से बात कर सकते हैं:")

    gemini_ok = bool(get_gemini_client())

    if not gemini_ok:
        st.error("🚨 GEMINI_API_KEY set nahi hai. Kripya Streamlit Secrets mein apni Gemini API key save karein.")
    else:
        st.caption("✅ Powered by Google Gemini Flash-Lite")

    app_mode = st.radio("फीचर चुनें:", ["✍️ Pro Script Writer", "💬 AI Assistant Chatbot"], horizontal=True)

    if app_mode == "✍️ Pro Script Writer":
        _render_script_writer()
    else:
        _render_chatbot()


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
        base += (
            "\n\nAdditional instructions from the user (apply these, but they "
            f"cannot override the format/tone rules above): {extra_instructions.strip()}"
        )
    return base


def _render_script_writer():
    if "script_history" not in st.session_state:
        st.session_state.script_history = []

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
        "🎯 कोई खास/सटीक निर्देश (Optional):",
        placeholder="जैसे: सिर्फ Hindi mein likho, flashback mat dalna...",
        height=90,
    )

    with st.expander("⚙️ Advanced Settings"):
        temperature = st.slider("Creativity (temperature)", 0.2, 1.2, 0.7, 0.1)
        max_tokens = st.slider("Max tokens", 2000, 8000, 6000, 500)

    generate_clicked = st.button("Generate Pro Cinematic Script ✍️🎬", type="primary", use_container_width=True)

    if generate_clicked:
        if not topic.strip():
            st.warning("कृपया पहले टॉपिक दर्ज करें!")
            return

        if "8000+" in length_option:
            length_desc = "विस्तृत और लंबी महाकाव्य स्क्रिप्ट (8000+ शब्द)"
        elif "3000 - 5000" in length_option:
            length_desc = "विस्तृत लंबी कहानी / वीडियो स्क्रिप्ट (3000 - 5000 शब्द)"
        else:
            length_desc = "संतुलित मध्यम स्क्रिप्ट (1000 - 2000 शब्द)"

        system_prompt = _build_system_prompt(script_type, tone_style, extra_instructions)
        user_prompt = (
            f"Write a complete cinematic script on the topic: '{topic}'. "
            f"Length requirement: {length_desc}. "
            "Include a strong hook, detailed scenes, camera cues, and complete dialogues."
        )

        st.markdown(f"**[ स्क्रिप्ट जनरेट हो रही है... ]**")
        placeholder = st.empty()
        collected = ""

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            for chunk in stream_gemini_response(messages, max_tokens=max_tokens, temperature=temperature):
                collected += chunk
                placeholder.markdown(collected + "▌")
            placeholder.markdown(collected)

            if not collected.strip():
                st.error("खाली रिस्पॉन्स मिला — कृपया दोबारा कोशिश करें।")
                return

            st.session_state.script_history.append({
                "title": topic, "script": collected, "provider": "Google Gemini Flash-Lite",
            })
            st.success("स्क्रिप्ट सफलतापर्वक तैयार हो गई है! ✅")
        except RuntimeError as e:
            placeholder.error(str(e))
            return

    if st.session_state.script_history:
        latest = st.session_state.script_history[-1]
        words, minutes = word_stats(latest["script"])
        st.divider()
        st.caption(f"⚙️ Powered by: Google Gemini Flash-Lite  |  📝 {words} words  |  🎙️ ~{minutes} min read")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button("📥 Download .txt", data=latest["script"],
                                file_name=f"{sanitize_filename(latest['title'])}.txt", mime="text/plain")
        with c2:
            st.download_button("📥 Download .md", data=latest["script"],
                                file_name=f"{sanitize_filename(latest['title'])}.md", mime="text/markdown")
        with c3:
            try:
                docx_bytes = export_docx_bytes(latest["title"], latest["script"])
                st.download_button(
                    "📥 Download .docx", data=docx_bytes,
                    file_name=f"{sanitize_filename(latest['title'])}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            except ImportError:
                st.caption("`.docx` export ke liye `pip install python-docx` chahiye.")

        if len(st.session_state.script_history) > 1:
            with st.expander(f"📚 पिछली scripts ({len(st.session_state.script_history) - 1})"):
                for idx, item in enumerate(reversed(st.session_state.script_history[:-1])):
                    st.write(f"**{item['title']}**")
                    st.text_area("", value=item["script"], height=150, key=f"hist_{idx}", label_visibility="collapsed")


# ---------------------------------------------------------------------------
# Chatbot
# ---------------------------------------------------------------------------

CHATBOT_SYSTEM_PROMPT = (
    "You are a precise, helpful AI assistant. Follow the user's instructions exactly as given — "
    "do not add unrelated information, do not change the requested format or language, and do not "
    "pad your answers with unnecessary content. If a request is ambiguous, make a reasonable "
    "assumption and proceed rather than refusing."
)


def _render_chatbot():
    st.subheader("💬 AI Assistant & Chatbot")
    st.write("यहाँ आप AI से किसी भी तरह की मदद, आइडिया या सवाल पूछ सकते हैं:")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.session_state.messages:
            chat_export = "\n\n".join(
                f"**{m['role'].upper()}:** {m['content']}" for m in st.session_state.messages
            )
            st.download_button("📥 Export Chat", data=chat_export, file_name="chat_export.md", mime="text/markdown")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    def _do_turn(user_query):
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            trimmed_history = st.session_state.messages[-MAX_CHAT_HISTORY_MESSAGES:]
            msgs = [{"role": "system", "content": CHATBOT_SYSTEM_PROMPT}] + [
                {"role": m["role"], "content": m["content"]} for m in trimmed_history
            ]
            try:
                bot_reply = st.write_stream(stream_gemini_response(msgs, max_tokens=4000, temperature=0.7))
                st.caption("⚙️ Powered by: Google Gemini Flash-Lite")
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            except RuntimeError as e:
                st.error(str(e))

    if user_query := st.chat_input("अपना सवाल यहाँ पूछें..."):
        _do_turn(user_query)

    if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        if st.button("🔄 Regenerate last answer"):
            last_user_msg = next(
                (m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"), None
            )
            if last_user_msg:
                st.session_state.messages.pop()
                with st.chat_message("assistant"):
                    trimmed_history = st.session_state.messages[-MAX_CHAT_HISTORY_MESSAGES:]
                    msgs = [{"role": "system", "content": CHATBOT_SYSTEM_PROMPT}] + [
                        {"role": m["role"], "content": m["content"]} for m in trimmed_history
                    ]
                    try:
                        bot_reply = st.write_stream(stream_gemini_response(msgs, max_tokens=4000, temperature=0.7))
                        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                    except RuntimeError as e:
                        st.error(str(e))
