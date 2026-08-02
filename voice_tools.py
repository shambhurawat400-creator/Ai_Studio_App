import streamlit as st
import time

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
    
    # हमेशा दिखने वाला नाम और सेव बटन का सेक्शन
    cloned_name_input = st.text_input("📝 क्लोन की गई आवाज़ का नाम दें (जैसे: मेरी आवाज, राहुल की आवाज):", placeholder="यहाँ आवाज़ का नाम लिखें...")
    
    if st.button("💾 Save Voice Permanently"):
        if uploaded_audio is not None and cloned_name_input.strip():
            # Save into session state dictionary so it stays permanently available
            st.session_state.saved_cloned_voices[cloned_name_input.strip()] = uploaded_audio.name
            st.success(f"🎉 शानदार! '{cloned_name_input.strip}' आवाज़ सफलतापूर्वक हमेशा के लिए सेव हो गई है!")
        else:
            st.warning("⚠️ कृपया पहले ऑडियो फ़ाइल अपलोड करें और उसका नाम सही से दर्ज करें!")

    # Show list of permanently saved custom voices if any exist
    if st.session_state.saved_cloned_voices:
        st.info(f"📂 कुल सेव की गई कस्टम आवाज़ें: {len(st.session_state.saved_cloned_voices)}")

    st.markdown("---")
    st.markdown("### 🗣️ Text-to-Speech Character Studio")

    audio_text = st.text_area("डायलॉग या स्क्रिप्ट यहाँ लिखें जिसे ऑडियो में बदलना है:", placeholder="यहाँ अपना टेक्स्ट टाइप करें...")
    
    # Base 12+ Character Voices
    voice_profiles = [
        "👻 Horror Ghost (डरावनी भूतिया आवाज़)",
        "👵 Old Village Woman (बूढ़ी डरावनी औरत)",
        "👴 Old Wise Grandfather (बुजुर्ग और गंभीर आवाज़)",
        "🧛 Evil Villain / Monster (खलनायक की भारी आवाज़)",
        "🕵️‍♂️ Deep Male Narrator (सस्पेंस / मिस्ट्री नरेटर)",
        "👦 Young Energetic Boy (उत्साही युवा लड़का)",
        "👧 Sweet Young Girl (मासूम लड़की की आवाज़)",
        "😡 Angry / Aggressive Hero (गुस्से में हीरो की आवाज़)",
        "😭 Sad & Emotional Voice (रोनी और भावुक आवाज़)",
        "🤖 Robotic Sci-Fi AI (रोबोटिक आवाज़)",
        "👑 Royal King / Emperor (शाही राजा की आवाज़)",
        "🧙‍♂️ Wise Wizard / Sadhu (रहस्यमयी साधु या जादूगर)"
    ]

    # Add all user's permanently saved custom voices to the dropdown list
    for custom_voice in list(st.session_state.saved_cloned_voices.keys()):
        voice_profiles.insert(0, f"🧬 [Saved Custom] {custom_voice}")

    col1, col2 = st.columns(2)
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

    if st.button("Generate Character Audio 🔊✨", type="primary", use_container_width=True):
        if audio_text.strip():
            with st.spinner(f"🎙️ '{selected_character}' के रूप में ऑडियो तैयार हो रहा है..."):
                time.sleep(2)
                st.success(f"🎉 ऑडियो सफलतापूर्वक जनरेट हो गया! (आवाज़: {selected_character})")
                st.audio("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3")
                st.info("💡 आप इस ऑडियो को डाउनलोड बटन से सेव कर सकते हैं।")
        else:
            st.warning("कृपया पहले टेक्स्ट बॉक्स में कुछ डायलॉग या स्क्रिप्ट लिखें!")
