import sys
import os
from pathlib import Path

file_path = Path(__file__).resolve()
parent_dir = file_path.parent
sys.path.insert(0, str(parent_dir))

import streamlit as st
from groq import Groq

from script_gen import render_script_page
from image_gen import render_image_page
from video_gen import render_video_page
from voice_tools import render_voice_page
from auth_pro import get_supabase_client, restore_session, render_auth_ui, render_account_menu
from settings_pro import render_settings_page
from admin_assistant_pro import is_admin, get_config, is_feature_enabled, render_admin_assistant_page, FEATURE_KEYS
from billing_pro import is_pro_user, render_manual_upgrade_ui, render_admin_approval_panel, FREE_NANO_BANANA_DAILY_LIMIT

st.set_page_config(
    page_title="AI Studio Hub",
    page_icon="https://i.imgur.com/71Q38xq.png",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Auth: this is now the FIRST thing that runs. No page below this point is
# reachable until a real, Supabase-verified session exists.
# ---------------------------------------------------------------------------

supabase = get_supabase_client()
if supabase is None:
    st.error("🚨 Supabase कनेक्ट नहीं हो पाया। `SUPABASE_URL` और `SUPABASE_KEY` को secrets/env में सेट करें।")
    st.stop()

restore_session(supabase)

if "user" not in st.session_state:
    render_auth_ui(supabase)
    st.stop()

# ---------------------------------------------------------------------------
# Groq client — no hardcoded key. Falls back to the app's shared key (from
# secrets/env) if the user hasn't set a personal key in Settings.
# ---------------------------------------------------------------------------

if "active_api_keys" not in st.session_state:
    st.session_state.active_api_keys = {"GROQ_KEY": "", "GEMINI_KEY": "", "OPENAI_KEY": "", "CUSTOM_VFX_KEY": ""}


def get_groq_client():
    key = st.session_state.active_api_keys.get("GROQ_KEY")
    if not key or not key.startswith("gsk_"):
        key = os.environ.get("GROQ_API_KEY", "")
        if not key:
            try:
                key = st.secrets.get("GROQ_API_KEY", "")
            except Exception:
                key = ""
    if not key:
        return None
    return Groq(api_key=key)


if "current_page" not in st.session_state:
    st.session_state.current_page = "🏠 Dashboard"
if "pricing_rules" not in st.session_state:
    st.session_state.pricing_rules = get_config(supabase, "pricing_rules", "फ़्री प्लान: रोजाना 10 मैसेज। प्रो प्लान: ₹199/महीना।")

admin_user = is_admin(st.session_state.get("user"))
app_title = get_config(supabase, "app_title", "🤖 AI Studio Hub")

# ---------------------------------------------------------------------------
# Header: title + account menu (email + logout)
# ---------------------------------------------------------------------------

head_col1, head_col2 = st.columns([3, 2])
with head_col1:
    st.title(app_title)
with head_col2:
    render_account_menu(supabase)

st.write("---")

# Build nav list, respecting feature flags (hidden from non-admins if a tool
# is turned off; admin still sees it, marked, so they can turn it back on)
pages = ["🏠 Dashboard"]
for flag_key, label in FEATURE_KEYS.items():
    enabled = is_feature_enabled(supabase, flag_key)
    if enabled:
        pages.append(label)
    elif admin_user:
        pages.append(f"🚧 {label}")
pages.append("💳 Pricing")
pages.append("💎 Upgrade to Pro")
if admin_user:
    pages.append("🧾 Pending Payments")
pages.append("⚙️ Settings")
if admin_user:
    pages.append("🛠️ Admin Assistant")

nav_cols = st.columns(len(pages))
for i, page in enumerate(pages):
    btn_type = "primary" if st.session_state.current_page == page else "secondary"
    if nav_cols[i].button(page, type=btn_type, use_container_width=True):
        st.session_state.current_page = page
        st.rerun()

st.write("---")

# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

if st.session_state.current_page == "🏠 Dashboard":
    st.subheader(get_config(supabase, "dashboard_welcome", "👋 Welcome to AI Studio Dashboard!"))
    st.info(get_config(supabase, "dashboard_info_banner", "💡 यहाँ से आप कोई भी AI टूल डायरेक्ट ओपन कर सकते हैं।"))

    custom_notice = get_config(supabase, "custom_notice", "")
    if custom_notice:
        st.warning(f"📢 {custom_notice}")

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

    col4, col5, col6 = st.columns(3)
    with col4:
        if st.button("🎨 Open Image Generator", use_container_width=True):
            st.session_state.current_page = "🎨 AI Image"
            st.rerun()
    with col5:
        if st.button("🎬 Open Video Generator", use_container_width=True):
            st.session_state.current_page = "🎬 Image to Video"
            st.rerun()
    with col6:
        if st.button("⚙️ Open Settings", use_container_width=True):
            st.session_state.current_page = "⚙️ Settings"
            st.rerun()

elif st.session_state.current_page in ("💬 AI Chatbot", "🚧 💬 AI Chatbot"):
    if st.session_state.current_page.startswith("🚧"):
        st.warning(get_config(supabase, "maintenance_message", "🚧 Ye feature abhi maintenance mode mein hai."))
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

        groq_client = get_groq_client()
        if not groq_client:
            st.error("🚨 GROQ_API_KEY सेट नहीं है (Settings में अपनी key daal sakte ho, ya app-level secret set karo).")
        else:
            try:
                current_messages = [{
                    "role": "system",
                    "content": "You are a professional Admin Assistant and expert Streamlit/Python developer. Follow the user's instructions precisely, do not add unrelated content. Help the user manage their app, write code snippets, and answer questions accurately in Hindi/Hinglish.",
                }]
                for m in st.session_state.chat_messages:
                    current_messages.append({"role": m["role"], "content": m["content"]})

                response = groq_client.chat.completions.create(model="llama-3.1-8b-instant", messages=current_messages)
                bot_res = response.choices[0].message.content
                with st.chat_message("assistant"):
                    st.write(bot_res)
                st.session_state.chat_messages.append({"role": "assistant", "content": bot_res})
            except Exception as e:
                st.error(f"Chat Error: {str(e)}")

elif st.session_state.current_page in ("📜 AI Script", "🚧 📜 AI Script"):
    if st.session_state.current_page.startswith("🚧"):
        st.warning(get_config(supabase, "maintenance_message", "🚧 Ye feature abhi maintenance mode mein hai."))
    try:
        render_script_page(get_groq_client())
    except Exception as e:
        st.error(f"Script Page Error: {str(e)}")

elif st.session_state.current_page in ("🎙️ Voice Studio", "🚧 🎙️ Voice Studio"):
    if st.session_state.current_page.startswith("🚧"):
        st.warning(get_config(supabase, "maintenance_message", "🚧 Ye feature abhi maintenance mode mein hai."))
    render_voice_page()

elif st.session_state.current_page in ("🎨 AI Image", "🚧 🎨 AI Image"):
    if st.session_state.current_page.startswith("🚧"):
        st.warning(get_config(supabase, "maintenance_message", "🚧 Ye feature abhi maintenance mode mein hai."))
    render_image_page(supabase, st.session_state.user)

elif st.session_state.current_page in ("🎬 Image to Video", "🚧 🎬 Image to Video"):
    if st.session_state.current_page.startswith("🚧"):
        st.warning(get_config(supabase, "maintenance_message", "🚧 Ye feature abhi maintenance mode mein hai."))
    render_video_page()

elif st.session_state.current_page == "💳 Pricing":
    st.subheader("💳 Pricing / Plans")
    st.markdown(get_config(supabase, "pricing_rules", "फ़्री प्लान: रोजाना 10 मैसेज। प्रो प्लान: ₹199/महीना।"))

elif st.session_state.current_page == "💎 Upgrade to Pro":
    st.subheader("💎 Upgrade to Pro")
    user_pro = is_pro_user(supabase, st.session_state.user)
    if user_pro:
        st.success("✅ Aap already Pro user hain! Sabhi premium features unlimited hain.")
    else:
        pro_price = float(get_config(supabase, "pro_price_inr", "99"))
        upi_id = get_config(supabase, "upi_id", "")
        st.write(f"**Free plan:** Nano Banana (high-quality image) sirf {FREE_NANO_BANANA_DAILY_LIMIT}/din")
        st.write("**Pro plan:** Nano Banana **unlimited** use, koi daily cap nahi")
        render_manual_upgrade_ui(supabase, st.session_state.user, upi_id, pro_price)

elif st.session_state.current_page == "🧾 Pending Payments" and admin_user:
    render_admin_approval_panel(supabase)

elif st.session_state.current_page == "⚙️ Settings":
    render_settings_page(supabase)

elif st.session_state.current_page == "🛠️ Admin Assistant" and admin_user:
    render_admin_assistant_page(supabase, get_groq_client())
