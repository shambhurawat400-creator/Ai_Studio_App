"""
Settings page (Pro Version)
------------------------------
- Profile info (email, account created date)
- Change password
- App preferences (default language, default style) — saved to Supabase
  per-user so they persist across devices/sessions
- Personal API key overrides — SESSION-ONLY (not saved to any database),
  clearly explained, so users aren't misled into thinking secrets are
  being stored somewhere.
"""

import streamlit as st


DEFAULT_PREFS = {
    "default_language": "🇮🇳 Hindi (हिन्दी)",
    "default_style": "Indian Storybook Illustration (बेस्ट)",
}


def _load_prefs(supabase, user_id: str) -> dict:
    if "user_prefs" in st.session_state:
        return st.session_state.user_prefs

    prefs = dict(DEFAULT_PREFS)
    try:
        res = supabase.table("user_settings").select("*").eq("user_id", user_id).limit(1).execute()
        if res.data:
            prefs.update(res.data[0].get("prefs", {}))
    except Exception:
        pass  # Table may not exist yet — fall back to defaults silently

    st.session_state.user_prefs = prefs
    return prefs


def _save_prefs(supabase, user_id: str, prefs: dict) -> bool:
    try:
        supabase.table("user_settings").upsert({"user_id": user_id, "prefs": prefs}).execute()
        st.session_state.user_prefs = prefs
        return True
    except Exception as e:
        st.warning(
            f"⚠️ Preferences cloud मे save नहीं हो पाईं ({e}). इस session के लिए local रहेंगी। "
            "(Supabase में `user_settings` table बनानी होगी: columns `user_id` text primary key, `prefs` jsonb)"
        )
        st.session_state.user_prefs = prefs
        return False


def render_settings_page(supabase) -> None:
    st.subheader("⚙️ Settings")

    user = st.session_state.get("user")
    if not user:
        st.error("आप लॉगिन नहीं हैं।")
        return

    # --- Profile ---
    st.markdown("### 👤 Profile")
    st.write(f"**Email:** {user.email}")
    created_at = getattr(user, "created_at", None)
    if created_at:
        st.write(f"**Member since:** {str(created_at)[:10]}")

    with st.expander("🔑 Password बदलें"):
        new_pw = st.text_input("नया Password (कम से कम 8 characters)", type="password", key="settings_new_pw")
        confirm_pw = st.text_input("नया Password दोबारा लिखें", type="password", key="settings_confirm_pw")
        if st.button("Password Update करें"):
            if len(new_pw) < 8:
                st.warning("⚠️ Password कम से कम 8 characters का होना चाहिए।")
            elif new_pw != confirm_pw:
                st.warning("⚠️ दोनों Password match नहीं कर रहे।")
            else:
                try:
                    supabase.auth.update_user({"password": new_pw})
                    st.success("✅ Password update हो गया!")
                except Exception as e:
                    st.error(f"Error: {e}")

    st.markdown("---")

    # --- Preferences ---
    st.markdown("### 🎛️ App Preferences")
    prefs = _load_prefs(supabase, user.id)

    lang_options = [
        "🇮🇳 Hindi (हिन्दी)", "🇮🇳 English (भारतीय अंग्रेज़ी)", "🇺🇸 English (US)",
        "🇧🇩 Bengali (বাংলা)", "🇮🇳 Marathi (मराठी)", "🇮🇳 Tamil (தமிழ்)",
        "🇮🇳 Telugu (తెలుగు)", "🇮🇳 Gujarati (ગુજરાતી)", "🇫🇷 French (Français)",
    ]
    style_options = [
        "Indian Storybook Illustration (बेस्ट)", "2D Animation / Cartoon",
        "Cinematic Story Frame", "Classic Oil Painting", "Watercolor Art",
    ]

    default_language = st.selectbox(
        "🌐 Default Language:", lang_options,
        index=lang_options.index(prefs.get("default_language", DEFAULT_PREFS["default_language"])) if prefs.get("default_language") in lang_options else 0,
    )
    default_style = st.selectbox(
        "🎨 Default Image Style:", style_options,
        index=style_options.index(prefs.get("default_style", DEFAULT_PREFS["default_style"])) if prefs.get("default_style") in style_options else 0,
    )

    if st.button("💾 Preferences Save करें", type="primary"):
        new_prefs = {"default_language": default_language, "default_style": default_style}
        if _save_prefs(supabase, user.id, new_prefs):
            st.success("✅ Preferences save ho gayi!")

    st.markdown("---")

    # --- Personal API keys (session-only) ---
    st.markdown("### 🔐 अपनी खुद की API Keys (Optional)")
    st.caption(
        "⚠️ Security के लिए ये keys कहीं save नहीं होतीं — sirf is browser session ke liye yaad rahengi. "
        "Page reload/logout hone par dobara daalni hongi."
    )

    current_keys = st.session_state.get("active_api_keys", {})
    groq_key_input = st.text_input(
        "अपनी Groq API Key (optional, apni quota use karne ke liye):",
        value=current_keys.get("GROQ_KEY", "") if current_keys.get("GROQ_KEY", "").startswith("gsk_") else "",
        type="password",
    )
    gemini_key_input = st.text_input(
        "अपनी Gemini API Key (optional, Nano Banana ke liye):",
        value=current_keys.get("GEMINI_KEY", ""),
        type="password",
    )

    if st.button("🔐 API Keys Update करें (session only)"):
        st.session_state.active_api_keys = {
            **st.session_state.get("active_api_keys", {}),
            "GROQ_KEY": groq_key_input.strip(),
            "GEMINI_KEY": gemini_key_input.strip(),
        }
        st.success("✅ Keys is session ke liye set ho gayi.")
