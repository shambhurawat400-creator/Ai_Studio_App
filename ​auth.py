import streamlit as st
import time

def handle_login_session(supabase):
    query_params = st.query_params
    if "user" not in st.session_state:
        if "logged_email" in query_params:
            class SavedUser:
                def __init__(self, email):
                    self.email = email
            st.session_state.user = SavedUser(query_params["logged_email"])

def render_auth_ui(supabase):
    st.title("🚀 Welcome to AI Studio")
    tab1, tab2 = st.tabs(["🔒 Login", "📝 Sign Up"])

    with tab1:
        st.subheader("Login to your account")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Log In", type="primary"):
            if email and password:
                with st.spinner("लॉगिन हो रहा है..."):
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        st.session_state.user = res.user
                        st.session_state.current_page = "🏠 Dashboard"
                        st.query_params["logged_email"] = res.user.email
                        st.success("सफलतापूर्वक लॉगिन हो गया! 🎉")
                        time.sleep(1)
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
                with st.spinner("अकाउंट बन रहा है..."):
                    try:
                        res = supabase.auth.sign_up({"email": new_email, "password": new_password})
                        st.success("अकाउंट बन गया! अब लॉगिन करें।")
                    except Exception as e:
                        st.error(f"साइन अप में त्रुटि: {str(e)}")
            else:
                st.warning("कृपया ईमेल और पासवर्ड भरें।")

def logout_user(supabase):
    if "logged_email" in st.query_params:
        del st.query_params["logged_email"]
    if "user" in st.session_state:
        del st.session_state["user"]
    st.session_state.current_page = "🏠 Dashboard"
    supabase.auth.sign_out()
    time.sleep(1)
    st.rerun()
