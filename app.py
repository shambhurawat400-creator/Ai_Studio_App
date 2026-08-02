import streamlit as st
from supabase import create_client, Client
from groq import Groq
from datetime import date
import urllib.parse

# Page Configuration
st.set_page_config(page_title="AI Studio Dashboard", page_icon="🤖", layout="wide")

# Credentials
SUPABASE_URL = "https://mrhjuxvgluansxrysuoy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1yaGp1eHZnbHVhbnN4cnlzdW95Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODU1ODc1NDgsImV4cCI6MjEwMTE2MzU0OH0.0Jq0cHTK16k2aN16p8n0HCU0zkritn2xgoHOeiq1a1U"

GROQ_KEYS = [
    "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"
]

ADMIN_EMAIL = "shambhurawat400@gmail.com"
DAILY_FREE_LIMIT = 10

# Initialize Clients
@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def get_groq_client(key_index=0) -> Groq:
    return Groq(api_key=GROQ_KEYS[key_index])

supabase = init_supabase()

# Helper Functions
def load_chat_history(user_email, chat_type):
    try:
        res = supabase.table("user_chats") \
            .select("role, content") \
            .eq("user_email", user_email) \
            .eq("chat_type", chat_type) \
            .order("created_at", desc=False) \
            .execute()
        return res.data if res.data else []
    except Exception:
        return []

def save_chat_message(user_email, role, content, chat_type):
    try:
        supabase.table("user_chats").insert({
            "user_email": user_email,
            "role": role,
            "content": content,
            "chat_type": chat_type
        }).execute()
    except Exception:
        pass

def get_today_message_count(user_email):
    try:
        today_str = str(date.today())
        res = supabase.table("user_chats") \
            .select("id") \
            .eq("user_email", user_email) \
            .eq("role", "user") \
            .gte("created_at", f"{today_str}T00:00:00") \
            .execute()
        return len(res.data) if res.data else 0
    except Exception:
        return 0

# Session States
if "user" not in st.session_state:
    st.session_state.user = None

if "current_page" not in st.session_state:
    st.session_state.current_page = "🏠 Dashboard"

if "pricing_rules" not in st.session_state:
    st.session_state.pricing_rules = f"फ़्री प्लान: रोजाना {DAILY_FREE_LIMIT} मैसेज। प्रो प्लान: ₹199/महीना (अनलिमिटेड)।"

# Auth Screen
if st.session_state.user is None:
    st.title("🚀 Welcome to AI Studio")
    tab1, tab2 = st.tabs(["🔒 Login", "📝 Sign Up"])

    with tab1:
        st.subheader("Login to your account")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Log In", type="primary"):
            if email and password:
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user = res.user
                    st.session_state.current_page = "🏠 Dashboard"
                    st.success("सफलतापूर्वक लॉगिन हो गया! 🎉")
                    st.rerun()
                except Exception as e:
                    st.error(f"लॉगिन में त्रुटि: {str(e)}")
            else:
                st.warning("कृपया ईमेल और पासवर्ड भरें।")

    with tab2:
        st.subheader("Create a new account")
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_pass")
        
        if st.button("Sign Up"):
            if new_email and new_password:
                try:
                    res = supabase.auth.sign_up({"email": new_email, "password": new_password})
                    st.success("अकाउंट बन गया! अब लॉगिन करें।")
                except Exception as e:
                    st.error(f"साइन अप में त्रुटि: {str(e)}")
            else:
                st.warning("कृपया ईमेल और पासवर्ड भरें।")

# Logged In View
else:
    user_email = st.session_state.user.email
    is_admin = user_email == ADMIN_EMAIL

    # Header Bar
    head_col1, head_col2 = st.columns([4, 1])
    with head_col1:
        st.title("🤖 AI Studio Hub")
    with head_col2:
        if st.button("🚪 Log Out", type="secondary"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    # Top Navigation Selection
    if is_admin:
        nav_options = ["🏠 Dashboard", "👑 Admin Assistant", "💬 AI Chatbot", "🎨 AI Image Generator", "⚙️ App Settings"]
    else:
        nav_options = ["🏠 Dashboard", "💬 AI Chatbot", "🎨 AI Image Generator"]

    selected_nav = st.selectbox("📌 Select Feature / Navigation:", nav_options, index=nav_options.index(st.session_state.current_page) if st.session_state.current_page in nav_options else 0)
    st.session_state.current_page = selected_nav

    st.write("---")

    # 🏠 MAIN DASHBOARD PAGE
    if st.session_state.current_page == "🏠 Dashboard":
        st.subheader(f"👋 Welcome, {user_email}!")

        if is_admin:
            st.success("👑 **Role:** Super Admin | **Access:** Unlimited")
        else:
            today_count = get_today_message_count(user_email)
            remaining = max(0, DAILY_FREE_LIMIT - today_count)
            st.info(f"👤 **Role:** Free User | 📊 **आज का यूसेज:** {today_count}/{DAILY_FREE_LIMIT} मैसेज (बचे: {remaining})")

        st.write("### 🚀 Available AI Tools")
        st.caption("नीचे दिए गए टूल पर क्लिक करके काम शुरू करें:")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 💬 AI Chat Assistant")
            st.write("स्मार्ट AI से सवाल पूछें और बातचीत करें।")
            if st.button("Open AI Chat ➔", type="primary", use_container_width=True):
                st.session_state.current_page = "💬 AI Chatbot"
                st.rerun()

        with col2:
            st.markdown("### 🎨 AI Image Generator")
            st.write("शानदार स्टाइल्स और आस्पेक्ट रेशियो के साथ HD इमेज बनाएं।")
            if st.button("Open Image Generator ➔", type="primary", use_container_width=True):
                st.session_state.current_page = "🎨 AI Image Generator"
                st.rerun()

        if is_admin:
            st.write("---")
            st.write("### 👑 Admin Special Tools")
            admin_col1, admin_col2 = st.columns(2)
            
            with admin_col1:
                st.markdown("### 👑 Admin Assistant")
                st.write("ऐप सेटिंग्स और कॉन्फ़िगरेशन के लिए एडमिन AI।")
                if st.button("Open Admin Assistant ➔", use_container_width=True):
                    st.session_state.current_page = "👑 Admin Assistant"
                    st.rerun()

            with admin_col2:
                st.markdown("### ⚙️ App Settings & Rules")
                st.write("ऐप के नियम और प्राइसिंग एडिट करें।")
                if st.button("Open App Settings ➔", use_container_width=True):
                    st.session_state.current_page = "⚙️ App Settings"
                    st.rerun()

    # 💬 CHATBOT PAGE
    elif st.session_state.current_page == "💬 AI Chatbot":
        st.subheader("💬 AI Chat Assistant")

        with st.expander("ℹ️ Rules & Pricing"):
            st.write(st.session_state.pricing_rules)

        user_history = load_chat_history(user_email, "user")
        for msg in user_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        today_count = get_today_message_count(user_email)
        limit_reached = (not is_admin) and (today_count >= DAILY_FREE_LIMIT)

        if limit_reached:
            st.error(f"⚠️ आपकी आज की फ्री लिमिट ({DAILY_FREE_LIMIT} मैसेज) समाप्त हो गई है!")

        if prompt := st.chat_input("AI से कुछ भी पूछें...", disabled=limit_reached):
            with st.chat_message("user"):
                st.write(prompt)
            save_chat_message(user_email, "user", prompt, "user")

            try:
                groq_client = get_groq_client(0)
                current_messages = [{"role": "system", "content": "You are a helpful AI assistant."}]
                for m in user_history:
                    current_messages.append({"role": m["role"], "content": m["content"]})
                current_messages.append({"role": "user", "content": prompt})

                response = groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=current_messages
                )
                bot_res = response.choices[0].message.content
                
                with st.chat_message("assistant"):
                    st.write(bot_res)
                save_chat_message(user_email, "assistant", bot_res, "user")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # 🎨 AI IMAGE GENERATOR PAGE (Ultra HD Quality Upgrade)
    elif st.session_state.current_page == "🎨 AI Image Generator":
        st.subheader("🎨 AI HD Image Generator")
        st.write("अपनी कल्पना लिखें, स्टाइल और साइज चुनें और **Ultra HD** फोटो जनरेट करें:")

        img_prompt = st.text_area("फोटो का विवरण (Prompt):", placeholder="A futuristic cyberpunk city with flying cars at night, highly detailed")
        
        col1, col2 = st.columns(2)
        with col1:
            ratio_option = st.selectbox(
                "📐 Aspect Ratio (साइज)", 
                ["Square (1:1)", "Landscape (16:9 - YouTube/PC)", "Portrait (9:16 - Insta/Shorts)"]
            )
            if "16:9" in ratio_option:
                width, height = 1280, 720
            elif "9:16" in ratio_option:
                width, height = 720, 1280
            else:
                width, height = 1024, 1024

        with col2:
            style_option = st.selectbox(
                "✨ Art Style (स्टाइल)", 
                ["Cinematic (मूवी जैसा)", "Realistic Photo (असली फोटो)", "Anime / Manga", "3D Pixar / Cartoon", "Digital Art", "Cyberpunk", "None (Normal)"]
            )

        if st.button("Generate HD Image 🚀", type="primary", use_container_width=True):
            if img_prompt.strip():
                with st.spinner("AI 4K Ultra HD में आपकी फोटो तैयार कर रहा है..."):
                    # Quality Booster Tags
                    quality_boosters = "masterpiece, 8k resolution, highly detailed, sharp focus, professional photography"
                    
                    if style_option != "None (Normal)":
                        final_prompt = f"{img_prompt}, {style_option} style, {quality_boosters}"
                    else:
                        final_prompt = f"{img_prompt}, {quality_boosters}"

                    encoded_prompt = urllib.parse.quote(final_prompt)
                    
                    # Flux Model + HD Parameters
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&model=flux&enhance=true&nologo=true"
                    
                    st.image(image_url, caption=f"Prompt: {img_prompt}", use_column_width=True)
                    st.success("✨ HD इमेज सफलतापूर्वक तैयार है! फोटो पर लॉन्ग प्रेस करके डाउनलोड कर सकते हैं।")
            else:
                st.warning("कृपया पहले फोटो का विवरण (Prompt) दर्ज करें!")

    # 👑 ADMIN ASSISTANT PAGE
    elif st.session_state.current_page == "👑 Admin Assistant" and is_admin:
        st.subheader("👑 Admin AI Assistant")

        admin_history = load_chat_history(user_email, "admin")
        for msg in admin_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        if prompt := st.chat_input("Admin Assistant से कुछ भी चेंज या हेल्प मांगें..."):
            with st.chat_message("user"):
                st.write(prompt)
            save_chat_message(user_email, "user", prompt, "admin")

            sys_prompt = f"You are an Admin Assistant for AI Studio App. Rules: '{st.session_state.pricing_rules}'."
            
            try:
                groq_client = get_groq_client(0)
                current_messages = [{"role": "system", "content": "You are a helpful assistant."}]
                for m in admin_history:
                    current_messages.append({"role": m["role"], "content": m["content"]})
                current_messages.append({"role": "user", "content": prompt})

                response = groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=current_messages
                )
                bot_res = response.choices[0].message.content
                
                with st.chat_message("assistant"):
                    st.write(bot_res)
                save_chat_message(user_email, "assistant", bot_res, "admin")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # ⚙️ APP SETTINGS PAGE
    elif st.session_state.current_page == "⚙️ App Settings" and is_admin:
        st.subheader("⚙️ App Pricing & Rules Control")
        st.write("**Current Rules:**", st.session_state.pricing_rules)

        st.write("---")
        new_rules = st.text_area("नये नियम या Pricing एडिट करें:", st.session_state.pricing_rules)
        if st.button("Save Rules", type="primary"):
            st.session_state.pricing_rules = new_rules
            st.success("ऐप के नियम अपडेट हो गए!")
