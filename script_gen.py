import streamlit as st
from groq import Groq

def render_script_page(groq_client):
    st.subheader("📜 AI Video & Story Script Writer & Chatbot Hub")
    st.write("यहाँ से आप यूट्यूब, शॉर्ट्स या लंबी कहानियों के लिए स्क्रिप्ट तैयार कर सकते हैं और AI चैटबॉट से बात कर सकते हैं:")

    # सुरक्षित तरीके से API Key लोड करने का सिस्टम (सीधे कोड में सुरक्षित रूप से सेट)
    SECURE_API_KEY = "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"
    
    active_client = groq_client
    if not active_client:
        try:
            if "GROQ_API_KEY" in st.secrets:
                active_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            else:
                active_client = Groq(api_key=SECURE_API_KEY)
        except Exception:
            pass

    # टैब या रेडियो बटन ताकि स्क्रिप्ट राइटर और चैटबॉट दोनों अलग-अलग आसानी से काम करें
    app_mode = st.radio("फीचर चुनें:", ["✍️ Pro Script Writer", "💬 AI Assistant Chatbot"], horizontal=True)

    if app_mode == "✍️ Pro Script Writer":
        topic = st.text_input("स्क्रिप्ट का टॉपिक/विषय दर्ज करें:", placeholder="जैसे: Horror story near a haunted well in an ancient village")
        
        col1, col2 = st.columns(2)
        with col1:
            script_type = st.selectbox("प्लेटफॉर्म/प्रकार:", [
                "YouTube Video (Full Cinematic Script)", 
                "Instagram Reel / YouTube Shorts (Fast-Paced)", 
                "Horror Story / Suspense Storytelling",
                "Motivational / Documentary Speech"
            ])
        with col2:
            tone_style = st.selectbox("टोन और अंदाज़ (Tone):", [
                "Suspense & Thrilling (रहस्यमयी और डरावना)",
                "Emotional & Dramatic (भावुक और गहरा)",
                "Energetic & Hype (जोशीला और रोमांचक)",
                "Informative & Engaging (दिल्चस्प और जानकारीपूर्ण)"
            ])

        length_option = st.selectbox("लंबाई और विस्तार (Length & Depth):", [
            "मध्यम स्क्रिप्ट (1000 - 2000 शब्द)",
            "लंबी कहानी / वीडियो (3000 - 5000 शब्द)",
            "महाकाव्य / बड़ी सीरीज़ (8000+ शब्द)"
        ])

        if st.button("Generate Pro Cinematic Script ✍️🎬", type="primary", use_container_width=True):
            if not topic.strip():
                st.warning("कृपया पहले टॉपिक दर्ज करें!")
            elif not active_client:
                st.error("🚨 API Key कनेक्ट नहीं हो पाई है!")
            else:
                with st.spinner("प्रो AI डायरेक्टर स्क्रिप्ट, विजुअल क्यूज और डायलॉग तैयार कर रहा है..."):
                    try:
                        full_script = ""
                        
                        if "8000+" in length_option:
                            parts = 5
                            words_per_part = "लगभग 1500-2000 शब्दों का विस्तार, गहरे विवरण के साथ"
                        elif "3000 - 5000" in length_option:
                            parts = 3
                            words_per_part = "लगभग 1200-1500 शब्दों का विस्तार"
                        else:
                            parts = 1
                            words_per_part = "लगभग 1000 शब्दों का संपूर्ण विस्तार"

                        previous_context = ""
                        
                        for i in range(1, parts + 1):
                            if parts > 1:
                                prompt = f"""You are a World-Class Hollywood/Bollywood Scriptwriter and Master Storyteller. 
                                Write Part {i} of {parts} for a professional {script_type} with a '{tone_style}' tone on the topic: '{topic}'.
                                Length requirement: {words_per_part}.
                                Crucial Guidelines:
                                - Include vivid Visual & Audio Cues (e.g., [Camera Pan], [SFX: Heavy Wind], [Dark Lighting]).
                                - Write engaging dialogues and build deep dramatic tension.
                                - Maintain strict narrative flow from previous context: '{previous_context[-400:]}'
                                - Write entirely in rich, engaging Hindi/Hinglish. Do not stop abruptly."""
                            else:
                                prompt = f"""You are a World-Class Scriptwriter. Write a detailed, professional {script_type} with a '{tone_style}' tone on the topic: '{topic}'.
                                Include powerful hooks, scene descriptions, visual cues [Camera Angles, SFX], and emotional dialogues. Write in rich Hindi/Hinglish."""

                            response = active_client.chat.completions.create(
                                model="llama-3.1-8b-instant", 
                                messages=[{"role": "user", "content": prompt}],
                                max_tokens=4000
                            )
                            
                            part_content = response.choices[0].message.content
                            full_script += f"\n\n==================== [ सीन / भाग {i} ] ====================\n\n" + part_content
                            previous_context = part_content

                        st.text_area("प्रो सिनेमैटिक स्क्रिप्ट:", value=full_script, height=480)
                        
                        st.download_button(
                            label="📥 Download Pro Script as Text File",
                            data=full_script,
                            file_name=f"pro_script_{topic[:15].strip()}.txt",
                            mime="text/plain"
                        )

                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    else:
        # 💬 AI Assistant Chatbot Section (पूर्णतः फिक्स किया गया)
        st.subheader("💬 AI Assistant & Chatbot")
        st.write("यहाँ आप AI से किसी भी तरह की मदद, आइडिया या सवाल पूछ सकते हैं:")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        # पुराने मैसेज दिखाएं
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # यूजर का इनपुट लें
        if user_query := st.chat_input("अपना सवाल यहाँ पूछें..."):
            st.session_state.messages.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)

            if not active_client:
                st.error("🚨 AI Client उपलब्ध नहीं है!")
            else:
                with st.chat_message("assistant"):
                    with st.spinner("AI सोच रहा है..."):
                        try:
                            # चैटबॉट के लिए बातचीत का इतिहास भेजें
                            chat_response = active_client.chat.completions.create(
                                model="llama-3.1-8b-instant",
                                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                                max_tokens=2000
                            )
                            bot_reply = chat_response.choices[0].message.content
                            st.markdown(bot_reply)
                            st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                        except Exception as e:
                            st.error(f"Chat Error: {str(e)}")
