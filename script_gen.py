"""
AI Video & Story Script Writer & Chatbot Hub (Pro Version with Groq & GitHub Fallback)
"""

import re
import time
import logging

import streamlit as st
from groq import Groq
from openai import OpenAI

logger = logging.getLogger(__name__)

MODEL_NAME = "llama-3.1-8b-instant"
GITHUB_MODEL_NAME = "gpt-4o" 
MAX_CHAT_HISTORY_MESSAGES = 20
MAX_RETRIES = 2

# ---------------------------------------------------------------------------
# Client Setup
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def get_groq_client() -> Groq | None:
    import os
    api_key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
    if not api_key: return None
    try: return Groq(api_key=api_key)
    except: return None

@st.cache_resource(show_spinner=False)
def get_github_client() -> OpenAI | None:
    import os
    token = st.secrets.get("GITHUB_TOKEN", os.environ.get("GITHUB_TOKEN", ""))
    if not token: return None
    try:
        return OpenAI(
            base_url="https://models.inference.ai.azure.com/v1",
            api_key=token
        )
    except: return None

def call_ai_with_fallback(groq_client, messages, max_tokens=4000, temperature=0.7):
    github_client = get_github_client()
    last_error = None

    # 1. Try Groq
    if groq_client:
        try:
            return groq_client.chat.completions.create(
                model=MODEL_NAME, messages=messages, max_tokens=max_tokens, temperature=temperature
            ), "Groq"
        except Exception as e:
            last_error = e
            logger.warning(f"Groq failed: {e}")

    # 2. Fallback to GitHub
    if github_client:
        try:
            return github_client.chat.completions.create(
                model=GITHUB_MODEL_NAME, messages=messages, max_tokens=max_tokens, temperature=temperature
            ), "GitHub Models"
        except Exception as e:
            last_error = e
            logger.error(f"GitHub fallback failed: {e}")

    raise RuntimeError(f"All AI providers failed. Last error: {str(last_error)}")

def sanitize_filename(text: str) -> str:
    text = text.strip()[:40]
    return re.sub(r"[^\w\-]+", "_", text) or "script"

# ---------------------------------------------------------------------------
# Rendering Functions
# ---------------------------------------------------------------------------

def render_script_page(groq_client=None):
    st.subheader("📜 AI Video & Story Script Writer")
    active_groq = groq_client or get_groq_client()
    
    app_mode = st.radio("फीचर चुनें:", ["✍️ Pro Script Writer", "💬 AI Assistant Chatbot"], horizontal=True)

    if app_mode == "✍️ Pro Script Writer":
        _render_script_writer(active_groq)
    else:
        _render_chatbot(active_groq)

def _render_script_writer(active_groq):
    topic = st.text_input("स्क्रिप्ट का टॉपिक:")
    col1, col2 = st.columns(2)
    with col1:
        script_type = st.selectbox("प्लेटफॉर्म:", ["YouTube Video", "Instagram Reel", "Horror Story", "Motivational"])
    with col2:
        tone_style = st.selectbox("टोन:", ["Suspense", "Emotional", "Energetic", "Informative"])
    
    if st.button("Generate Script ✍️"):
        if not topic:
            st.warning("टॉपिक लिखें!")
            return
        
        with st.spinner("AI स्क्रिप्ट बना रहा है..."):
            try:
                system_prompt = f"You are a professional scriptwriter. Format: {script_type}. Tone: {tone_style}. Write in Hindi/Hinglish."
                messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Write a script about: {topic}"}]
                
                response, provider = call_ai_with_fallback(active_groq, messages)
                script = response.choices[0].message.content
                
                st.text_area("रिजल्ट:", value=script, height=400)
                st.caption(f"Powered by: {provider}")
            except Exception as e:
                st.error(f"Error: {e}")

def _render_chatbot(active_groq):
    if "messages" not in st.session_state: st.session_state.messages = []
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    
    if prompt := st.chat_input("कुछ पूछें..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            try:
                messages = [{"role": "system", "content": "You are a helpful assistant."}] + st.session_state.messages[-10:]
                response, provider = call_ai_with_fallback(active_groq, messages)
                reply = response.choices[0].message.content
                st.markdown(reply)
                st.caption(f"Powered by: {provider}")
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                st.error(f"Chat Error: {e}")
