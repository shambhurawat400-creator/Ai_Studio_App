import streamlit as st
from supabase import create_client, Client
from groq import Groq
from datetime import date
import time

# Import all custom modules safely
from auth import handle_login_session, render_auth_ui, logout_user
from image_gen import render_image_page
from video_gen import render_video_page
from voice_tools import render_voice_page
from script_gen import render_script_page

# Page Configuration
st.set_page_config(page_title="AI Studio Dashboard", page_icon="🤖", layout="wide")

SUPABASE_URL = "https://mrhjuxvgluansxrysuoy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1yaGp1eHZnbHVhbnN4cnlzdW95Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODU1ODc1NDgsImV4cCI6MjEwMTE2MzU0OH0.0Jq0cHTK16k2aN16p8n0HCU0zkritn2xgoHOeiq1a1U"
GROQ_KEYS = ["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"]
ADMIN_EMAIL = "shambhurawat400@gmail.com"
DAILY_FREE_LIMIT = 10

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def get_groq_client(key_index=0) -> Groq:
    return Groq(api_key=GROQ_KEYS[key_index])

supabase = init_supabase()
groq_client = get_groq_client(0)

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

# Handle Login/Refresh Session
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
    
    # Complete Navigation including Voice Cloning & Scripting
    pages = ["🏠 Dashboard", "💬 AI Chatbot", "📜 AI Script", "🎙️ Voice Studio", "🎨 AI Image", "🎬 Image to Video"]
    if is_admin:
        pages.append("⚙️ Admin")

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
            st.success("👑 **Role:** Super Admin | **Access:** Unlimited")
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
        render_script_page(groq_client)

    elif st.session_state.current_page == "🎙️ Voice Studio":
        render_voice_page()

    elif st.session_state.current_page == "🎨 AI Image":
        render_image_page()

    elif st.session_state.current_page == "🎬 Image to Video":
        render_video_page()

    elif st.session_state.current_page == "⚙️ Admin" and is_admin:
        st.subheader("⚙️ Admin Dashboard")
        st.write("**Current Rules:**", st.session_state.pricing_rules)
        new_rules = st.text_area("नये नियम:", st.session_state.pricing_rules)
        if st.button("Save Rules"):
            st.session_state.pricing_rules = new_rules
            st.success("अपडेट हो गया!")
