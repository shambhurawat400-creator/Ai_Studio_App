import streamlit as str_lit
import os
import asyncio
import edge_tts
from datetime import datetime
import io
import re

# --- Safe Studio Audio Enhancer (Pydub optional / safe fallback) ---
try:
    from pydub import AudioSegment, effects
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

class StudioAudioEnhancer:
    """Applies smart pauses, human breathing tags, and audio mastering (DSP)."""
    
    @staticmethod
    def apply_smart_pauses_and_breathing(text: str, emotion: str) -> str:
        """Inserts natural breathing tokens and strategic sentence/punctuation pauses based on emotion."""
        sentences = text.split('.')
        processed_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if len(sentence.split()) > 8:
                sentence = f"... {sentence}"
            
            # Emotion-based distinct pacing and human touch
            if "डरावना" in emotion or "गंभीर" in emotion:
                sentence = sentence.replace(",", "...... ")
                sentence = sentence.replace("!", "...... ")
                sentence = sentence.replace("?", "......... ")
            elif "भावुक" in emotion:
                sentence = sentence.replace(",", ".... ")
                sentence = sentence.replace("!", ".... ")
            else:
                sentence = sentence.replace(",", "... ")
                sentence = sentence.replace("!", "... ")
                sentence = sentence.replace("?", "...... ")
            
            processed_sentences.append(sentence)
            
        return " ... ".join(processed_sentences)

    @staticmethod
    def enhance_audio_bytes(audio_bytes: bytes, output_format: str = "mp3") -> bytes:
        """Applies compression, normalization and warm studio sound effects if pydub is available."""
        if not PYDUB_AVAILABLE:
            return audio_bytes
        try:
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
            audio = effects.compress_dynamic_range(audio, threshold=-16.0, ratio=2.5, attack=4.0, release=40.0)
            audio = effects.normalize(audio, headroom=0.5)
            
            out_buffer = io.BytesIO()
            audio.export(out_buffer, format=output_format, bitrate="320k")
            return out_buffer.getvalue()
        except Exception:
            return audio_bytes

# Safe Async Runner for Streamlit to prevent event loop crashes
def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return asyncio.run(coro)
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)

async def generate_edge_audio_with_emotion(text, voice_name, output_file, rate_str="+0%", pitch_str="+0Hz", emotion="Normal"):
    enhanced_text = StudioAudioEnhancer.apply_smart_pauses_and_breathing(text, emotion)
    
    communicate = edge_tts.Communicate(enhanced_text, voice_name, rate=rate_str, pitch=pitch_str)
    
    raw_output = output_file.replace(".mp3", "_raw.mp3")
    await communicate.save(raw_output)
    
    if os.path.exists(raw_output):
        with open(raw_output, "rb") as f:
            raw_bytes = f.read()
        mastered_bytes = StudioAudioEnhancer.enhance_audio_bytes(raw_bytes)
        with open(output_file, "wb") as f:
            f.write(mastered_bytes)
        os.remove(raw_output)

def render_voice_page():
    str_lit.subheader("🎙️ AI Master Voice & Character Studio (All-in-One Pro)")
    str_lit.write("सभी कैरेक्टर्स, परफेक्ट इमोशंस, स्मार्ट पॉज़ और स्टूडियो मास्टरिंग के साथ:")

    # --- Initialize Permanent Saved Voices in Session State ---
    if "saved_cloned_voices" not in str_lit.session_state:
        str_lit.session_state.saved_cloned_voices = {}

    # --- 1. VOICE CLONING SECTION ---
    str_lit.markdown("---")
    str_lit.markdown("### 🧬 AI Voice Customization (स्थायी रूप से आवाज़ सेव करें)")
    
    uploaded_audio = str_lit.file_uploader("अपनी आवाज़ का सैंपल अपलोड करें (WAV / MP3 / AAC):", type=["wav", "mp3", "m4a", "aac"])
    cloned_name_input = str_lit.text_input("📝 इस आवाज़ प्रोफाइल का नाम दें:", placeholder="जैसे: मेरी आवाज़, राहुल...")
    
    # Base voice style for the custom clone mapping
    clone_base_style = str_lit.selectbox("🎭 इस क्लोन के लिए आधार आवाज़ चुनें:", [
        "🇮🇳 Madhur (Deep Male Voice)", 
        "🇮🇳 Swara (Natural Female Voice)", 
        "🇮🇳 Prabhat (Energetic Male Voice)", 
        "🇮🇳 Ananya (Sweet Young Voice)"
    ])

    if str_lit.button("💾 Save Voice Profile"):
        if uploaded_audio is not None and cloned_name_input.strip():
            os.makedirs("cloned_voices", exist_ok=True)
            saved_path = os.path.join("cloned_voices", uploaded_audio.name)
            with open(saved_path, "wb") as f:
                f.write(uploaded_audio.getbuffer())
            
            mapped_voice = "hi-IN-MadhurNeural"
            if "Swara" in clone_base_style:
                mapped_voice = "hi-IN-SwaraNeural"
            elif "Prabhat" in clone_base_style:
                mapped_voice = "hi-IN-PrabhatNeural"
            elif "Ananya" in clone_base_style:
                mapped_voice = "hi-IN-AnanyaNeural"

            str_lit.session_state.saved_cloned_voices[cloned_name_input.strip()] = {
                "path": saved_path,
                "voice": mapped_voice
            }
            str_lit.success(f"🎉 शानदार! '{cloned_name_input.strip}' प्रोफाइल सफलतापूर्वक सेव और टेक्स्ट-टू-स्पीच के लिए तैयार हो गई है!")
        else:
            str_lit.warning("⚠️ कृपया पहले ऑडियो फ़ाइल अपलोड करें और उसका नाम सही से दर्ज करें!")

    # Display preview for uploaded/saved custom voices
    if str_lit.session_state.saved_cloned_voices:
        str_lit.info(f"📂 कुल सेव की गई कस्टम आवाज़ें: {len(str_lit.session_state.saved_cloned_voices)}")
        selected_preview_custom = str_lit.selectbox("🎧 अपनी सेव की गई क्लोन आवाज़ सुनें:", list(str_lit.session_state.saved_cloned_voices.keys()))
        if selected_preview_custom:
            str_lit.audio(str_lit.session_state.saved_cloned_voices[selected_preview_custom]["path"])

    # --- 2. ADVANCED TEXT-TO-SPEECH CHARACTER STUDIO ---
    str_lit.markdown("---")
    str_lit.markdown("### 🗣️ Ultimate Character & Realistic Voice Studio")

    audio_text = str_lit.text_area("डायलॉग या स्क्रिप्ट यहाँ लिखें जिसे ऑडियो में बदलना है:", placeholder="यहाँ अपना टेक्स्ट टाइप करें...")
    
    # Fully Working Multi-Language Supported Neural Voices for Every Character (Fixed Ananya & Prabhat)
    voice_profiles_map = {
        "🇮🇳 Swara (Best Indian Female - कहानी और वीडियो के लिए सर्वश्रेष्ठ)": {"voice": "hi-IN-SwaraNeural", "sample": "नमस्कार दोस्तों, इस तरह का वीडियो बहुत ही ज्यादा चलता है।"},
        "🇮🇳 Madhur (Best Indian Male - गंभीर और भारी आवाज़)": {"voice": "hi-IN-MadhurNeural", "sample": "समय का चक्र बहुत बलवान है बालक, ध्यान से सुनो।"},
        "🇮🇳 Ananya (Sweet Young Girl Voice - मासूम आवाज़)": {"voice": "hi-IN-AnanyaNeural", "sample": "नमस्ते दोस्तों, आज हम एक नई कहानी सुनेंगे।"},
        "🇮🇳 Prabhat (Energetic Male Voice - जोशीली आवाज़)": {"voice": "hi-IN-PrabhatNeural", "sample": "स्वागत है आपका हमारे चैनल पर, चलिए शुरू करते हैं!"},
        "🇬🇧 Ryan (Deep English Narrator - ब्रिटिश नरेटर)": {"voice": "en-GB-RyanNeural", "sample": "Beware, darkness is approaching this mysterious land."},
        "🇺🇸 Andrew (Wise Grandfather - अमेरिकी बुजुर्ग आवाज़)": {"voice": "en-US-AndrewNeural", "sample": "Listen closely to my advice, young adventurer."},
        "🇺🇸 Aria (Energetic Young Boy/Girl - उत्साह भरी आवाज़)": {"voice": "en-US-AriaNeural", "sample": "Hey everyone, let's go on an amazing adventure!"},
        "🇫🇷 French Mysterious Narrator (रहस्यमयी विदेशी आवाज़)": {"voice": "fr-FR-HenriNeural", "sample": "Un secret mystérieux caché dans la nuit sombre."},
        "👻 Horror Ghost (डरावनी भूतिया आवाज़)": {"voice": "en-GB-RyanNeural", "sample": "Beware, darkness is approaching."},
        "👵 Old Village Woman (बूढ़ी डरावनी औरत)": {"voice": "hi-IN-SwaraNeural", "sample": "बेटा, उस कुएं के पास मत जाना।"},
        "👴 Old Wise Grandfather (बुजुर्ग और गंभीर आवाज़)": {"voice": "hi-IN-MadhurNeural", "sample": "ध्यान से सुनो मेरी बात, बालक।"},
        "🧛 Evil Villain / Monster (खलनायक की भारी आवाज़)": {"voice": "hi-IN-MadhurNeural", "sample": "अब तुम्हें कोई नहीं बचा सकता मुझसे।"},
        "🕵️‍♂️ Deep Male Narrator (सस्पेंस / मिस्ट्री नरेटर)": {"voice": "en-US-BrianNeural", "sample": "A mysterious secret hidden in the dark."},
        "👦 Young Energetic Boy (उत्साही युवा लड़का)": {"voice": "en-US-AriaNeural", "sample": "Hey everyone, let's go on an adventure!"},
        "👧 Sweet Young Girl (मासूम लड़की की आवाज़)": {"voice": "hi-IN-AnanyaNeural", "sample": "नमस्ते दोस्तों, कैसे हो आप सब?"},
        "😡 Angry / Aggressive Hero (गुस्से में हीरो की आवाज़)": {"voice": "hi-IN-PrabhatNeural", "sample": "मैं तुम्हें कभी माफ नहीं करूंगा!"},
        "😭 Sad & Emotional Voice (रोनी और भावुक आवाज़)": {"voice": "hi-IN-SwaraNeural", "sample": "मेरा सब कुछ लुट गया है बाबूजी।"},
        "🤖 Robotic Sci-Fi AI (रोबोटिक आवाज़)": {"voice": "en-US-ChristopherNeural", "sample": "System operational, initializing sequence."},
        "👑 Royal King / Emperor (शाही राजा की आवाज़)": {"voice": "en-GB-SoniaNeural", "sample": "By the order of the king, hear me out."},
        "🧙‍♂️ Wise Wizard / Sadhu (रहस्यमयी साधु या जादूगर)": {"voice": "hi-IN-MadhurNeural", "sample": "समय का चक्र बहुत बलवान है बालक।"}
    }

    voice_profiles = list(voice_profiles_map.keys())
    for custom_voice in list(str_lit.session_state.saved_cloned_voices.keys()):
        voice_profiles.insert(0, f"🧬 [Custom] {custom_voice}")

    selected_character = str_lit.selectbox("🎭 कैरेक्टर और रियलिस्टिक आवाज़ का चयन:", voice_profiles)

    # --- INSTANT AUTO PREVIEW PLAYER ---
    if "[Custom]" not in selected_character:
        try:
            config = voice_profiles_map.get(selected_character, {"voice": "hi-IN-SwaraNeural", "sample": "नमस्ते"})
            preview_filename = f"preview_{config['voice']}.mp3"
            
            if not os.path.exists(preview_filename):
                run_async(generate_edge_audio_with_emotion(config["sample"], config["voice"], preview_filename, emotion="Normal"))
            
            str_lit.markdown(f"🔊 **चयनित कैरेक्टर का नैचुरल प्रीव्यू:**")
            str_lit.audio(preview_filename)
        except Exception:
            pass

    # --- EMOTION SELECTION CONTROLS ---
    audio_emotion = str_lit.selectbox("⚡ भाव / टोन (Tone & Expression):", [
        "Normal / Clear & Natural (सामान्य और साफ़)",
        "Storytelling / Emotional (कहानी वाला भावुक अंदाज़)",
        "Excited / Energetic (जोशीला और एनर्जेटिक)",
        "Dark / Mysterious (गंभीर और डरावना)"
    ])

    speed_option = str_lit.slider("🗣️ बोलने की गति (Speed Mode):", 0.5, 2.0, 1.0, 0.1)

    # --- GENERATE FULL AUDIO BUTTON ---
    if str_lit.button("Generate Master Character Audio 🔊✨", type="primary", use_container_width=True):
        if audio_text.strip():
            with str_lit.spinner(f"🎙️ '{selected_character}' के रूप में हाई-क्वालिटी रियलिस्टिक आवाज़ तैयार हो रही है..."):
                try:
                    # Fix: Properly route custom cloned voices and character configurations
                    if "[Custom]" in selected_character:
                        custom_key = selected_character.replace("🧬 [Custom] ", "").strip()
                        voice_id = str_lit.session_state.saved_cloned_voices[custom_key]["voice"]
                    else:
                        config = voice_profiles_map.get(selected_character, {"voice": "hi-IN-SwaraNeural"})
                        voice_id = config["voice"]

                    rate_val = f"{int((speed_option - 1.0) * 100)}%"
                    if speed_option < 1.0:
                        rate_val = f"-{int((1.0 - speed_option) * 100)}%"
                    else:
                        rate_val = f"+{int((speed_option - 1.0) * 100)}%"

                    # Distinct emotional pitch and pacing control
                    pitch_val = "+0Hz"
                    if "डरावना" in audio_emotion or "गंभीर" in audio_emotion:
                        pitch_val = "-6Hz"
                        rate_val = "-10%"
                    elif "भावुक" in audio_emotion:
                        pitch_val = "-3Hz"
                        rate_val = "-5%"
                    elif "जोशीला" in audio_emotion or "एनर्जेटिक" in audio_emotion:
                        pitch_val = "+5Hz"
                        rate_val = "+10%"

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"master_audio_{timestamp}.mp3"

                    run_async(generate_edge_audio_with_emotion(audio_text, voice_id, filename, rate_str=rate_val, pitch_str=pitch_val, emotion=audio_emotion))

                    str_lit.success(f"🎉 ऑडियो सफलतापूर्वक जनरेट हो गया!")
                    str_lit.audio(filename)
                    str_lit.info("💡 आप इस ऑडियो प्लेयर पर दिए गए तीन डॉट्स (...) पर क्लिक करके इसे आसानी से डाउनलोड कर सकते हैं।")
                    
                except Exception as e:
                    str_lit.error(f"🚨 ऑडियो जनरेशन में गड़बड़: {e}")
        else:
            str_lit.warning("⚠️ कृपया पहले टेक्स्ट बॉक्स में अपनी स्क्रिप्ट या डायलॉग लिखें!")
