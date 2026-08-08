"""
Admin AI Assistant (Pro Version)
------------------------------------
Visible ONLY to the configured admin email. Lets the admin describe a
desired app change in plain Hindi/English, and the assistant proposes a
concrete config change (app title, dashboard message, pricing text,
turning a tool on/off for maintenance, or any custom key/value setting).
Nothing is applied automatically — every proposed change is shown for
explicit confirmation before it's written to Supabase (so all users see
it), which prevents an accidental/misunderstood instruction from breaking
the live app.
"""

import json
import logging

import streamlit as st

logger = logging.getLogger(__name__)

ADMIN_EMAIL = "shambhurawat400@gmail.com"

# Known feature flags that gate which nav buttons show up for normal users.
FEATURE_KEYS = {
    "chatbot": "💬 AI Chatbot",
    "script": "📜 AI Script",
    "voice": "🎙️ Voice Studio",
    "image": "🎨 AI Image",
    "video": "🎬 Image to Video",
}

# Well-known config keys the admin can set via plain text (any other custom
# key is also allowed — this list is just what the assistant is told about).
KNOWN_CONFIG_KEYS = {
    "app_title": "App ke header mein dikhne wala title (e.g. '🤖 AI Studio Hub')",
    "dashboard_welcome": "Dashboard page ka welcome heading",
    "dashboard_info_banner": "Dashboard ke top wala info message",
    "pricing_rules": "Pricing/plan details — ye 'Pricing' page mein sabko dikhta hai",
    "custom_notice": "Koi bhi announcement/notice jo Dashboard ke top pe sabko dikhna chahiye",
    "maintenance_message": "Jab koi feature band ho to users ko dikhne wala message",
}

SYSTEM_PROMPT = f"""You are the Admin Control Assistant for a Streamlit app called AI Studio Hub.
The admin will describe changes they want to make to the LIVE app in Hindi/Hinglish/English.
You must respond with STRICT JSON ONLY — no markdown, no code fences, no extra text before or after.

JSON schema (pick exactly one action):
1. Changing a text setting (title, dashboard message, pricing text, or any custom text setting):
   {{"action": "set_config", "key": "<config_key>", "value": "<new value>", "reply": "<short Hindi/Hinglish explanation of what you're proposing>"}}
   Known keys: {json.dumps(KNOWN_CONFIG_KEYS, ensure_ascii=False)}
   If the admin wants something not in this list, invent a short snake_case key for it.

2. Turning a tool/feature on or off for all users (maintenance mode for a specific tool):
   {{"action": "set_feature_flag", "feature": "<one of: chatbot, script, voice, image, video>", "enabled": true or false, "reply": "<short explanation>"}}

3. Just answering/clarifying without changing anything (e.g. admin asked a question, or the request is ambiguous):
   {{"action": "none", "reply": "<your Hindi/Hinglish reply or clarifying question>"}}

Rules:
- Only ever propose ONE change per response. If the admin asks for multiple things, handle the first and mention in "reply" that they should ask for the rest separately.
- Never invent feature names outside the known list for set_feature_flag.
- Keep "reply" short (1-3 sentences), in Hindi/Hinglish, clearly stating what will change.
- Output must be valid JSON — nothing else.
"""


def is_admin(user) -> bool:
    return bool(user) and getattr(user, "email", "").strip().lower() == ADMIN_EMAIL.lower()


# ---------------------------------------------------------------------------
# Config storage (Supabase-backed, cached per session)
# ---------------------------------------------------------------------------

def _load_all_config(supabase) -> dict:
    if "app_config" in st.session_state:
        return st.session_state.app_config

    config = {}
    try:
        res = supabase.table("app_config").select("*").execute()
        for row in res.data:
            config[row["key"]] = row["value"]
    except Exception as e:
        logger.info("Could not load app_config (table may not exist yet): %s", e)

    st.session_state.app_config = config
    return config


def get_config(supabase, key: str, default: str = "") -> str:
    config = _load_all_config(supabase)
    return config.get(key, default)


def is_feature_enabled(supabase, feature_key: str) -> bool:
    config = _load_all_config(supabase)
    flags = config.get("_feature_flags", {})
    if isinstance(flags, str):
        try:
            flags = json.loads(flags)
        except Exception:
            flags = {}
    return flags.get(feature_key, True)  # default: enabled


def _save_config(supabase, key: str, value) -> bool:
    try:
        supabase.table("app_config").upsert({"key": key, "value": value}).execute()
        config = _load_all_config(supabase)
        config[key] = value
        st.session_state.app_config = config
        return True
    except Exception as e:
        st.error(
            f"🚨 Save नहीं हो पाया: {e}\n\n"
            "Supabase में `app_config` table बनानी होगी: columns `key` text primary key, `value` jsonb"
        )
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


# ---------------------------------------------------------------------------
# Assistant page
# ---------------------------------------------------------------------------

def render_admin_assistant_page(supabase, groq_client) -> None:
    st.subheader("🛠️ Admin Control Assistant")
    st.caption("Sirf tumhe (admin) dikhta hai. Jo bhi change chahiye plain Hindi/English mein likho — main propose karunga, tum confirm karoge, tabhi live app pe apply hoga.")

    if not groq_client:
        st.error("🚨 GROQ_API_KEY set nahi hai — Settings ya app secrets mein daalo.")
        return

    with st.expander("ℹ️ Ye kya-kya change kar sakta hai"):
        st.markdown("**Text settings:**")
        for k, desc in KNOWN_CONFIG_KEYS.items():
            st.write(f"• `{k}` — {desc}")
        st.markdown("**Feature ON/OFF (maintenance ke liye):**")
        for k, label in FEATURE_KEYS.items():
            st.write(f"• {label}")
        st.markdown("Isके अलावा भी कोई custom setting bolo, wo bhi बना देगा.")

    if "admin_chat_messages" not in st.session_state:
        st.session_state.admin_chat_messages = []
    if "admin_pending_action" not in st.session_state:
        st.session_state.admin_pending_action = None

    for msg in st.session_state.admin_chat_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Show a pending proposed change, waiting for confirmation
    pending = st.session_state.admin_pending_action
    if pending:
        st.info(f"📋 **Proposed change:** {pending.get('reply', '')}")
        st.json({k: v for k, v in pending.items() if k != "reply"})
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✅ Apply Karo", type="primary", use_container_width=True):
                success = _apply_action(supabase, pending)
                if success:
                    st.success("✅ Apply ho gaya! Live app pe reflect hoga.")
                st.session_state.admin_pending_action = None
                st.rerun()
        with col_b:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.admin_pending_action = None
                st.info("Cancel kar diya, koi change nahi hua.")
                st.rerun()
        return  # don't accept new input while a proposal is pending

    if prompt := st.chat_input("Jo bhi badalna hai, likho..."):
        st.session_state.admin_chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        try:
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            # only send recent turns to keep it focused
            for m in st.session_state.admin_chat_messages[-10:]:
                messages.append({"role": m["role"], "content": m["content"]})

            response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                max_tokens=500,
                temperature=0.3,
            )
            raw = response.choices[0].message.content.strip()
            raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

            parsed = json.loads(raw)
            reply = parsed.get("reply", "Samajh nahi aaya, dobara try karo.")

            with st.chat_message("assistant"):
                st.write(reply)
            st.session_state.admin_chat_messages.append({"role": "assistant", "content": reply})

            if parsed.get("action") in ("set_config", "set_feature_flag"):
                st.session_state.admin_pending_action = parsed
                st.rerun()

        except json.JSONDecodeError:
            error_msg = "⚠️ AI ka response samajh nahi aaya (invalid format). Dobara clearly try karo."
            with st.chat_message("assistant"):
                st.write(error_msg)
            st.session_state.admin_chat_messages.append({"role": "assistant", "content": error_msg})
        except Exception as e:
            st.error(f"Error: {e}")


def _apply_action(supabase, action: dict) -> bool:
    if action.get("action") == "set_config":
        return _save_config(supabase, action["key"], action["value"])
    if action.get("action") == "set_feature_flag":
        return _set_feature_flag(supabase, action["feature"], bool(action["enabled"]))
    return False
