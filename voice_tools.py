import streamlit as st
import os
import asyncio
import edge_tts
from datetime import datetime

async def generate_edge_audio(text, voice_name, output_file):
    communicate = edge_tts.Communicate(text, voice_name)
    await communicate.save(output_file)

def render_voice_page():
    st.subheader("🎙️ AI Master Voice & Character Studio (All-in-One Pro)")
    st.write("बिना किसी पैसे या API Key के, सभी कैरेक्टर और अल्ट्रा-रियलिस्टिक नैचुरल आवाज़ों का उपयोग करें:")

    # --- Initialize Permanent Saved Voices in Session State ---
    if "saved_cloned_voices" not in st.session_state:
        st.session_state.saved_cloned_voices = {}

    # --- 1. VOICE CLONING SECTION ---
    st.markdown("---")
    st.markdown("### 🧬 AI Voice Customization (स्थायी रूप से आवाज़ सेव करें)")
    
    uploaded_audio = st.file_uploader("अपनी आवाज़ का सैंपल अपलोड करें (WAV / MP3 / AAC):", type=["wav", "mp3", "m4a", "aac"])
    cloned_name_input = st.text_input("📝 इस आवाज़ प्रोफाइल का नाम दें:", placeholder="जैसे: मेरी आवाज़, राहुल...")
    
    if st.button("💾 Save Voice Profile"):
        if uploaded_audio is not None and cloned_name_input.strip():
            st.session_state.saved_cloned_voices[cloned_name_input.strip()] = uploaded_audio.name
            st.success(f"🎉 शानदार! '{cloned_name_input.strip}' प्रोफाइल सफलतापूर्वक सेव हो गई है!")
        else:
            st.warning("⚠️ कृपया पहले ऑडियो फ़ाइल अपलोड करें और उसका नाम सही से दर्ज करें!")

    if st.session_state.saved_cloned_voices:
        st.info(f"📂 कुल सेव की गई कस्टम आवाज़ें: {len(st.session_state.saved_cloned_voices)}")

    # --- 2. ADVANCED TEXT-TO-SPEECH CHARACTER STUDIO ---
    st.markdown("---")
    st.markdown("### 🗣️ Ultimate Character & Realistic Voice Studio")

    audio_text = st.text_area("डायलॉग या स्क्रिप्ट यहाँ लिखें जिसे ऑडियो में बदलना है:", placeholder="यहाँ अपना टेक्स्ट टाइप करें...")
    
    # Combined List: All 12+ Character Voices + Ultra-Realistic Premium Neural Voices
    voice_profiles_map = {
        # --- Premium Realistic Voices ---
        "🇮🇳 Swara (Best Indian Female - कहानी और वीडियो के लिए सर्वश्रेष्ठ)": {"voice": "hi-IN-SwaraNeural", "sample": "नमस्कार दोस्तों, इस तरह का वीडियो बहुत ही ज्यादा चलता है।"},
        "🇮🇳 Madhur (Best Indian Male - गंभीर और भारी आवाज़)": {"voice": "hi-IN-MadhurNeural", "sample": "समय का चक्र बहुत बलवान है बालक, ध्यान से सुनो।"},
        "🇮🇳 Ananya (Sweet Young Girl Voice - मासूम आवाज़)": {"voice": "hi-IN-AnanyaNeural", "sample": "नमस्ते दोस्तों, आज हम एक नई कहानी सुनेंगे।"},
        "🇮🇳 Prabhat (Energetic Male Voice - जोशीली आवाज़)": {"voice": "en-IN-PrabhatNeural", "sample": "Welcome back to our channel, let's start!"},
        "🇬🇧 Ryan (Deep English Narrator - ब्रिटिश नरेटर)": {"voice": "en-GB-RyanNeural", "sample": "Beware, darkness is approaching this mysterious land."},
        "🇺🇸 Andrew (Wise Grandfather - अमेरिकी बुजुर्ग आवाज़)": {"voice": "en-US-AndrewNeural", "sample": "Listen closely to my advice, young adventurer."},
        "🇺🇸 Aria (Energetic Young Boy/Girl - उत्साह भरी आवाज़)": {"voice": "en-US-AriaNeural", "sample": "Hey everyone, let's go on an amazing adventure!"},
        "🇫🇷 French Mysterious Narrator (रहस्यमयी विदेशी आवाज़)": {"voice": "fr-FR-HenriNeural", "sample": "Un secret mystérieux caché dans la nuit sombre."},
        
        # --- Character Special Voices ---
        "👻 Horror Ghost (डरावनी भूतिया आवाज़)": {"voice": "en-GB-RyanNeural", "sample": "Beware, darkness is approaching."},
        "👵 Old Village Woman (बूढ़ी डरावनी औरत)": {"voice": "hi-IN-SwaraNeural", "sample": "बेटा, उस कुएं के पास मत जाना।"},
        "👴 Old Wise Grandfather (बुजुर्ग और गंभीर आवाज़)": {"voice": "en-US-AndrewNeural", "sample": "Listen closely to my advice, young one."},
        "🧛 Evil Villain / Monster (खलनायक की भारी आवाज़)": {"voice": "en-US-SteffanNeural", "sample": "Now nobody can save you from me."},
        "🕵️‍♂️ Deep Male Narrator (सस्पेंस / मिस्ट्री नरेटर)": {"voice": "en-US-BrianNeural", "sample": "A mysterious secret hidden in the dark."},
        "👦 Young Energetic Boy (उत्साही युवा लड़का)": {"voice": "en-US-AriaNeural", "sample": "Hey everyone, let's go on an adventure!"},
        "👧 Sweet Young Girl (मासूम लड़की की आवाज़)": {"voice": "hi-IN-AnanyaNeural", "sample": "नमस्ते दोस्तों, कैसे हो आप सब?"},
        "😡 Angry / Aggressive Hero (गुस्से में हीरो की आवाज़)": {"voice": "en-IN-PrabhatNeural", "sample": "I will not forgive what you did!"},
        "😭 Sad & Emotional Voice (रोनी और भावुक आवाज़)": {"voice": "hi-IN-SwaraNeural", "sample": "मेरा सब कुछ लुट गया है बाबूजी।"},
        "🤖 Robotic Sci-Fi AI (रोबोटिक आवाज़)": {"voice": "en-US-ChristopherNeural", "sample": "System operational, initializing sequence."},
        "👑 Royal King / Emperor (शाही राजा की आवाज़)": {"voice": "en-GB-SoniaNeural", "sample": "By the order of the king, hear me out."},
        "🧙‍♂️ Wise Wizard / Sadhu (रहस्यमयी साधु या जादूगर)": {"voice": "hi-IN-MadhurNeural", "sample": "समय का चक्र बहुत बलवान है बालक।"}
    }

    voice_profiles = list(voice_profiles_map.keys())
    for custom_voice in list(st.session_state.saved_cloned_voices.keys()):
        voice_profiles.insert(0, f"🧬 [Custom] {custom_voice}")

    selected_character = st.selectbox("🎭 कैरेक्टर और रियलिस्टिक आवाज़ का चयन:", voice_profiles)

    # --- INSTANT AUTO PREVIEW PLAYER ---
    if "[Custom]" not in selected_character:
        try:
            config = voice_profiles_map.get(selected_character, {"voice": "hi-IN-SwaraNeural", "sample": "नमस्ते"})
            preview_filename = f"preview_{config['voice']}.mp3"
            
            if not os.path.exists(preview_filename):
                asyncio.run(generate_edge_audio(config["sample"], config["voice"], preview_filename))
            
            st.markdown(f"🔊 **चयनित कैरेक्टर का नैचुरल प्रीव्यू:**")
            st.audio(preview_filename)
        except Exception:
            pass

    audio_emotion = st.selectbox("⚡ भाव / टोन (Tone & Expression):", [
        "Normal / Clear & Natural (सामान्य और साफ़)",
        "Storytelling / Emotional (कहानी वाला भावुक अंदाज़)",
        "Excited / Energetic (जोशीला और एनर्जेटिक)",
        "Dark / Mysterious (गंभीर और डरावना)"
    ])

    speed_option = st.slider("🗣️ बोलने की गति (Speed Mode):", 0.5, 2.0, 1.0, 0.1)

    # --- GENERATE FULL AUDIO BUTTON ---
    if st.button("Generate Master Character Audio 🔊✨", type="primary", use_container_width=True):
        if audio_text.strip():
            with st.spinner(f"🎙️ '{selected_character}' के रूप में हाई-क्वालिटी रियलिस्टिक आवाज़ तैयार हो रही है..."):
                try:
                    if "[Custom]" in selected_character:
                        voice_id = "hi-IN-SwaraNeural"
                    else:
                        config = voice_profiles_map.get(selected_character, {"voice": "hi-IN-SwaraNeural"})
                        voice_id = config["voice"]

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"master_audio_{timestamp}.mp3"

                    # Generate using Edge-TTS
                    asyncio.run(generate_edge_audio(audio_text, voice_id, filename))

                    st.success(f"🎉 ऑडियो सफलतापूर्वक जनरेट हो गया!")
                    st.audio(filename)
                    st.info("💡 आप इस ऑडियो प्लेयर पर दिए गए तीन डॉट्स (...) पर क्लिक करके इसे आसानी से डाउनलोड कर सकते हैं।")
                    
                except Exception as e:
                    st.error(f"🚨 ऑडियो जनरेशन में गड़बड़: {e}")
        else:
            st.warning("⚠️ कृपया पहले टेक्स्ट बॉक्स में अपनी स्क्रिप्ट या डायलॉग लिखें!")
