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

    # Top Header & Logout
    head_col1, head_col2 = st.columns([5, 1])
    with head_col1:
        st.title("🤖 AI Studio Hub")
    with head_col2:
        if st.button("🚪 Log Out", type="secondary"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    # --- HORIZONTAL NAVIGATION BAR ---
    st.write("---")
    
    if is_admin:
        nav_cols = st.columns(5)
        pages = ["🏠 Dashboard", "💬 AI Chatbot", "📜 AI Script", "🎨 AI Image", "⚙️ Admin"]
    else:
        nav_cols = st.columns(4)
        pages = ["🏠 Dashboard", "💬 AI Chatbot", "📜 AI Script", "🎨 AI Image"]

    for i, page in enumerate(pages):
        btn_type = "primary" if st.session_state.current_page == page else "secondary"
        if nav_cols[i].button(page, type=btn_type, use_container_width=True):
            st.session_state.current_page = page
            st.rerun()

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

        st.write("### 🚀 Quick Access Tools")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### 💬 AI Chatbot")
            st.write("स्मार्ट AI से सवाल पूछें और बातचीत करें।")
            if st.button("Open Chatbot ➔", type="primary", use_container_width=True):
                st.session_state.current_page = "💬 AI Chatbot"
                st.rerun()

        with col2:
            st.markdown("### 📜 AI Script Generator")
            st.write("YouTube, Reels और स्टोरीज के लिए स्क्रिप्ट लिखें।")
            if st.button("Open Script Tool ➔", type="primary", use_container_width=True):
                st.session_state.current_page = "📜 AI Script"
                st.rerun()

        with col3:
            st.markdown("### 🎨 AI Image Generator")
            st.write("HD और स्टाइलिश इमेज बनाएं।")
            if st.button("Open Image Generator ➔", type="primary", use_container_width=True):
                st.session_state.current_page = "🎨 AI Image"
                st.rerun()

    # 💬 CHATBOT PAGE
    elif st.session_state.current_page == "💬 AI Chatbot":
        st.subheader("💬 AI Chat Assistant")

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

    # 📜 AI SCRIPT GENERATOR PAGE
    elif st.session_state.current_page == "📜 AI Script":
        st.subheader("📜 AI Video & Story Script Writer")
        st.write("अपने यूट्यूब वीडियो, रील्स या हॉरर स्टोरी की स्क्रिप्ट तैयार करें:")

        topic = st.text_input("स्क्रिप्ट का टॉपिक/विषय दर्ज करें:", placeholder="जैसे: Horror story near a haunted well in village")
        script_type = st.selectbox("स्क्रिप्ट का प्रकार (Type):", ["YouTube Video (Full Script)", "Instagram Reel / Shorts (60sec)", "Horror Story / Storytelling", "Educational / Business"])

        if st.button("Generate Script ✍️", type="primary", use_container_width=True):
            if topic.strip():
                with st.spinner("AI स्क्रिप्ट लिख रहा है..."):
                    try:
                        groq_client = get_groq_client(0)
                        prompt = f"Write a detailed {script_type} in Hindi/Hinglish on the topic: '{topic}'. Include scene details, narrator lines, and visual cues."
                        
                        response = groq_client.chat.completions.create(
                            model="llama-3.1-8b-instant",
                            messages=[{"role": "user", "content": prompt}]
                        )
                        script_res = response.choices[0].message.content
                        st.markdown("### 📝 Generated Script:")
                        st.text_area("आपकी स्क्रिप्ट:", value=script_res, height=350)
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.warning("कृपया पहले टॉपिक दर्ज करें!")

    # 🎨 AI IMAGE GENERATOR PAGE
    elif st.session_state.current_page == "🎨 AI Image":
        st.subheader("🎨 AI Image Generator")
        st.write("अपनी कल्पना लिखें, स्टाइल और साइज चुनें और फोटो जनरेट करें:")

        img_prompt = st.text_area("फोटो का विवरण (Prompt):", placeholder="A futuristic cyberpunk city with flying cars at night, highly detailed")
        
        col1, col2 = st.columns(2)
        with col1:
            ratio_option = st.selectbox(
                "📐 Aspect Ratio (साइज)", 
                ["Landscape (16:9 - YouTube/PC)", "Portrait (9:16 - Insta/Shorts)", "Square (1:1)"]
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
                ["Cinematic (मूवी जैसा)", "3D Pixar / Cartoon", "Realistic Photo", "Anime / Manga", "Digital Art", "Cyberpunk", "None (Normal)"]
            )

        if st.button("Generate Image 🚀", type="primary", use_container_width=True):
            if img_prompt.strip():
                with st.spinner("AI आपकी फोटो तैयार कर रहा है..."):
                    enhanced_prompt = img_prompt.strip()
                    if style_option != "None (Normal)":
                        enhanced_prompt += f", {style_option} style, highly detailed, 8k resolution"
                    else:
                        enhanced_prompt += ", highly detailed, 8k resolution"

                    encoded_prompt = urllib.parse.quote(enhanced_prompt)
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
                    
                    st.image(image_url, caption=f"Prompt: {img_prompt}", use_column_width=True)
                    st.success("✨ इमेज सफलतापूर्वक तैयार है! फोटो पर लॉन्ग प्रेस करके डाउनलोड कर सकते हैं।")
            else:
                st.warning("कृपया पहले फोटो का विवरण (Prompt) दर्ज करें!")

    # ⚙️ ADMIN PAGE
    elif st.session_state.current_page == "⚙️ Admin" and is_admin:
        st.subheader("⚙️ Admin Dashboard & Settings")
        st.write("**Current Rules:**", st.session_state.pricing_rules)

        st.write("---")
        new_rules = st.text_area("नये नियम या Pricing एडिट करें:", st.session_state.pricing_rules)
        if st.button("Save Rules", type="primary"):
            st.session_state.pricing_rules = new_rules
            st.success("ऐप के नियम अपडेट हो गए!")
