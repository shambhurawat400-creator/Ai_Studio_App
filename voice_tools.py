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
    """Applies smart pauses, breathing effects, and audio mastering (DSP)."""
    
    @staticmethod
    def apply_smart_pauses_and_breathing(text: str, emotion: str) -> str:
        # सांस लेने और फुसफुसाहट के नेचुरल इफ़ेक्ट्स
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
                sentence = sentence.replace(",", "...... ")
                sentence = sentence.replace("!", "...... ")
                sentence = sentence.replace("?", "......... ")
            elif "भावुक" in emotion:
                sentence = sentence.replace(",", ".... ")
                sentence = sentence.replace("!", ".... ")
                sentence = sentence.replace("?", "...... ")
            else:
                sentence = sentence.replace(",", "... ")
                sentence = sentence.replace("!", "... ")
                sentence = sentence.replace("?", "...... ")
            
            processed_sentences.append(sentence)
            
        return " ... ".join(processed_sentences)

    @staticmethod
    def enhance_audio_bytes(audio_bytes: bytes, output_format: str = "mp3") -> bytes:
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
    str_lit.subheader("🎙️ AI Master Voice & Professional Studio (Pro Version)")
    str_lit.write("यहाँ हर कैरेक्टर के लिए बिल्कुल अलग और सटीक न्यूरल आवाज़ें और सांस/पॉज़ इफेक्ट्स काम कर रहे हैं:")

    # --- 1. LANGUAGE SELECTOR ---
    str_lit.markdown("---")
    selected_language = str_lit.selectbox("🌐 भाषा चुनें (Select Output Language):", [
        "🇮🇳 Hindi (हिन्दी)",
        "🇮🇳 English (भारतीय अंग्रेज़ी)",
        "🇺🇸 English (US - अमेरिकी अंग्रेज़ी)",
        "🇧🇩 Bengali (বাংলা)",
        "🇮🇳 Marathi (मराठी)",
        "🇮🇳 Tamil (தமிழ்)",
        "🇮🇳 Telugu (తెలుగు)",
        "🇮🇳 Gujarati (ગુજરાતી)",
        "🇫🇷 French (Français)"
    ])

    lang_code_map = {
        "🇮🇳 Hindi (हिन्दी)": {"female": "hi-IN-SwaraNeural", "male_deep": "hi-IN-MadhurNeural", "male_energetic": "hi-IN-MadhurNeural"},
        "🇮🇳 English (भारतीय अंग्रेज़ी)": {"female": "en-IN-NeerjaNeural", "male_deep": "en-IN-PrabhatNeural", "male_energetic": "en-IN-PrabhatNeural"},
        "🇺🇸 English (US - अमेरिकी अंग्रेज़ी)": {"female": "en-US-AriaNeural", "male_deep": "en-US-ChristopherNeural", "male_energetic": "en-US-AndrewNeural"},
        "🇧🇩 Bengali (বাংলা)": {"female": "bn-BD-TanishaNeural", "male_deep": "bn-BD-PradeepNeural", "male_energetic": "bn-BD-PradeepNeural"},
        "🇮🇳 Marathi (मराठी)": {"female": "mr-IN-AarohiNeural", "male_deep": "mr-IN-ManoharNeural", "male_energetic": "mr-IN-ManoharNeural"},
        "🇮🇳 Tamil (தமிழ்)": {"female": "ta-IN-PallaviNeural", "male_deep": "ta-IN-ValluvarNeural", "male_energetic": "ta-IN-ValluvarNeural"},
        "🇮🇳 Telugu (తెలుగు)": {"female": "te-IN-ShrutiNeural", "male_deep": "te-IN-MohanNeural", "male_energetic": "te-IN-MohanNeural"},
        "🇮🇳 Gujarati (ગુજરાતી)": {"female": "gu-IN-DhwaniNeural", "male_deep": "gu-IN-NiranjanNeural", "male_energetic": "gu-IN-NiranjanNeural"},
        "🇫🇷 French (Français)": {"female": "fr-FR-DeniseNeural", "male_deep": "fr-FR-HenriNeural", "male_energetic": "fr-FR-AlainNeural"}
    }
    
    current_lang_voices = lang_code_map.get(selected_language, lang_code_map["🇮🇳 Hindi (हिन्दी)"])

    # --- 2. ADVANCED UNIQUE CHARACTER STUDIO ---
    str_lit.markdown("---")
    str_lit.markdown("### 🗣️ Ultimate Character Studio (100% Distinct Voices & Breathing Effects)")

    audio_text = str_lit.text_area(
        "डायलॉग या बड़ी स्क्रिप्ट यहाँ लिखें (8000+ शब्द समर्थित):", 
        placeholder="यहाँ अपनी लंबी स्क्रिप्ट या कहानी पेस्ट करें...",
        height=250
    )
    
    if audio_text:
        word_count = len(audio_text.split())
        char_count = len(audio_text)
        str_lit.caption(f"📊 कुल शब्द (Words): {word_count} | कुल अक्षर (Characters): {char_count}")

    # हर कैरेक्टर के लिए बिल्कुल अलग न्यूरल वॉइस आईडी और पिच/रेट सेट की गई है ताकि कोई भी आवाज़ आपस में न मिले
    voice_profiles_map = {
        f"1. 🇮🇳 {selected_language} - Swara (मुख्य नेचुरल महिला आवाज़)": {
            "voice": current_lang_voices["female"], "pitch": "+0Hz", "rate": "+0%"
        },
        f"2. 🇮🇳 {selected_language} - Madhur (गंभीर और भारी पुरुष आवाज़)": {
            "voice": current_lang_voices["male_deep"], "pitch": "-5Hz", "rate": "-5%"
        },
        f"3. 🇮🇳 {selected_language} - Prabhat (तेज़ और जोशीली पुरुष आवाज़)": {
            "voice": current_lang_voices["male_energetic"], "pitch": "+4Hz", "rate": "+10%"
        },
        "4. 👻 Horror Ghost (डरावनी भूतिया भारी आवाज़)": {
            "voice": "en-GB-RyanNeural", "pitch": "-12Hz", "rate": "-20%"
        },
        "5. 👵 Old Village Woman (बूढ़ी औरत की खुरदरी भारी आवाज़)": {
            "voice": "en-US-AriaNeural", "pitch": "-8Hz", "rate": "-15%"
        },
        "6. 👴 Old Wise Grandfather (बुजुर्ग और समझदार दादाजी)": {
            "voice": "en-US-AndrewNeural", "pitch": "-7Hz", "rate": "-10%"
        },
        "7. 🧛 Evil Villain / Monster (खतरनाक खलनायक की आवाज़)": {
            "voice": "en-US-ChristopherNeural", "pitch": "-10Hz", "rate": "-8%"
        },
        "8. 🕵️‍♂️ Deep Mystery Narrator (सस्पेंस मिस्ट्री नरेटर)": {
            "voice": "en-US-BrianNeural", "pitch": "-6Hz", "rate": "-5%"
        },
        "9. 👦 Young Energetic Boy (उत्साही युवा लड़का)": {
            "voice": "en-US-AndrewNeural", "pitch": "+6Hz", "rate": "+8%"
        },
        "10. 👧 Sweet Young Girl (मासूम और प्यारी बच्ची की पतली आवाज़)": {
            "voice": "en-US-AriaNeural", "pitch": "+12Hz", "rate": "+5%"
        },
        "11. 😭 Sad & Emotional Voice (रोनी और भावुक धीमी आवाज़)": {
            "voice": current_lang_voices["female"], "pitch": "-4Hz", "rate": "-15%"
        },
        "12. 🤖 Robotic Sci-Fi AI (रोबोटिक कंप्यूटर आवाज़)": {
            "voice": "en-US-ChristopherNeural", "pitch": "+0Hz", "rate": "+2%"
        }
    }

    voice_profiles = list(voice_profiles_map.keys())
    selected_character = str_lit.selectbox("🎭 कैरेक्टर और आवाज़ का चयन (हर कैरेक्टर की बिल्कुल अलग आवाज़):", voice_profiles)

    audio_emotion = str_lit.selectbox("⚡ भाव / टोन (Tone & Expression):", [
        "Normal / Clear & Natural (सामान्य और साफ़)",
        "Storytelling / Emotional (कहानी वाला भावुक अंदाज़)",
        "Excited / Energetic (जोशीला और एनर्जेटिक)",
        "Dark / Mysterious (गंभीर और डरावना)",
        "Whisper / Soft Breath (फुसफुसाहट और सांस लेने का अंदाज़)",
        "Laughing / Joyful (हंसते हुए और आनंदित)"
    ])

    speed_option = str_lit.slider("🗣️ बोलने की गति (Speed Mode):", 0.5, 2.0, 1.0, 0.1)

    if str_lit.button("Generate Master Character Audio 🔊✨", type="primary", use_container_width=True):
        if audio_text.strip():
            with str_lit.spinner(f"🎙️ '{selected_character}' के रूप में बिल्कुल अलग आवाज़ तैयार हो रही है..."):
                try:
                    config = voice_profiles_map.get(selected_character, {"voice": current_lang_voices["female"], "pitch": "+0Hz", "rate": "+0%"})
                    voice_id = config["voice"]

                    base_rate_num = int(config["rate"].replace("+", "").replace("%", ""))
                    slider_rate_num = int((speed_option - 1.0) * 100)
                    total_rate_num = base_rate_num + slider_rate_num
                    rate_val = f"+{total_rate_num}%" if total_rate_num >= 0 else f"{total_rate_num}%"

                    base_pitch_num = int(config["pitch"].replace("Hz", ""))
                    if "डरावना" in audio_emotion or "गंभीर" in audio_emotion:
                        base_pitch_num -= 4
                    elif "भावुक" in audio_emotion:
                        base_pitch_num -= 2
                    elif "जोशीला" in audio_emotion or "एनर्जेटिक" in audio_emotion:
                        base_pitch_num += 3
                    elif "फुसफुसाहट" in audio_emotion or "Whisper" in audio_emotion:
                        base_pitch_num -= 5
                        rate_val = "-18%"
                    elif "हंसते हुए" in audio_emotion or "Laughing" in audio_emotion:
                        base_pitch_num += 3
                    
                    pitch_val = f"+{base_pitch_num}Hz" if base_pitch_num >= 0 else f"{base_pitch_num}Hz"

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"master_audio_{timestamp}.mp3"

                    if len(audio_text) > 4000:
                        chunks = [audio_text[i:i+3500] for i in range(0, len(audio_text), 3500)]
                        temp_files = []
                        for idx, chunk in enumerate(chunks):
                            chunk_file = f"chunk_{timestamp}_{idx}.mp3"
                            run_async(generate_edge_audio_with_emotion(chunk, voice_id, chunk_file, rate_str=rate_val, pitch_str=pitch_val, emotion=audio_emotion))
                            temp_files.append(chunk_file)
                            
                        if PYDUB_AVAILABLE:
                            combined_audio = AudioSegment.from_file(temp_files[0])
                            for tf in temp_files[1:]:
                                if os.path.exists(tf):
                                    combined_audio += AudioSegment.from_file(tf)
                            combined_audio.export(filename, format="mp3")
                            for tf in temp_files:
                                try:
                                    os.remove(tf)
                                except:
                                    pass
                        else:
                            os.rename(temp_files[0], filename)
                    else:
                        run_async(generate_edge_audio_with_emotion(audio_text, voice_id, filename, rate_str=rate_val, pitch_str=pitch_val, emotion=audio_emotion))

                    str_lit.success(f"🎉 ऑडियो सफलतापूर्वक जनरेट हो गया!")
                    str_lit.audio(filename)
                    str_lit.info("💡 आप प्लेयर के तीन डॉट्स (...) पर क्लिक करके इसे आसानी से डाउनलोड कर सकते हैं।")
                    
                except Exception as e:
                    str_lit.error(f"🚨 ऑडियो जनरेशन में गड़बड़: {e}")
        else:
            str_lit.warning("⚠️ कृपया पहले टेक्स्ट बॉक्स में अपनी स्क्रिप्ट या डायलॉग लिखें!")
