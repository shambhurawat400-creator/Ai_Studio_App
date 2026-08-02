import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from supabase import create_client, Client
from groq import Groq
from datetime import date
import time

# Import all custom separate modules
from auth import handle_login_session, render_auth_ui, logout_user
from image_gen import render_image_page
from video_gen import render_video_page
from voice_tools import render_voice_page
from script_gen import render_script_page

# Page Configuration
st.set_page_config(page_title="AI Studio Dashboard", page_icon="🤖", layout="wide")

SUPABASE_URL = "https://mrhjuxvgluansxrysuoy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1yaGp1eHZnbHVhbnN4cnlzdW95Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODU1ODc1NDgsImV4cCI6MjEwMTE2MzU0OH0.0Jq0cHTK16k2aN16p8n0HCU0zkritn2xgoHOeiq1a1U"
ADMIN_EMAIL = "shambhurawat400@gmail.com"
DAILY_FREE_LIMIT = 10

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Dynamic API Key Management (Session State)
if "active_api_keys" not in st.session_state:
    st.session_state.active_api_keys = {
        "GROQ_KEY": "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",
        "GEMINI_KEY": "",
        "OPENAI_KEY": "",
        "CUSTOM_VFX_KEY": ""
    }

def get_groq_client() -> Groq:
    return Groq(api_key=st.session_state.active_api_keys["GROQ_KEY"])

# Chat Helpers
def load_chat_history(user_email, chat_type):
    try:
        res = supabase.table("user_chats").select("role, content").eq("user_email", user_email).eq("chat_type", chat_type).order("created_at", desc=False).execute()
        return res.data if res.data else []
    except Exception:
        return []

def save_chat_message(user_email, role, content, chat_type):
    try:
        supabase.table("user_chats").insert({"user_email": user_email, "role": role, "content": content, "chat_type": chat_type}).execute()
    except Exception:
        pass

def get_today_message_count(user_email):
    try:
        today_str = str(date.today())
        res = supabase.table("user_chats").select("id").eq("user_email", user_email).eq("role", "user").gte("created_at", f"{today_str}T00:00:00").execute()
        return len(res.data) if res.data else 0
    except Exception:
        return 0

if "current_page" not in st.session_state:
    st.session_state.current_page = "🏠 Dashboard"

if "pricing_rules" not in st.session_state:
    st.session_state.pricing_rules = f"फ़्री प्लान: रोजाना {DAILY_FREE_LIMIT} मैसेज। प्रो प्लान: ₹199/महीना।"

# Persistent Login Check
handle_login_session(supabase)

if "user" not in st.session_state:
    render_auth_ui(supabase)
else:
    user_email = st.session_state.user.email
    is_admin = user_email == ADMIN_EMAIL

    head_col1, head_col2 = st.columns([5, 1])
    with head_col1:
        st.title("🤖 AI Studio Hub")
    with head_col2:
        if st.button("🚪 Log Out", type="secondary"):
            logout_user(supabase)

    st.write("---")
    
    # Navigation Bar
    pages = ["🏠 Dashboard", "💬 AI Chatbot", "📜 AI Script", "🎙️ Voice Studio", "🎨 AI Image", "🎬 Image to Video"]
    if is_admin:
        pages.append("⚙️ Admin AI Assistant")

    nav_cols = st.columns(len(pages))
    for i, page in enumerate(pages):
        btn_type = "primary" if st.session_state.current_page == page else "secondary"
        if nav_cols[i].button(page, type=btn_type, use_container_width=True):
            st.session_state.current_page = page
            st.rerun()

    st.write("---")

    # Routing Pages
    if st.session_state.current_page == "🏠 Dashboard":
        st.subheader(f"👋 Welcome, {user_email}!")
        if is_admin:
            st.success("👑 **Role:** Super Admin | **Access:** Full Control Over APIs & Settings")
        else:
            today_count = get_today_message_count(user_email)
            st.info(f"👤 **Role:** Free User | 📊 **आज का यूसेज:** {today_count}/{DAILY_FREE_LIMIT} मैसेज")

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
        st.subheader("💬 AI Chat Assistant")
        user_history = load_chat_history(user_email, "user")
        for msg in user_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        today_count = get_today_message_count(user_email)
        limit_reached = (not is_admin) and (today_count >= DAILY_FREE_LIMIT)
        if limit_reached:
            st.error(f"⚠️ आपकी आज की फ्री लिमिट समाप्त हो गई है!")

        if prompt := st.chat_input("AI से कुछ भी पूछें...", disabled=limit_reached):
            with st.chat_message("user"):
                st.write(prompt)
            save_chat_message(user_email, "user", prompt, "user")
            try:
                groq_client = get_groq_client()
                current_messages = [{"role": "system", "content": "You are a helpful AI assistant."}]
                for m in user_history:
                    current_messages.append({"role": m["role"], "content": m["content"]})
                current_messages.append({"role": "user", "content": prompt})

                response = groq_client.chat.completions.create(model="llama-3.1-8b-instant", messages=current_messages)
                bot_res = response.choices[0].message.content
                with st.chat_message("assistant"):
                    st.write(bot_res)
                save_chat_message(user_email, "assistant", bot_res, "user")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

    elif st.session_state.current_page == "📜 AI Script":
        try:
            groq_client = get_groq_client()
            render_script_page(groq_client)
        except Exception as e:
            st.error("API Key नहीं मिली। कृपया Admin panel में सेट करें।")

    elif st.session_state.current_page == "🎙️ Voice Studio":
        render_voice_page()

    elif st.session_state.current_page == "🎨 AI Image":
        render_image_page()

    elif st.session_state.current_page == "🎬 Image to Video":
        render_video_page()

    # ⚙️ ADMIN AI ASSISTANT & API KEY MANAGER (Only Visible to Admin)
    elif st.session_state.current_page == "⚙️ Admin AI Assistant" and is_admin:
        st.subheader("⚙️ Admin Control Panel & API Manager")
        st.write("🔒 **यह सेक्शन केवल आपको (Admin) दिख रहा है। यूज़र्स को यह नहीं दिखेगा।**")

        st.write("---")
        st.markdown("### 🔑 Live API Key Manager")
        st.info("आप यहाँ कोई भी नई API Key डाल सकते हैं। पूरा ऐप तुरंत उस नई API का इस्तेमाल करने लगेगा।")

        col1, col2 = st.columns(2)
        with col1:
            groq_input = st.text_input("Groq / LLM API Key:", value=st.session_state.active_api_keys["GROQ_KEY"], type="password")
            gemini_input = st.text_input("Google Gemini API Key:", value=st.session_state.active_api_keys["GEMINI_KEY"], type="password")
        with col2:
            openai_input = st.text_input("ChatGPT / OpenAI API Key:", value=st.session_state.active_api_keys["OPENAI_KEY"], type="password")
            custom_input = st.text_input("Custom Image/VFX Engine API Key:", value=st.session_state.active_api_keys["CUSTOM_VFX_KEY"], type="password")

        if st.button("Save & Update All API Keys 💾", type="primary"):
            st.session_state.active_api_keys["GROQ_KEY"] = groq_input
            st.session_state.active_api_keys["GEMINI_KEY"] = gemini_input
            st.session_state.active_api_keys["OPENAI_KEY"] = openai_input
            st.session_state.active_api_keys["CUSTOM_VFX_KEY"] = custom_input
            st.success("🎉 सभी API Keys अपडेट हो गईं! यूज़र्स अब आपकी नई API से सर्विस यूज़ कर सकते हैं।")

        st.write("---")
        st.markdown("### 🤖 Admin AI Studio Assistant")
        st.write("ऐप के नियमों या प्राइजिंग को बदलने के लिए यहाँ एडिट करें:")

        new_rules = st.text_area("App Rules & Pricing:", st.session_state.pricing_rules, height=100)
        if st.button("Save Rules Update"):
            st.session_state.pricing_rules = new_rules
            st.success("नियम अपडेट हो गए!")
