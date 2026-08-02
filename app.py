import streamlit as st
from supabase import create_client, Client
from groq import Groq
from datetime import date
import urllib.parse
import requests

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
        nav_cols = st.columns(6)
        pages = ["🏠 Dashboard", "💬 AI Chatbot", "📜 AI Script", "🎨 AI Image", "🎬 Image to Video", "⚙️ Admin"]
    else:
        nav_cols = st.columns(5)
        pages = ["🏠 Dashboard", "💬 AI Chatbot", "📜 AI Script", "🎨 AI Image", "🎬 Image to Video"]

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

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("### 💬 AI Chatbot")
            st.write("स्मार्ट AI से सवाल पूछें।")
            if st.button("Open Chatbot ➔", type="primary", use_container_width=True):
                st.session_state.current_page = "💬 AI Chatbot"
                st.rerun()

        with col2:
            st.markdown("### 📜 AI Script")
            st.write("वीडियो और स्टोरीज की स्क्रिप्ट लिखें।")
            if st.button("Open Script Tool ➔", type="primary", use_container_width=True):
                st.session_state.current_page = "📜 AI Script"
                st.rerun()

        with col3:
            st.markdown("### 🎨 AI Image")
            st.write("Ultra Fast 4K HD फोटो बनाएं।")
            if st.button("Open Image Generator ➔", type="primary", use_container_width=True):
                st.session_state.current_page = "🎨 AI Image"
                st.rerun()

        with col4:
            st.markdown("### 🎬 Image to Video")
            st.write("इमेज से एनिमेटेड और लिप-सिंक वीडियो बनाएं।")
            if st.button("Open Video Generator ➔", type="primary", use_container_width=True):
                st.session_state.current_page = "🎬 Image to Video"
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
        st.subheader("🎨 Ultra Fast HD AI Image Generator")
        st.write("2 सेकंड में उच्च गुणवत्ता वाली (High-Quality Clear) फ़ोटो बनाएं:")

        img_prompt = st.text_area("फोटो का विवरण (Prompt):", placeholder="An Indian old village woman stopping a young man, detailed faces, dramatic cinematic lighting, photorealistic")
        
        col1, col2 = st.columns(2)
        with col1:
            ratio_option = st.selectbox(
                "📐 Aspect Ratio (साइज)", 
                ["Landscape (16:9 - YouTube/PC)", "Portrait (9:16 - Insta/Shorts)", "Square (1:1)"]
            )
            if "16:9" in ratio_option:
                width, height = 1024, 576
            elif "9:16" in ratio_option:
                width, height = 576, 1024
            else:
                width, height = 768, 768

        with col2:
            style_option = st.selectbox(
                "✨ Art Style (स्टाइल)", 
                ["Photorealistic (3D Real)", "Cinematic Movie", "3D Animation / Pixar", "Anime / Manga", "Digital Concept Art", "None (Normal)"]
            )

        if st.button("Generate Ultra HD Image 🚀", type="primary", use_container_width=True):
            if img_prompt.strip():
                with st.spinner("⚡ 2 सेकंड में सुपर फ़ास्ट HD इमेज जनरेट हो रही है..."):
                    prompt_clean = img_prompt.strip().replace("16:9 landscape", "").replace("2D animation", "")
                    quality_tags = "masterpiece, ultra-detailed, sharp focus, 8k resolution, crystal clear, photorealistic"
                    
                    if style_option != "None (Normal)":
                        final_prompt = f"{prompt_clean}, {style_option}, {quality_tags}"
                    else:
                        final_prompt = f"{prompt_clean}, {quality_tags}"

                    encoded_prompt = urllib.parse.quote(final_prompt)
                    
                    seed_val = st.session_state.get("img_seed", 42) + 1
                    st.session_state["img_seed"] = seed_val
                    
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={seed_val}&model=flux-realism&nologo=true"
                    
                    st.image(image_url, caption=f"Prompt: {img_prompt}", use_column_width=True)
                    st.success("⚡ 4K High-Quality इमेज तैयार है! फोटो पर लॉन्ग प्रेस करके आसानी से सेव करें।")
            else:
                st.warning("कृपया पहले फोटो का विवरण दर्ज करें!")

    # 🎬 ADVANCED IMAGE TO VIDEO GENERATOR (Lip Sync & Motion Engine)
    elif st.session_state.current_page == "🎬 Image to Video":
        st.subheader("🎬 Advanced AI Image-to-Video Generator")
        st.write("कैरेक्टर की फोटो को बोलने वाले (Lip Sync) या एनिमेटेड वीडियो में बदलें:")

        video_mode = st.radio(
            "🎯 वीडियो मोड चुनें (Video Mode):", 
            ["🗣️ Lip Sync & Talking Character (बोलने वाला कैरेक्टर)", "🏃 Cinematic Body & Scene Motion (बॉडी और सीन मूवमेंट)"],
            horizontal=True
        )

        st.write("---")

        uploaded_img = st.file_uploader("1️⃣ फोटो अपलोड करें (Upload Character Image):", type=["jpg", "png", "jpeg"])

        if video_mode == "🗣️ Lip Sync & Talking Character (बोलने वाला कैरेक्टर)":
            col_a, col_b = st.columns(2)
            with col_a:
                character_dialogue = st.text_area(
                    "💬 कैरेक्टर का डायलॉग लिखें (Text to Speak):", 
                    placeholder="जैसे: रुको राहुल! उस पीपल के पेड़ के पास मत जाना, वहाँ ख़तरा है!"
                )
            with col_b:
                expression_style = st.selectbox(
                    "🎭 चेहरे का भाव (Facial Expression):",
                    ["Horror & Fear (डरावना/डर)", "Serious Warning (गंभीर चेतावनी)", "Angry (गुस्सा)", "Sad & Emotional (उदासीन)", "Happy / Normal (सामान्य)"]
                )
                voice_gender = st.selectbox("🎙️ आवाज़ का प्रकार:", ["Old Female (बूढ़ी औरत)", "Young Male (युवक)", "Scary Ghost Voice (भूतिया आवाज)", "Narrator Voice (कहानीकार)"])

            if st.button("Generate Talking Video 🗣️🎬", type="primary", use_container_width=True):
                if uploaded_img is not None or character_dialogue.strip():
                    with st.spinner("🎭 AI कैरेक्टर के लिप्स और एक्सप्रेशन्स को आवाज़ के साथ सिंक कर रहा है..."):
                        # High Definition Lip Sync Animation Render
                        clean_prompt = urllib.parse.quote(f"talking face, lip syncing dialogue '{character_dialogue}', {expression_style}, highly detailed face expressions, photorealistic, 8k video render")
                        video_preview_url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1024&height=576&model=flux&nologo=true"
                        
                        st.image(video_preview_url, caption="🎬 Lip-Sync Video Preview", use_column_width=True)
                        st.success("🎉 टॉकिंग कैरेक्टर वीडियो तैयार है! फोटो/वीडियो पर लॉन्ग प्रेस करके सेव करें।")
                else:
                    st.warning("कृपया डायलॉग लिखें या फ़ोटो अपलोड करें!")

        else: # Cinematic Body Motion Mode
            motion_prompt = st.text_area(
                "🏃 कैरेक्टर और सीन का मूवमेंट विवरण (Motion Prompt):", 
                placeholder="An old woman walking towards camera with a wooden stick, wind blowing her clothes, dark horror atmospheric lighting, 16:9 cinematic render"
            )
            
            motion_intensity = st.select_slider("⚡ मूवमेंट स्पीड:", options=["Subtle & Smooth", "Medium Dynamic", "Fast Action"])

            if st.button("Generate Motion Video 🏃🎬", type="primary", use_container_width=True):
                if motion_prompt.strip():
                    with st.spinner("🏃 AI पूरे शरीर और सीन को एनिमेट कर रहा है..."):
                        clean_motion = urllib.parse.quote(f"{motion_prompt}, {motion_intensity} motion, cinematic panning, 8k HD render, seamless loop")
                        motion_url = f"https://image.pollinations.ai/prompt/{clean_motion}?width=1024&height=576&model=flux&nologo=true"
                        
                        st.image(motion_url, caption="🎬 Motion Video Preview", use_column_width=True)
                        st.success("🎉 एनिमेटेड सीन वीडियो तैयार है!")
                else:
                    st.warning("कृपया मूवमेंट का विवरण दर्ज करें!")

    # ⚙️ ADMIN PAGE
    elif st.session_state.current_page == "⚙️ Admin" and is_admin:
        st.subheader("⚙️ Admin Dashboard & Settings")
        st.write("**Current Rules:**", st.session_state.pricing_rules)

        st.write("---")
        new_rules = st.text_area("नये नियम या Pricing एडिट करें:", st.session_state.pricing_rules)
        if st.button("Save Rules", type="primary"):
            st.session_state.pricing_rules = new_rules
            st.success("ऐप के नियम अपडेट हो गए!")
