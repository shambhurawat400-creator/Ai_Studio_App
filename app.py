import streamlit as st
from supabase import create_client, Client
from groq import Groq

# Page Configuration
st.set_page_config(page_title="AI Studio", page_icon="🤖", layout="wide")

# Credentials
SUPABASE_URL = "https://mrhjuxvgluansxrysuoy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1yaGp1eHZnbHVhbnN4cnlzdW95Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODU1ODc1NDgsImV4cCI6MjEwMTE2MzU0OH0.0Jq0cHTK16k2aN16p8n0HCU0zkritn2xgoHOeiq1a1U"
GROQ_API_KEY = "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"

# Define Admin Email
ADMIN_EMAIL = "shambhurawat400@gmail.com"

# Initialize Clients
@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_resource
def init_groq() -> Groq:
    return Groq(api_key=GROQ_API_KEY)

supabase = init_supabase()
groq_client = init_groq()

# Session States
if "user" not in st.session_state:
    st.session_state.user = None

if "pricing_rules" not in st.session_state:
    st.session_state.pricing_rules = "फ़्री प्लान: अनलिमिटेड AI मैसेज। प्रीमियम प्लान: ₹199/महीना।"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "admin_messages" not in st.session_state:
    st.session_state.admin_messages = []

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
                    st.success("अकाउंट बन गया! यदि ईमेल वेरिफिकेशन ऑन है तो इनबॉक्स चेक करें।")
                except Exception as e:
                    st.error(f"साइन अप में त्रुटि: {str(e)}")
            else:
                st.warning("कृपया ईमेल और पासवर्ड भरें।")

# Logged In View
else:
    is_admin = st.session_state.user.email == ADMIN_EMAIL

    # Sidebar Navigation
    with st.sidebar:
        st.write(f"👤 **{st.session_state.user.email}**")
        if is_admin:
            st.success("👑 Role: Admin")
            menu = st.radio("Navigation", ["👑 Admin Assistant", "⚙️ Pricing & App Settings", "💬 AI Chatbot"])
        else:
            st.info("👤 Role: User")
            menu = st.radio("Navigation", ["💬 AI Chatbot"])

        st.write("---")
        if st.button("Log Out", type="secondary"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    # Admin Only Views
    if is_admin and menu == "👑 Admin Assistant":
        st.title("👑 Admin AI Assistant")
        st.info("यह असिस्टेंट सिर्फ आपको (Admin) दिख रहा है। इससे आप ऐप के नियम, सेटिंग्स या pricing बदलवा सकते हैं।")

        for msg in st.session_state.admin_messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        if prompt := st.chat_input("Admin Assistant से कुछ भी चेंज करने को कहें..."):
            st.session_state.admin_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            sys_prompt = f"You are an Admin Assistant for AI Studio App. Current Pricing Rules: '{st.session_state.pricing_rules}'. Assist the admin with app settings and configuration."
            
            try:
                response = groq_client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[{"role": "system", "content": sys_prompt}] + st.session_state.admin_messages
                )
                bot_res = response.choices[0].message.content
                st.session_state.admin_messages.append({"role": "assistant", "content": bot_res})
                with st.chat_message("assistant"):
                    st.write(bot_res)
            except Exception as e:
                st.error(f"Error: {str(e)}")

    elif is_admin and menu == "⚙️ Pricing & App Settings":
        st.title("⚙️ App Pricing & Rules Control")
        st.subheader("वर्तमान नियम (Current Rules):")
        st.write(st.session_state.pricing_rules)

        st.write("---")
        new_rules = st.text_area("नये नियम या Pricing एडिट करें:", st.session_state.pricing_rules)
        if st.button("Save Rules", type="primary"):
            st.session_state.pricing_rules = new_rules
            st.success("ऐप के नियम सफलतापूर्वक अपडेट हो गए!")

    # User Chatbot View (Visible to everyone)
    elif menu == "💬 AI Chatbot":
        st.title("💬 AI Chat Assistant")

        # Show current pricing info to users
        with st.expander("ℹ️ Current App Rules & Pricing"):
            st.write(st.session_state.pricing_rules)

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        if prompt := st.chat_input("AI से कुछ भी पूछें..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            try:
                response = groq_client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[{"role": "system", "content": "You are a helpful and smart AI assistant."}] + st.session_state.messages
                )
                bot_res = response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": bot_res})
                with st.chat_message("assistant"):
                    st.write(bot_res)
            except Exception as e:
                st.error(f"Error: {str(e)}")
