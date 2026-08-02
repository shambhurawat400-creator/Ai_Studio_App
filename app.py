import streamlit as st
from supabase import create_client, Client

# Page Configuration
st.set_page_config(page_title="AI Studio - Login", page_icon="🔐", layout="centered")

# Supabase Credentials
SUPABASE_URL = "https://mrhjuxvgluansxrysuoy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1yaGp1eHZnbHVhbnN4cnlzdW95Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODU1ODc1NDgsImV4cCI6MjEwMTE2MzU0OH0.0Jq0cHTK16k2aN16p8n0HCU0zkritn2xgoHOeiq1a1U"

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Session State Management
if "user" not in st.session_state:
    st.session_state.user = None

st.title("🚀 Welcome to AI Studio")

if st.session_state.user is None:
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
                st.warning("कृपया ईमेल और पासवर्ड दोनों भरें।")

    with tab2:
        st.subheader("Create a new account")
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_pass")
        
        if st.button("Sign Up"):
            if new_email and new_password:
                try:
                    res = supabase.auth.sign_up({"email": new_email, "password": new_password})
                    st.success("अकाउंट बन गया है! यदि ईमेल कन्फर्मेशन ऑन है, तो अपनी ईमेल जाँचें।")
                except Exception as e:
                    st.error(f"साइन अप में त्रुटि: {str(e)}")
            else:
                st.warning("कृपया ईमेल और पासवर्ड भरें।")

else:
    st.success(f"आपका स्वागत है, **{st.session_state.user.email}**!")
    st.write("---")
    st.write("🎉 **आप Supabase से सफलतापूर्वक ऑथेंटिकेट हो चुके हैं!**")
    
    if st.button("Log Out", type="secondary"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()
