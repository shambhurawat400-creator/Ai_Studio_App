import streamlit as st
from supabase import create_client, Client
from groq import Groq
from datetime import date
import urllib.parse

# Page Configuration
st.set_page_config(page_title="AI Studio", page_icon="🤖", layout="wide")

# Credentials
SUPABASE_URL = "https://mrhjuxvgluansxrysuoy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1yaGp1eHZnbHVhbnN4cnlzdW95Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODU1ODc1NDgsImV4cCI6MjEwMTE2MzU0OH0.0Jq0cHTK16k2aN16p8n0HCU0zkritn2xgoHOeiq1a1U"

# Multiple Backup Groq API Keys list
GROQ_KEYS = [
    "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"
    # भविष्य में यहाँ अपनी दूसरी बैकअप Key जोड़ सकते हैं: "gsk_backup_key_2"
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

# Database Helper Functions
def load_chat_history(user_email, chat_type):
    try:
        res = supabase.table("user_chats") \
            .select("role, content") \
            .eq("user_email", user_email) \
            .eq("chat_type", chat_type) \
            .order("created_at", desc=False) \
            .execute()
        return res.data if res.data else []
    except Exception as e:
        return []

def save_chat_message(user_email, role, content, chat_type):
    try:
        supabase.table("user_chats").insert({
            "user_email": user_email,
            "role": role,
            "content": content,
            "chat_type": chat_type
        }).execute()
    except Exception as e:
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

# Session State Management
if "user" not in st.session_state:
    st.session_state.user = None

if "pricing_rules" not in st.session_state:
    st.session_state.pricing_rules = f"फ़्री प्लान: रोजाना अधिकतम {DAILY_FREE_LIMIT} मैसेज। प्रो प्लान: ₹199/महीना (अनलिमिटेड)।"

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
                    st.success("अकाउंट बन गया! इनबॉक्स चेक करें।")
                except Exception as e:
                    st.error(f"साइन अप में त्रुटि: {str(e)}")
            else:
                st.warning("कृपया ईमेल और पासवर्ड भरें।")

# Logged In Screen
else:
    user_email = st.session_state.user.email
    is_admin = user_email == ADMIN_EMAIL

    # Sidebar Navigation
    with st.sidebar:
        st.write(f"👤 **{user_email}**")
        if is_admin:
            st.success("👑 Role: Admin (Unlimited Access)")
            menu = st.radio("Navigation", ["👑 Admin Assistant", "🎨 AI Image Generator", "⚙️ Pricing & App Settings", "💬 AI Chatbot"])
        else:
            today_count = get_today_message_count(user_email)
            remaining = max(0, DAILY_FREE_LIMIT - today_count)
            st.info(f"👤 Role: Free User\n\n📊 **आज की लिमिट:** {today_count}/{DAILY_FREE_LIMIT} मैसेज (बचे: {remaining})")
            menu = st.radio("Navigation", ["💬 AI Chatbot", "🎨 AI Image Generator"])

        st.write("---")
        if st.button("Log Out", type="secondary"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    # Admin Only Views
    if is_admin and menu == "👑 Admin Assistant":
        st.title("👑 Admin AI Assistant")
        st.caption("यह असिस्टेंट आपकी बात Supabase में सुरक्षित रखता है।")

        admin_history = load_chat_history(user_email, "admin")
        for msg in admin_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        if prompt := st.chat_input("Admin Assistant से कुछ भी चेंज या हेल्प मांगें..."):
            with st.chat_message("user"):
                st.write(prompt)
            save_chat_message(user_email, "user", prompt, "admin")

            sys_prompt = f"You are an Admin Assistant for AI Studio App. Current Pricing Rules: '{st.session_state.pricing_rules}'. Assist the admin with app settings and configuration."
            
            try:
                groq_client = get_groq_client(0)
                current_messages = [{"role": "system", "content": sys_prompt}]
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

    # 🎨 AI Image Generator Tool
    elif menu == "🎨 AI Image Generator":
        st.title("🎨 AI Image Generator")
        st.subheader("अपनी कल्पना को फोटो में बदलें!")

        img_prompt = st.text_area("आपको कैसी फोटो बनानी है? (जैसे: A futuristic city with flying cars in 8k, photorealistic)")
        
        col1, col2 = st.columns(2)
        with col1:
            width = st.selectbox("चौड़ाई (Width)", [512, 768, 1024], index=2)
        with col2:
            height = st.selectbox("ऊंचाई (Height)", [512, 768, 1024], index=2)

        if st.button("Generate Image 🚀", type="primary"):
            if img_prompt.strip():
                with st.spinner("AI आपकी फोटो जनरेट कर रहा है..."):
                    encoded_prompt = urllib.parse.quote(img_prompt)
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
                    
                    st.image(image_url, caption=f"Prompt: {img_prompt}", use_column_width=True)
                    st.success("इमेज तैयार है! फोटो पर लॉन्ग प्रेस करके या राइट-क्लिक करके सेव कर सकते हैं।")
            else:
                st.warning("कृपया फोटो का प्रॉम्प्ट दर्ज करें!")

    elif is_admin and menu == "⚙️ Pricing & App Settings":
        st.title("⚙️ App Pricing & Rules Control")
        st.subheader("वर्तमान नियम (Current Rules):")
        st.write(st.session_state.pricing_rules)

        st.write("---")
        new_rules = st.text_area("नये नियम या Pricing एडिट करें:", st.session_state.pricing_rules)
        if st.button("Save Rules", type="primary"):
            st.session_state.pricing_rules = new_rules
            st.success("ऐप के नियम सफलतापूर्वक अपडेट हो गए!")

    # User Chatbot View
    elif menu == "💬 AI Chatbot":
        st.title("💬 AI Chat Assistant")

        with st.expander("ℹ️ Current App Rules & Pricing"):
            st.write(st.session_state.pricing_rules)

        user_history = load_chat_history(user_email, "user")
        for msg in user_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        today_count = get_today_message_count(user_email)
        limit_reached = (not is_admin) and (today_count >= DAILY_FREE_LIMIT)

        if limit_reached:
            st.error(f"⚠️ आपकी आज की फ्री लिमिट ({DAILY_FREE_LIMIT} मैसेज) समाप्त हो गई है! कृपया कल पुनः प्रयास करें या प्रो प्लान लें।")

        if prompt := st.chat_input("AI से कुछ भी पूछें...", disabled=limit_reached):
            with st.chat_message("user"):
                st.write(prompt)
            save_chat_message(user_email, "user", prompt, "user")

            try:
                groq_client = get_groq_client(0)
                current_messages = [{"role": "system", "content": "You are a helpful and smart AI assistant."}]
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
