"""
Admin AI Assistant (Gemini Powered Version)
------------------------------------
Visible ONLY to the configured admin email.
"""

import json
import logging
import re
import streamlit as st
from google import genai

logger = logging.getLogger(__name__)

ADMIN_EMAIL = "shambhurawat400@gmail.com"
GEMINI_MODEL_NAME = "gemini-3.5-flash-lite"

FEATURE_KEYS = {
    "chatbot": "💬 AI Chatbot",
    "script": "📜 AI Script",
    "voice": "🎙️ Voice Studio",
    "image": "🎨 AI Image",
    "video": "🎬 Image to Video",
}

KNOWN_CONFIG_KEYS = {
    "app_title": "App ke header mein dikhne wala title",
    "dashboard_welcome": "Dashboard page ka welcome heading",
    "dashboard_info_banner": "Dashboard ke top wala info message",
    "pricing_rules": "Pricing/plan details",
    "custom_notice": "Koi bhi announcement/notice",
    "maintenance_message": "Jab koi feature band ho",
    "pro_price_inr": "Pro plan ki price",
    "upi_id": "Admin ki UPI ID",
}

SYSTEM_PROMPT = f"""You are the Admin Control Assistant for AI Studio Hub.
Respond with STRICT JSON ONLY — no markdown, no code fences.

Schema:
1. {{"action": "set_config", "key": "<config_key>", "value": "<new value>", "reply": "<short Hindi/Hinglish explanation>"}}
2. {{"action": "set_feature_flag", "feature": "<chatbot|script|voice|image|video>", "enabled": true/false, "reply": "<short explanation>"}}
3. {{"action": "none", "reply": "<your reply>"}}
"""

def get_gemini_client():
    import os
    api_key = None
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        logger.error("Failed to init Gemini client: %s", e)
        return None

def is_admin(user) -> bool:
    return bool(user) and getattr(user, "email", "").strip().lower() == ADMIN_EMAIL.lower()

def _load_all_config(supabase) -> dict:
    if "app_config" in st.session_state:
        return st.session_state.app_config
    config = {}
    try:
        res = supabase.table("app_config").select("*").execute()
        for row in res.data:
            config[row["key"]] = row["value"]
    except Exception as e:
        logger.info("Could not load app_config: %s", e)
    st.session_state.app_config = config
    return config

def get_config(supabase, key: str, default: str = "") -> str:
    return _load_all_config(supabase).get(key, default)

def is_feature_enabled(supabase, feature_key: str) -> bool:
    config = _load_all_config(supabase)
    flags = config.get("_feature_flags", {})
    if isinstance(flags, str):
        try:
            flags = json.loads(flags)
        except Exception:
            flags = {}
    return flags.get(feature_key, True)

def _save_config(supabase, key: str, value) -> bool:
    try:
        supabase.table("app_config").upsert({"key": key, "value": value}).execute()
        config = _load_all_config(supabase)
        config[key] = value
        st.session_state.app_config = config
        return True
    except Exception as e:
        st.error(f"🚨 Save nahi ho paya: {e}")
        return False

def _set_feature_flag(supabase, feature_key: str, enabled: bool) -> bool:
    config = _load_all_config(supabase)
    flags = config.get("_feature_flags", {})
    if isinstance(flags, str):
        try:
            flags = json.loads(flags)
        except Exception:
            flags = {}
    flags = dict(flags)
    flags[feature_key] = enabled
    return _save_config(supabase, "_feature_flags", flags)

def render_admin_assistant_page(supabase, groq_client=None) -> None:
    st.subheader("🛠️ Admin Control Assistant")
    st.caption("Sirf admin ke liye active (Powered by Gemini).")

    client = get_gemini_client()
    if not client:
        st.error("🚨 GEMINI_API_KEY set nahi hai.")
        return

    if "admin_chat_messages" not in st.session_state:
        st.session_state.admin_chat_messages = []
    if "admin_pending_action" not in st.session_state:
        st.session_state.admin_pending_action = None

    for msg in st.session_state.admin_chat_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    pending = st.session_state.admin_pending_action
    if pending:
        st.info(f"📋 **Proposed change:** {pending.get('reply', '')}")
        st.json({k: v for k, v in pending.items() if k != "reply"})
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✅ Apply Karo", type="primary", use_container_width=True):
                if pending.get("action") == "set_config":
                    _save_config(supabase, pending["key"], pending["value"])
                elif pending.get("action") == "set_feature_flag":
                    _set_feature_flag(supabase, pending["feature"], bool(pending["enabled"]))
                st.success("✅ Apply ho gaya!")
                st.session_state.admin_pending_action = None
                st.rerun()
        with col_b:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.admin_pending_action = None
                st.rerun()
        return

    if prompt := st.chat_input("Jo bhi badalna hai, likho..."):
        st.session_state.admin_chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        try:
            contents = [SYSTEM_PROMPT]
            for m in st.session_state.admin_chat_messages[-10:]:
                role_prefix = "User: " if m["role"] == "user" else "Model: "
                contents.append(role_prefix + m["content"])

            response = client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents="\n\n".join(contents),
                config={"temperature": 0.3, "max_output_tokens": 500}
            )
            raw = response.text.strip()
            
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
            else:
                raise json.JSONDecodeError("Invalid JSON", raw, 0)

            reply = parsed.get("reply", "Samajh nahi aaya.")
            with st.chat_message("assistant"):
                st.write(reply)
            st.session_state.admin_chat_messages.append({"role": "assistant", "content": reply})

            if parsed.get("action") in ("set_config", "set_feature_flag"):
                st.session_state.admin_pending_action = parsed
                st.rerun()

        except Exception as e:
            error_msg = f"⚠️ Error: {str(e)}"
            with st.chat_message("assistant"):
                st.write(error_msg)
            st.session_state.admin_chat_messages.append({"role": "assistant", "content": error_msg})
