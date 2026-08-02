import streamlit as st
from supabase import create_client, Client
from groq import Groq
from datetime import date
import time

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

# --- EMBEDDED AUTH FUNCTIONS (NO SEPARATE FILE NEEDED) ---
def handle_login_session(sb_client):
    query_params = st.query_params
    if "access_token" in query_params:
        try:
            token = query_params["access_token"]
            res = sb_client.auth.get_user(token)
            if res and res.user:
                st.session_state.user = res.user
        except Exception:
            pass

def render_auth_ui(sb_client):
    st.subheader("🔐 Login / Sign Up to AI Studio")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        email = st.text_input("Email", key="l_email")
        password = st.text_input("Password", type="password", key="l_pass")
        if st.button("Login", type="primary"):
            try:
                res = sb_client.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.success("सफलतापूर्वक लॉगिन हो गया!")
                st.rerun()
            except Exception as e:
                st.error(f"Login Error: {str(e)}")
                
    with tab2:
        s_email = st.text_input("Email", key="s_email")
        s_pass = st.text_input("Password", type="password", key="s_pass")
        if st.button("Create Account"):
            try:
                sb_client.auth.sign_up({"email": s_email, "password": s_pass})
                st.success("अकाउंट बन गया! अब Login टैब से लॉगिन करें।")
            except Exception as e:
                st.error(f"Sign Up Error: {str(e)}")

def logout_user(sb_client):
    try:
        sb_client.auth.sign_out()
    except Exception:
        pass
    if "user" in st.session_state:
        del st.session_state["user"]
    st.rerun()

# Dynamic API Key Management
if "active_api_keys" not in st.session_state:
    st.session_state.active_api_keys = {
        "GROQ_KEY": "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",
        "GEMINI_KEY": "",
        "OPENAI_KEY": "",
        "CUSTOM_VFX_KEY": ""
    }

def get_groq_client() -> Groq:
    return Groq(api_key=st.session_state.active_api_keys["GROQ_KEY"])

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

    if st.session_state.current_page == "🏠 Dashboard":
        st.subheader(f"👋 Welcome, {user_email}!")
        if is_admin:
            st.success("👑 **Role:** Super Admin | **Access:** Full Control")
        else:
            today_count = get_today_message_count(user_email)
            st.info(f"👤 **Role:** Free User | 📊 **आज का यूसेज:** {today_count}/{DAILY_FREE_LIMIT} मैसेज")

    elif st.session_state.current_page == "💬 AI Chatbot":
        st.subheader("💬 AI Chat Assistant")
        user_history = load_chat_history(user_email, "user")
        for msg in user_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        if prompt := st.chat_input("AI से कुछ भी पूछें..."):
            with st.chat_message("user"):
                st.write(prompt)
            save_chat_message(user_email, "user", prompt, "user")
            try:
                groq_client = get_groq_client()
                response = groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}]
                )
                bot_res = response.choices[0].message.content
                with st.chat_message("assistant"):
                    st.write(bot_res)
                save_chat_message(user_email, "assistant", bot_res, "user")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

    elif st.session_state.current_page == "📜 AI Script":
        st.subheader("📜 AI Script Writer")
        topic = st.text_input("स्क्रिप्ट का टॉपिक दर्ज करें:")
        if st.button("Generate Script"):
            if topic:
                try:
                    groq_client = get_groq_client()
                    res = groq_client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": f"Write a YouTube script about: {topic}"}]
                    )
                    st.write(res.choices[0].message.content)
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    elif st.session_state.current_page == "🎙️ Voice Studio":
        st.subheader("🎙️ Voice Studio")
        st.info("Voice tools coming soon...")

    elif st.session_state.current_page == "🎨 AI Image":
        st.subheader("🎨 AI Image Generator")
        st.info("Image generator coming soon...")

    elif st.session_state.current_page == "🎬 Image to Video":
        st.subheader("🎬 Video Generator")
        st.info("Video generator coming soon...")

    elif st.session_state.current_page == "⚙️ Admin AI Assistant" and is_admin:
        st.subheader("⚙️ Admin Control Panel")
        groq_input = st.text_input("Groq API Key:", value=st.session_state.active_api_keys["GROQ_KEY"], type="password")
        if st.button("Save API Key"):
            st.session_state.active_api_keys["GROQ_KEY"] = groq_input
            st.success("API Key अपडेट हो गई!")
