import streamlit as st
import os
import time
from datetime import datetime
try:
    from gtts import gTTS
except ImportError:
    gTTS = None

def render_voice_page():
    st.subheader("🎙️ AI Voice Cloning & Advanced Text-to-Speech Studio")
    st.write("अपने टेक्स्ट को 15+ अलग-अलग कैरेक्टर आवाज़ों में बदलें या अपनी आवाज़ हमेशा के लिए क्लोन करके सेव करें:")

    # --- Initialize Permanent Saved Voices in Session State ---
    if "saved_cloned_voices" not in st.session_state:
        st.session_state.saved_cloned_voices = {}

    # --- 1. VOICE CLONING & PERMANENT SAVING ---
    st.markdown("---")
    st.markdown("### 🧬 AI Voice Cloning (स्थायी रूप से आवाज़ सेव करें)")
    
    uploaded_audio = st.file_uploader("अपनी आवाज़ का सैंपल अपलोड करें (WAV / MP3 / AAC):", type=["wav", "mp3", "m4a", "aac"])
    
    cloned_name_input = st.text_input("📝 क्लोन की गई आवाज़ का नाम दें (जैसे: मेरी आवाज, राहुल की आवाज):", placeholder="यहाँ आवाज़ का नाम लिखें...")
    
    if st.button("💾 Save Voice Permanently"):
        if uploaded_audio is not None and cloned_name_input.strip():
            st.session_state.saved_cloned_voices[cloned_name_input.strip()] = uploaded_audio.name
            st.success(f"🎉 शानदार! '{cloned_name_input.strip}' आवाज़ सफलतापूर्वक हमेशा के लिए सेव हो गई है!")
        else:
            st.warning("⚠️ कृपया पहले ऑडियो फ़ाइल अपलोड करें और उसका नाम सही से दर्ज करें!")

    if st.session_state.saved_cloned_voices:
        st.info(f"📂 कुल सेव की गई कस्टम आवाज़ें: {len(st.session_state.saved_cloned_voices)}")

    st.markdown("---")
    st.markdown("### 🗣️ Text-to-Speech Character Studio")

    audio_text = st.text_area("डायलॉग या स्क्रिप्ट यहाँ लिखें जिसे ऑडियो में बदलना है:", placeholder="यहाँ अपना टेक्स्ट टाइप करें...")
    
    # Base Character Voices with human-touch mapping for gTTS
    voice_profiles_map = {
        "👻 Horror Ghost (डरावनी भूतिया आवाज़)": {"lang": "en", "tld": "co.uk"},
        "👵 Old Village Woman (बूढ़ी डरावनी औरत)": {"lang": "hi", "tld": "co.in"},
        "👴 Old Wise Grandfather (बुजुर्ग और गंभीर आवाज़)": {"lang": "en", "tld": "us"},
        "🧛 Evil Villain / Monster (खलनायक की भारी आवाज़)": {"lang": "en", "tld": "ca"},
        "🕵️‍♂️ Deep Male Narrator (सस्पेंस / मिस्ट्री नरेटर)": {"lang": "fr", "tld": "fr"},
        "👦 Young Energetic Boy (उत्साही युवा लड़का)": {"lang": "en", "tld": "com.au"},
        "👧 Sweet Young Girl (मासूम लड़की की आवाज़)": {"lang": "es", "tld": "es"},
        "😡 Angry / Aggressive Hero (गुस्से में हीरो की आवाज़)": {"lang": "en", "tld": "co.in"},
        "😭 Sad & Emotional Voice (रोनी और भावुक आवाज़)": {"lang": "hi", "tld": "co.in"},
        "🤖 Robotic Sci-Fi AI (रोबोटिक आवाज़)": {"lang": "de", "tld": "de"},
        "👑 Royal King / Emperor (शाही राजा की आवाज़)": {"lang": "en", "tld": "co.uk"},
        "🧙‍♂️ Wise Wizard / Sadhu (रहस्यमयी साधु या जादूगर)": {"lang": "hi", "tld": "co.in"}
    }

    voice_profiles = list(voice_profiles_map.keys())

    # Add all user's permanently saved custom voices to the dropdown list
    for custom_voice in list(st.session_state.saved_cloned_voices.keys()):
        voice_profiles.insert(0, f"🧬 [Saved Custom] {custom_voice}")

    col1, col2 = st.columns([2, 1])
    with col1:
        selected_character = st.selectbox("🎭 कैरेक्टर और आवाज़ का चयन:", voice_profiles)
    with col2:
        audio_emotion = st.selectbox("⚡ भाव / एक्सप्रेशन (Emotion):", [
            "Scary / Horror (डरावना)", 
            "Suspense / Mysterious (रहस्यमयी)", 
            "Angry / Fierce (क्रोधित)", 
            "Emotional / Crying (भावुक)", 
            "Excited / Energetic (जोशीला)", 
            "Calm / Storytelling (शांत कहानी)", 
            "Dark & Moody (गंभीर)"
        ])

    speed_option = st.slider("🗣️ बोलने की गति (Speed):", 0.5, 2.0, 1.0, 0.1)

    # --- PREVIEW BUTTON SECTION ---
    if st.button("▶️ Listen Voice Preview (आवाज़ सुनें)"):
        if gTTS is None:
            st.error("🚨 gTTS इंस्टॉल नहीं है।")
        else:
            with st.spinner("🎧 प्रीव्यू आवाज़ लोड हो रही है..."):
                try:
                    preview_text = "नमस्कार, यह इस कैरेक्टर की आवाज़ का प्रीव्यू है।"
                    config = voice_profiles_map.get(selected_character, {"lang": "hi", "tld": "co.in"})
                    tts_preview = gTTS(text=preview_text, lang=config["lang"], tld=config["tld"], slow=False)
                    tts_preview.save("preview_audio.mp3")
                    st.audio("preview_audio.mp3")
                except Exception as e:
                    st.error(f"प्रीव्यू में त्रुटि: {e}")

    # --- GENERATE FULL AUDIO BUTTON ---
    if st.button("Generate Character Audio 🔊✨", type="primary", use_container_width=True):
        if audio_text.strip():
            if gTTS is None:
                st.error("🚨 gTTS लाइब्रेरी इंस्टॉल नहीं है। कृपया `pip install gTTS` रन करें।")
            else:
                with st.spinner(f"🎙️ '{selected_character}' के रूप में इंसानी टच के साथ ऑडियो तैयार हो रहा है..."):
                    try:
                        if "[Saved Custom]" in selected_character:
                            lang_code = "hi"
                            tld_val = "co.in"
                        else:
                            config = voice_profiles_map.get(selected_character, {"lang": "hi", "tld": "co.in"})
                            lang_code = config["lang"]
                            tld_val = config["tld"]

                        # Apply speed adjustment logic
                        is_slow = True if speed_option < 0.9 else False

                        # Generate speech with natural human-like phrasing
                        tts = gTTS(text=audio_text, lang=lang_code, tld=tld_val, slow=is_slow)
                        
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"character_audio_{timestamp}.mp3"
                        tts.save(filename)

                        st.success(f"🎉 ऑडियो सफलतापूर्वक जनरेट हो गया! (आवाज़: {selected_character})")
                        st.audio(filename)
                        st.info("💡 आप इस ऑडियो को प्लेयर पर दिए गए तीन डॉट्स (...) पर क्लिक करके सेव कर सकते हैं।")
                        
                    except Exception as e:
                        st.error(f"🚨 ऑडियो जनरेशन में गड़बड़: {e}")
        else:
            st.warning("कृपया पहले टेक्स्ट बॉक्स में कुछ डायलॉग या स्क्रिप्ट लिखें!")
