"""
Admin AI Assistant (Pro Version)
------------------------------------
Visible ONLY to the configured admin email.
"""

import json
import logging
import re
import streamlit as st

logger = logging.getLogger(__name__)

ADMIN_EMAIL = "shambhurawat400@gmail.com"

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

def render_admin_assistant_page(supabase, groq_client) -> None:
    st.subheader("🛠️ Admin Control Assistant")
    st.caption("Sirf admin ke liye active.")

    if not groq_client:
        st.error("🚨 GROQ_API_KEY set nahi hai.")
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
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for m in st.session_state.admin_chat_messages[-10:]:
                messages.append({"role": m["role"], "content": m["content"]})

            # Using latest active groq model matching script module stability
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=500,
                temperature=0.3,
            )
            raw = response.choices[0].message.content.strip()
            
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
