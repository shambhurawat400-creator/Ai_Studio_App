import sys
import os
from pathlib import Path

# --- THE ULTIMATE ROOT PATH FIX ---
file_path = Path(__file__).resolve()
parent_dir = file_path.parent
sys.path.insert(0, str(parent_dir))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from groq import Groq
from datetime import date
import time

# Import all custom modules safely
from script_gen import render_script_page
from image_gen import render_image_page
from video_gen import render_video_page
from voice_tools import render_voice_page

# Page Configuration
st.set_page_config(page_title="AI Studio Dashboard", page_icon="🤖", layout="wide")

# Dynamic API Key Management (Session State & Secure Fallback)
if "active_api_keys" not in st.session_state:
    st.session_state.active_api_keys = {
        "GROQ_KEY": "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",
        "GEMINI_KEY": "",
        "OPENAI_KEY": "",
        "CUSTOM_VFX_KEY": ""
    }

def get_groq_client() -> Groq:
    # पहले session state से कोशिश करेगा, फिर secrets से या सीधे फिक्स की से
    key = st.session_state.active_api_keys.get("GROQ_KEY")
    if not key or "gsk_" not in key:
        key = "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"
    return Groq(api_key=key)

if "current_page" not in st.session_state:
    st.session_state.current_page = "🏠 Dashboard"

if "pricing_rules" not in st.session_state:
    st.session_state.pricing_rules = "फ़्री प्लान: रोजाना 10 मैसेज। प्रो प्लान: ₹199/महीना।"

# Main Dashboard UI Layout
head_col1, head_col2 = st.columns([5, 1])
with head_col1:
    st.title("🤖 AI Studio Hub")

st.write("---")

# Navigation Bar with Script Page Included
pages = ["🏠 Dashboard", "💬 AI Chatbot", "📜 AI Script", "🎙️ Voice Studio", "🎨 AI Image", "🎬 Image to Video"]

nav_cols = st.columns(len(pages))
for i, page in enumerate(pages):
    btn_type = "primary" if st.session_state.current_page == page else "secondary"
    if nav_cols[i].button(page, type=btn_type, use_container_width=True):
        st.session_state.current_page = page
        st.rerun()

st.write("---")

# Routing Pages
if st.session_state.current_page == "🏠 Dashboard":
    st.subheader("👋 Welcome to AI Studio Dashboard!")
    st.info("💡 यहाँ से आप कोई भी AI टूल डायरेक्ट ओपन कर सकते हैं।")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💬 Open Chatbot", use_container_width=True):
            st.session_state.current_page = "💬 AI Chatbot"
            st.rerun()
    with col2:
        if st.button("📜 Open Script Writer", use_container_width=True):
            st.session_state.current_page = "📜 AI Script"
            st.rerun()
    with col3:
        if st.button("🎙️ Open Voice Studio", use_container_width=True):
            st.session_state.current_page = "🎙️ Voice Studio"
            st.rerun()

    col4, col5 = st.columns(2)
    with col4:
        if st.button("🎨 Open Image Generator", use_container_width=True):
            st.session_state.current_page = "🎨 AI Image"
            st.rerun()
    with col5:
        if st.button("🎬 Open Video Generator", use_container_width=True):
            st.session_state.current_page = "🎬 Image to Video"
            st.rerun()

elif st.session_state.current_page == "💬 AI Chatbot":
    st.subheader("💬 AI Chat Assistant & Admin Helper")
    st.write("यहाँ आप अपने AI असिस्टेंट से सामान्य सवाल पूछ सकते हैं या भविष्य में ऐप में बदलाव/कोडिंग से जुड़े निर्देश ले सकते हैं।")
    
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("AI से कुछ भी पूछें या ऐप में बदलाव के लिए निर्देश दें..."):
        with st.chat_message("user"):
            st.write(prompt)
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        try:
            groq_client = get_groq_client()
            # यहाँ एडमिन/कोडिंग असिस्टेंट का सिस्टम प्रॉम्प्ट जोड़ा गया है ताकि यह ऐप डेवलपर की तरह मदद कर सके
            current_messages = [{
                "role": "system", 
                "content": "You are a professional Admin Assistant and expert Streamlit/Python developer. Help the user manage their app, write code snippets, and answer questions accurately in Hindi/Hinglish."
            }]
            for m in st.session_state.chat_messages:
                current_messages.append({"role": m["role"], "content": m["content"]})

            response = groq_client.chat.completions.create(model="llama-3.1-8b-instant", messages=current_messages)
            bot_res = response.choices[0].message.content
            with st.chat_message("assistant"):
                st.write(bot_res)
            st.session_state.chat_messages.append({"role": "assistant", "content": bot_res})
            st.rerun()
        except Exception as e:
            st.error(f"Chat Error: {str(e)}")

elif st.session_state.current_page == "📜 AI Script":
    try:
        groq_client = get_groq_client()
        render_script_page(groq_client)
    except Exception as e:
        st.error(f"Script Page Error: {str(e)}")

elif st.session_state.current_page == "🎙️ Voice Studio":
    render_voice_page()

elif st.session_state.current_page == "🎨 AI Image":
    render_image_page()

elif st.session_state.current_page == "🎬 Image to Video":
    render_video_page()
