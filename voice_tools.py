"""
AI Master Voice & Professional Studio (Pro Version)
-----------------------------------------------------
Production-hardened rewrite:
- No hardcoded secrets (reads from environment / st.secrets)
- Cached expensive API calls
- Fixed multi-chunk audio generation (chunks are now actually merged)
- Proper error handling (no silent bare excepts)
- Temp files cleaned up after use
- Safer async handling for Streamlit's execution model
"""

import streamlit as st
import os
import asyncio
import re
import logging
from datetime import datetime
from pathlib import Path

import edge_tts
import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CLONED_VOICES_DIR = Path("saved_cloned_voices")
CLONED_VOICES_DIR.mkdir(exist_ok=True)

OUTPUT_DIR = Path("generated_audio")
OUTPUT_DIR.mkdir(exist_ok=True)

MAX_CHUNK_CHARS = 3500
CHUNK_THRESHOLD_CHARS = 4000


def get_elevenlabs_api_key() -> str | None:
    """
    Fetch the ElevenLabs API key from environment variables or Streamlit secrets.
    NEVER hardcode API keys in source. Set ELEVENLABS_API_KEY as an env var,
    or add it to .streamlit/secrets.toml as:
        ELEVENLABS_API_KEY = "your-key-here"
    """
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        try:
            key = st.secrets.get("ELEVENLABS_API_KEY")
        except Exception:
            key = None
    return key


# ---------------------------------------------------------------------------
# Text processing (smart pauses / breathing effects)
# ---------------------------------------------------------------------------

class StudioAudioEnhancer:
    """Applies smart pauses and breathing effects without external dependencies."""

    @staticmethod
    def apply_smart_pauses_and_breathing(text: str, emotion: str) -> str:
        if not text:
            return text

        if "फुसफुसाहट" in emotion or "Whisper" in emotion:
            text = f"shh... (सांस लेते हुए) {text}... धीरे से..."
        elif "हंसते हुए" in emotion or "Laughing" in emotion:
            text = f"हा हा... {text}..."

        sentences = re.split(r'(?<=[.!?])\s+', text)
        processed_sentences = []

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if len(sentence.split()) > 5:
                sentence = f"... (सांस लें) ... {sentence}"

            if "डरावना" in emotion or "गंभीर" in emotion:
                sentence = sentence.replace(",", "...... ").replace("!", "...... ").replace("?", "......... ")
            elif "भावुक" in emotion:
                sentence = sentence.replace(",", ".... ").replace("!", ".... ").replace("?", "...... ")
            else:
                sentence = sentence.replace(",", "... ").replace("!", "... ").replace("?", "...... ")

            processed_sentences.append(sentence)

        return " ... ".join(processed_sentences)


# ---------------------------------------------------------------------------
# Async helper
# ---------------------------------------------------------------------------

def run_async(coro):
    """
    Run an async coroutine safely inside Streamlit's sync execution context.
    Streamlit does not run its own event loop per-script-run, so a fresh
    loop is the most reliable approach here.
    """
    try:
        return asyncio.run(coro)
    except RuntimeError as e:
        # Fallback for the rare case a loop is already running in this thread
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)
        finally:
            loop.close()


# ---------------------------------------------------------------------------
# TTS generation
# ---------------------------------------------------------------------------

async def generate_edge_audio_with_emotion(
    text: str,
    voice_name: str,
    output_file: Path,
    rate_str: str = "+0%",
    pitch_str: str = "+0Hz",
    emotion: str = "Normal",
) -> None:
    enhanced_text = StudioAudioEnhancer.apply_smart_pauses_and_breathing(text, emotion)
    communicate = edge_tts.Communicate(enhanced_text, voice_name, rate=rate_str, pitch=pitch_str)
    await communicate.save(str(output_file))


def generate_elevenlabs_audio(text: str, voice_id: str, output_file: Path) -> None:
    api_key = get_elevenlabs_api_key()
    if not api_key:
        raise RuntimeError("ElevenLabs API key is not configured (set ELEVENLABS_API_KEY).")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key,
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }

    response = requests.post(url, json=payload, headers=headers, timeout=60)
    if response.status_code != 200:
        raise RuntimeError(f"ElevenLabs API Error ({response.status_code}): {response.text}")

    output_file.write_bytes(response.content)


@st.cache_data(ttl=600, show_spinner=False)
def get_elevenlabs_voices() -> dict:
    """Cached for 10 minutes so we don't hit the API on every rerun/widget interaction."""
    api_key = get_elevenlabs_api_key()
    if not api_key:
        return {}

    try:
        response = requests.get(
            "https://api.elevenlabs.io/v1/voices",
            headers={"xi-api-key": api_key},
            timeout=15,
        )
        response.raise_for_status()
        voices = response.json().get("voices", [])
        return {v["name"]: v["voice_id"] for v in voices}
    except requests.RequestException as e:
        logger.warning("Could not fetch ElevenLabs voices: %s", e)
        return {}


def merge_audio_chunks(chunk_files: list[Path], output_file: Path) -> None:
    """
    Concatenate MP3 chunks into a single file.
    Raw byte concatenation works reliably for consecutive MPEG audio frames
    produced by edge-tts (no ID3 container per chunk), which covers this
    use case without adding a heavy dependency like pydub/ffmpeg.
    """
    with open(output_file, "wb") as outfile:
        for chunk_path in chunk_files:
            outfile.write(chunk_path.read_bytes())


def cleanup_files(paths: list[Path]) -> None:
    for p in paths:
        try:
            if p.exists():
                p.unlink()
        except OSError as e:
            logger.warning("Could not delete temp file %s: %s", p, e)


# ---------------------------------------------------------------------------
# Static config: languages & character voice profiles
# ---------------------------------------------------------------------------

LANG_VOICE_MAP = {
    "🇮🇳 Hindi (हिन्दी)": {"female": "hi-IN-SwaraNeural", "male_deep": "hi-IN-MadhurNeural", "male_energetic": "hi-IN-MadhurNeural"},
    "🇮🇳 English (भारतीय अंग्रेज़ी)": {"female": "en-IN-NeerjaNeural", "male_deep": "en-IN-PrabhatNeural", "male_energetic": "en-IN-PrabhatNeural"},
    "🇺🇸 English (US - अमेरिकी अंग्रेज़ी)": {"female": "en-US-AriaNeural", "male_deep": "en-US-ChristopherNeural", "male_energetic": "en-US-AndrewNeural"},
    "🇧🇩 Bengali (বাংলা)": {"female": "bn-BD-TanishaNeural", "male_deep": "bn-BD-PradeepNeural", "male_energetic": "bn-BD-PradeepNeural"},
    "🇮🇳 Marathi (मराठी)": {"female": "mr-IN-AarohiNeural", "male_deep": "mr-IN-ManoharNeural", "male_energetic": "mr-IN-ManoharNeural"},
    "🇮🇳 Tamil (தமிழ்)": {"female": "ta-IN-PallaviNeural", "male_deep": "ta-IN-ValluvarNeural", "male_energetic": "ta-IN-ValluvarNeural"},
    "🇮🇳 Telugu (తెలుగు)": {"female": "te-IN-ShrutiNeural", "male_deep": "te-IN-MohanNeural", "male_energetic": "te-IN-MohanNeural"},
    "🇮🇳 Gujarati (ગુજરાતી)": {"female": "gu-IN-DhwaniNeural", "male_deep": "gu-IN-NiranjanNeural", "male_energetic": "gu-IN-NiranjanNeural"},
    "🇫🇷 French (Français)": {"female": "fr-FR-DeniseNeural", "male_deep": "fr-FR-HenriNeural", "male_energetic": "fr-FR-AlainNeural"},
}

FIXED_CHARACTER_PROFILES = {
    "4. 👻 Horror Ghost (डरावनी भूतिया भारी आवाज़)": {
        "type": "edge", "voice": "en-GB-RyanNeural", "pitch": "-12Hz", "rate": "-20%",
        "sample_text": "This is a dark horror ghost voice speaking from the shadows.",
    },
    "5. 👵 Old Village Woman (बूढ़ी औरत की खुरदरी भारी आवाज़)": {
        "type": "edge", "voice": "en-US-AriaNeural", "pitch": "-8Hz", "rate": "-15%",
        "sample_text": "Beta, sun rahe ho meri purani kahani?",
    },
    "6. 👴 Old Wise Grandfather (बुजुर्ग और समझदार दादाजी)": {
        "type": "edge", "voice": "en-US-AndrewNeural", "pitch": "-7Hz", "rate": "-10%",
        "sample_text": "Waqt sabse bada sikandar hota hai mere bachhe.",
    },
    "7. 🧛 Evil Villain / Monster (खतरनाक खलनायक की आवाज़)": {
        "type": "edge", "voice": "en-US-ChristopherNeural", "pitch": "-10Hz", "rate": "-8%",
        "sample_text": "You cannot escape from my trap now!",
    },
    "8. 🕵️‍♂️ Deep Mystery Narrator (सस्पेंस मिस्ट्री नरेटर)": {
        "type": "edge", "voice": "en-US-BrianNeural", "pitch": "-6Hz", "rate": "-5%",
        "sample_text": "A dark secret was hidden behind the ancient walls.",
    },
    "9. 👦 Young Energetic Boy (उत्साही युवा लड़का)": {
        "type": "edge", "voice": "en-US-AndrewNeural", "pitch": "+6Hz", "rate": "+8%",
        "sample_text": "Hey guys, let's explore this amazing adventure!",
    },
    "10. 👧 Sweet Young Girl (मासूम और प्यारी बच्ची की पतली आवाज़)": {
        "type": "edge", "voice": "en-US-AriaNeural", "pitch": "+12Hz", "rate": "+5%",
        "sample_text": "Dekho na bhaiya, kitni sundar titli hai yeh!",
    },
    "11. 🤖 Robotic Sci-Fi AI (रोबोटिक कंप्यूटर आवाज़)": {
        "type": "edge", "voice": "en-US-ChristopherNeural", "pitch": "+0Hz", "rate": "+2%",
        "sample_text": "System online. Processing neural commands.",
    },
    "12. 👑 Royal King / Emperor (शाही और रौबदार राजा की आवाज़)": {
        "type": "edge", "voice": "en-US-BrianNeural", "pitch": "-9Hz", "rate": "-10%",
        "sample_text": "Humare samrajya mein aapka swagat hai.",
    },
    "13. 🧚 Fairy Tale Princess (परी कथा वाली जादुई आवाज़)": {
        "type": "edge", "voice": "en-US-AriaNeural", "pitch": "+8Hz", "rate": "+3%",
        "sample_text": "Once upon a time in a magical kingdom far away.",
    },
    "14. 🧙‍♂️ Ancient Wizard / Sage (प्राचीन जादूगर की रहस्यमयी आवाज़)": {
        "type": "edge", "voice": "en-GB-RyanNeural", "pitch": "-14Hz", "rate": "-22%",
        "sample_text": "Ancient spells are awakened by secret words.",
    },
    "15. 🦸 Action Superhero (धांसू और दमदार सुपरहीरो आवाज़)": {
        "type": "edge", "voice": "en-US-AndrewNeural", "pitch": "-3Hz", "rate": "+5%",
        "sample_text": "Justice will be served today. Fear not!",
    },
}


def build_voice_profiles(selected_language: str) -> dict:
    """Build the full voice profile map: language-specific + fixed + cloned + ElevenLabs."""
    current_lang_voices = LANG_VOICE_MAP.get(selected_language, LANG_VOICE_MAP["🇮🇳 Hindi (हिन्दी)"])

    profiles = {
        f"1. 🇮🇳 {selected_language} - Swara (मुख्य नेचुरल महिला आवाज़)": {
            "type": "edge", "voice": current_lang_voices["female"], "pitch": "+0Hz", "rate": "+0%",
            "sample_text": "नमस्ते, यह मेरी प्राकृतिक महिला आवाज़ का सैंपल है।",
        },
        f"2. 🇮🇳 {selected_language} - Madhur (गंभीर और भारी पुरुष आवाज़)": {
            "type": "edge", "voice": current_lang_voices["male_deep"], "pitch": "-5Hz", "rate": "-5%",
            "sample_text": "नमस्कार, यह एक गंभीर और भारी पुरुष आवाज़ है।",
        },
        f"3. 🇮🇳 {selected_language} - Prabhat (तेज़ और जोशीली पुरुष आवाज़)": {
            "type": "edge", "voice": current_lang_voices["male_energetic"], "pitch": "+4Hz", "rate": "+10%",
            "sample_text": "नमस्ते दोस्तों, यह एक जोशीली और एनर्जेटिक आवाज़ है!",
        },
    }
    profiles.update(FIXED_CHARACTER_PROFILES)

    # Locally saved cloned voices
    for clone_file in CLONED_VOICES_DIR.glob("*.mp3"):
        c_name = clone_file.stem
        profiles[f"🧬 My Cloned Voice - {c_name}"] = {
            "type": "local_clone",
            "voice": current_lang_voices["male_deep"],
            "pitch": "-3Hz",
            "rate": "-2%",
            "file_path": clone_file,
            "sample_text": f"नमस्ते, यह मेरा क्लोन किया हुआ कैरेक्टर {c_name} बोल रहा है।",
        }

    # ElevenLabs voices (only if API key configured; cached)
    for el_name, el_id in get_elevenlabs_voices().items():
        profiles[f"🔥 ElevenLabs Voice - {el_name}"] = {
            "type": "elevenlabs",
            "voice_id": el_id,
            "sample_text": "Hello, this is an ElevenLabs master voice sample.",
        }

    return profiles


# ---------------------------------------------------------------------------
# Audio generation orchestration
# ---------------------------------------------------------------------------

def compute_rate_and_pitch(config: dict, speed_option: float, emotion: str) -> tuple[str, str]:
    base_rate_num = int(config["rate"].replace("+", "").replace("%", ""))
    slider_rate_num = int((speed_option - 1.0) * 100)
    total_rate_num = base_rate_num + slider_rate_num
    rate_val = f"+{total_rate_num}%" if total_rate_num >= 0 else f"{total_rate_num}%"

    base_pitch_num = int(config["pitch"].replace("Hz", ""))
    if "डरावना" in emotion or "गंभीर" in emotion:
        base_pitch_num -= 4
    elif "भावुक" in emotion:
        base_pitch_num -= 2
    elif "जोशीला" in emotion or "एनर्जेटिक" in emotion:
        base_pitch_num += 3
    elif "फुसफुसाहट" in emotion or "Whisper" in emotion:
        base_pitch_num -= 5
        rate_val = "-18%"
    elif "हंसते हुए" in emotion or "Laughing" in emotion:
        base_pitch_num += 3

    pitch_val = f"+{base_pitch_num}Hz" if base_pitch_num >= 0 else f"{base_pitch_num}Hz"
    return rate_val, pitch_val


def generate_master_audio(config: dict, text: str, emotion: str, speed_option: float, timestamp: str) -> Path:
    """Generate the final audio file, correctly merging chunks for long text."""
    final_path = OUTPUT_DIR / f"master_audio_{timestamp}.mp3"

    if config["type"] == "elevenlabs":
        try:
            generate_elevenlabs_audio(text, config["voice_id"], final_path)
            return final_path
        except Exception as e:
            logger.warning("ElevenLabs generation failed, falling back to edge-tts: %s", e)
            # Fall through to edge-tts fallback below using a deep male voice
            fallback_voice = LANG_VOICE_MAP["🇮🇳 Hindi (हिन्दी)"]["male_deep"]
            run_async(generate_edge_audio_with_emotion(text, fallback_voice, final_path, emotion=emotion))
            return final_path

    if config["type"] == "local_clone":
        # Cloned sample is a static reference file, not a generator; just return it.
        return config["file_path"]

    # type == "edge"
    voice_id = config["voice"]
    rate_val, pitch_val = compute_rate_and_pitch(config, speed_option, emotion)

    if len(text) <= CHUNK_THRESHOLD_CHARS:
        run_async(generate_edge_audio_with_emotion(text, voice_id, final_path, rate_str=rate_val, pitch_str=pitch_val, emotion=emotion))
        return final_path

    # Long text: split, generate each chunk, then merge them all (bug fix vs. original)
    chunks = [text[i:i + MAX_CHUNK_CHARS] for i in range(0, len(text), MAX_CHUNK_CHARS)]
    chunk_paths = []
    for idx, chunk in enumerate(chunks):
        chunk_path = OUTPUT_DIR / f"chunk_{timestamp}_{idx}.mp3"
        run_async(generate_edge_audio_with_emotion(chunk, voice_id, chunk_path, rate_str=rate_val, pitch_str=pitch_val, emotion=emotion))
        chunk_paths.append(chunk_path)

    merge_audio_chunks(chunk_paths, final_path)
    cleanup_files(chunk_paths)
    return final_path


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------

def render_voice_page():
    st.subheader("🎙️ AI Master Voice & Professional Studio (Pro Version)")
    st.write("यहाँ हर कैरेक्टर के लिए बिल्कुल अलग और सटीक न्यूरल आवाज़ें, सांस/पॉज़ इफेक्ट्स और वॉइस क्लोनिंग की सुविधा उपलब्ध है:")

    if not get_elevenlabs_api_key():
        st.info("ℹ️ ElevenLabs voices अभी उपलब्ध नहीं हैं। `ELEVENLABS_API_KEY` env variable सेट करें ताकि प्रीमियम आवाज़ें भी दिखें।")

    # --- Voice cloning manager ---
    with st.expander("🧬 Custom Voice Cloning & Management (अपनी आवाज़ सेव करें)", expanded=False):
        st.write("अपनी आवाज़ रिकॉर्ड करें या ऑडियो फाइल अपलोड करके नया क्लोन कैरेक्टर रजिस्टर करें:")
        clone_name = st.text_input("कैरेक्टर या आवाज़ का नाम दें (जैसे: Trup):")
        uploaded_sample = st.file_uploader("आवाज़ का सैंपल अपलोड करें (MP3 / WAV फ़ाइल):", type=["mp3", "wav"])

        if st.button("Save & Register Cloned Voice 🎙️"):
            if clone_name and uploaded_sample:
                safe_name = re.sub(r"[^\w\-]", "_", clone_name.strip())
                save_path = CLONED_VOICES_DIR / f"{safe_name}.mp3"
                save_path.write_bytes(uploaded_sample.getbuffer())
                st.success(f"🎉 '{clone_name}' की आवाज़ सफलतापूर्वक सेव हो गई है!")
                st.cache_data.clear()
            else:
                st.warning("⚠️ कृपया आवाज़ का नाम और ऑडियो फाइल दोनों दें!")

        saved_files = list(CLONED_VOICES_DIR.glob("*.mp3"))
        if saved_files:
            st.markdown("**सेव किए गए क्लोन कैरेक्टर्स:**")
            for sf in saved_files:
                st.text(f"• {sf.stem}")

    st.markdown("---")

    # --- Language selector ---
    selected_language = st.selectbox("🌐 भाषा चुनें (Select Output Language):", list(LANG_VOICE_MAP.keys()))

    # --- Script input ---
    st.markdown("### ✍️ अपनी स्क्रिप्ट या डायलॉग यहाँ दर्ज करें")
    audio_text = st.text_area(
        "डायलॉग या बड़ी स्क्रिप्ट यहाँ लिखें (8000+ शब्द समर्थित):",
        placeholder="यहाँ अपनी लंबी स्क्रिप्ट या कहानी पेस्ट करें...",
        height=220,
    )

    if audio_text:
        word_count = len(audio_text.split())
        char_count = len(audio_text)
        st.caption(f"📊 कुल शब्द (Words): {word_count} | कुल अक्षर (Characters): {char_count}")

    # --- Character selection ---
    voice_profiles_map = build_voice_profiles(selected_language)
    voice_profiles = list(voice_profiles_map.keys())

    col_v1, col_v2 = st.columns([3, 1])
    with col_v1:
        selected_character = st.selectbox("🎭 कैरेक्टर और आवाज़ का चयन (न्यूरल और क्लोन विकल्प):", voice_profiles)
    with col_v2:
        st.markdown("<br>", unsafe_allow_html=True)
        preview_clicked = st.button("🔊 Preview Voice")

    if preview_clicked:
        with st.spinner("आवाज़ का सैंपल तैयार हो रहा है..."):
            try:
                p_config = voice_profiles_map[selected_character]
                if p_config["type"] == "local_clone":
                    st.audio(str(p_config["file_path"]))
                elif p_config["type"] == "elevenlabs":
                    preview_path = OUTPUT_DIR / "voice_preview_temp.mp3"
                    try:
                        generate_elevenlabs_audio(p_config["sample_text"], p_config["voice_id"], preview_path)
                    except Exception as el_err:
                        logger.warning("ElevenLabs preview failed, falling back: %s", el_err)
                        fallback_voice = LANG_VOICE_MAP["🇮🇳 Hindi (हिन्दी)"]["female"]
                        run_async(generate_edge_audio_with_emotion(p_config["sample_text"], fallback_voice, preview_path))
                    st.audio(str(preview_path))
                else:
                    preview_path = OUTPUT_DIR / "voice_preview_temp.mp3"
                    run_async(generate_edge_audio_with_emotion(
                        p_config["sample_text"], p_config["voice"], preview_path,
                        rate_str=p_config.get("rate", "+0%"), pitch_str=p_config.get("pitch", "+0Hz"),
                    ))
                    st.audio(str(preview_path))
            except Exception as e:
                st.error(f"प्रीव्यू में एरर: {e}")

    audio_emotion = st.selectbox("⚡ भाव / टोन (Tone & Expression):", [
        "Normal / Clear & Natural (सामान्य और साफ़)",
        "Storytelling / Emotional (कहानी वाला भावुक अंदाज़)",
        "Excited / Energetic (जोशीला और एनर्जेटिक)",
        "Dark / Mysterious (गंभीर और डरावना)",
        "Whisper / Soft Breath (फुसफुसाहट और सांस लेने का अंदाज़)",
        "Laughing / Joyful (हंसते हुए और आनंदित)",
    ])

    speed_option = st.slider("🗣️ बोलने की गति (Speed Mode):", 0.5, 2.0, 1.0, 0.1)

    if st.button("Generate Master Character Audio 🔊✨", type="primary", use_container_width=True):
        if not audio_text.strip():
            st.warning("⚠️ कृपया पहले टेक्स्ट बॉक्स में अपनी स्क्रिप्ट या डायलॉग लिखें!")
            return

        with st.spinner(f"🎙️ '{selected_character}' के रूप में फाइनल ऑडियो तैयार हो रहा है..."):
            try:
                config = voice_profiles_map[selected_character]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                final_path = generate_master_audio(config, audio_text, audio_emotion, speed_option, timestamp)

                st.success("🎉 ऑडियो सफलतापूर्वक जनरेट हो गया!")
                st.audio(str(final_path))
                st.info("💡 आप प्लेयर के तीन डॉट्स (...) पर क्लिक करके इसे आसानी से डाउनलोड कर सकते हैं।")
            except Exception as e:
                logger.exception("Audio generation failed")
                st.error(f"🚨 ऑडियो जनरेशन में गड़बड़: {e}")


if __name__ == "__main__":
    render_voice_page()
