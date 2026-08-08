"""
Authentication module (Pro Version)
--------------------------------------
Fixes vs the original:
- Session persistence now uses the real Supabase access/refresh tokens
  (verified server-side via supabase.auth.set_session), instead of trusting
  a bare email string from the URL — which anyone could fake by typing
  ?logged_email=someone@example.com in the address bar.
- Centralized, cached Supabase client creation with clear setup errors.
- A reusable account-menu widget (shows who's logged in + Logout).
"""

import logging
import time

import streamlit as st

logger = logging.getLogger(__name__)


@st.cache_resource(show_spinner=False)
def get_supabase_client():
    import os
    from supabase import create_client

    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        try:
            url = url or st.secrets.get("SUPABASE_URL", "")
            key = key or st.secrets.get("SUPABASE_KEY", "")
        except Exception:
            pass

    if not url or not key:
        return None

    try:
        return create_client(url, key)
    except Exception as e:
        logger.error("Failed to create Supabase client: %s", e)
        return None


def restore_session(supabase) -> None:
    """
    Called once per page load. If the browser still has valid tokens in the
    URL from a previous login, verify them with Supabase and restore the
    real authenticated user — instead of trusting an unverified email string.
    """
    if "user" in st.session_state:
        return

    qp = st.query_params
    access_token = qp.get("at")
    refresh_token = qp.get("rt")

    if not access_token or not refresh_token:
        return

    try:
        result = supabase.auth.set_session(access_token, refresh_token)
        if result and result.user:
            st.session_state.user = result.user
            st.session_state.access_token = access_token
            st.session_state.refresh_token = refresh_token
        else:
            _clear_session_query_params()
    except Exception as e:
        logger.info("Stored session invalid/expired, clearing: %s", e)
        _clear_session_query_params()


def _clear_session_query_params():
    for k in ("at", "rt"):
        if k in st.query_params:
            del st.query_params[k]


def render_auth_ui(supabase) -> None:
    if supabase is None:
        st.error("🚨 Supabase कनेक्ट नहीं हो पाया। `SUPABASE_URL` और `SUPABASE_KEY` secrets में सेट करें।")
        return

    st.title("🚀 Welcome to AI Studio")
    tab1, tab2 = st.tabs(["🔒 Login", "📝 Sign Up"])

    with tab1:
        st.subheader("Login to your account")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Log In", type="primary"):
            if not (email and password):
                st.warning("कृपया ईमेल और पासवर्ड भरें।")
            else:
                with st.spinner("लॉगिन हो रहा है..."):
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        st.session_state.user = res.user
                        st.session_state.access_token = res.session.access_token
                        st.session_state.refresh_token = res.session.refresh_token
                        st.session_state.current_page = "🏠 Dashboard"
                        # Store verified tokens (not a bare email) so a reload can restore the session securely
                        st.query_params["at"] = res.session.access_token
                        st.query_params["rt"] = res.session.refresh_token
                        st.success("सफलतापूर्वक लॉगिन हो गया! 🎉")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"लॉगिन में त्रुटि: {str(e)}")

    with tab2:
        st.subheader("Create a new account")
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password (कम से कम 8 characters)", type="password", key="signup_pass")
        confirm_password = st.text_input("Password दोबारा लिखें", type="password", key="signup_pass_confirm")

        if st.button("Sign Up"):
            if not (new_email and new_password and confirm_password):
                st.warning("कृपया सभी फ़ील्ड भरें।")
            elif len(new_password) < 8:
                st.warning("⚠️ Password कम से कम 8 characters का होना चाहिए।")
            elif new_password != confirm_password:
                st.warning("⚠️ दोनों Password match नहीं कर रहे।")
            else:
                with st.spinner("अकाउंट बन रहा है..."):
                    try:
                        supabase.auth.sign_up({"email": new_email, "password": new_password})
                        st.success("🎉 अकाउंट बन गया! अपना ईमेल check करें (verification link) फिर Login tab से लॉगिन करें।")
                    except Exception as e:
                        st.error(f"साइन अप में त्रुटि: {str(e)}")


def logout_user(supabase) -> None:
    _clear_session_query_params()
    for k in ("user", "access_token", "refresh_token"):
        if k in st.session_state:
            del st.session_state[k]
    st.session_state.current_page = "🏠 Dashboard"
    try:
        if supabase:
            supabase.auth.sign_out()
    except Exception as e:
        logger.warning("Sign-out call failed (session cleared locally anyway): %s", e)
    time.sleep(0.5)
    st.rerun()


def render_account_menu(supabase) -> None:
    """Small header widget: shows the logged-in user's email + a Logout button."""
    user = st.session_state.get("user")
    if not user:
        return
    col1, col2 = st.columns([4, 1])
    with col1:
        st.caption(f"👤 Logged in as **{user.email}**")
    with col2:
        if st.button("🚪 Logout", use_container_width=True):
            logout_user(supabase)
