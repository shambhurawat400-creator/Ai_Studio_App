import streamlit as st

def render_script_page(groq_client):
    st.subheader("📜 AI Video & Story Script Writer (Long-Form Pro)")
    topic = st.text_input("स्क्रिप्ट का टॉपिक/विषय दर्ज करें:", placeholder="जैसे: Horror story near a haunted well")
    script_type = st.selectbox("प्रकार:", ["YouTube Video (Full Script)", "Instagram Reel / Shorts", "Horror Story / Storytelling (Long-Form)"])
    
    # लंबाई और शब्दों का चयन करने का नया विकल्प
    length_option = st.selectbox("लगभग कितने शब्दों की स्क्रिप्ट चाहिए?", [
        "छोटी स्क्रिप्ट (500 - 1000 शब्द)",
        "मध्यम स्क्रिप्ट (2000 - 3000 शब्द)",
        "बड़ी महाकाव्य/लंबी कहानी (5000+ शब्द)"
    ])

    if st.button("Generate Long Script ✍️", type="primary", use_container_width=True):
        if topic.strip():
            with st.spinner("AI लंबी स्क्रिप्ट और कहानी तैयार कर रहा है (कृपया प्रतीक्षा करें)..."):
                try:
                    full_script = ""
                    
                    # यदि यूजर को लंबी या बहुत बड़ी कहानी चाहिए, तो हम उसे पार्ट्स में जनरेट करेंगे
                    if "5000+" in length_option:
                        parts = 4  # 4 भागों में विभाजित करके लंबी कहानी लिखेंगे
                        words_per_part = "लगभग 1200-1500 शब्दों का विस्तार"
                    elif "2000 - 3000" in length_option:
                        parts = 2  # 2 भागों में विभाजित करेंगे
                        words_per_part = "लगभग 1000-1500 शब्दों का विस्तार"
                    else:
                        parts = 1
                        words_per_part = "लगभग 500-800 शब्दों का विस्तार"

                    previous_context = ""
                    
                    for i in range(1, parts + 1):
                        if parts > 1:
                            prompt = f"""You are an expert scriptwriter and storyteller. 
                            Write Part {i} of {parts} for a detailed {script_type} in Hindi/Hinglish on the topic: '{topic}'.
                            Length requirement: {words_per_part}.
                            Previous part context (maintain flow from here): '{previous_context[-300:]}'
                            Include vivid scene descriptions, emotional dialogues, and a gripping narrative. Do not stop abruptly."""
                        else:
                            prompt = f"Write a detailed {script_type} in Hindi/Hinglish on topic: '{topic}'. Include scene details, detailed dialogues, and a complete narrative arc."

                        response = groq_client.chat.completions.create(
                            model="llama-3.1-8b-instant", 
                            messages=[{"role": "user", "content": prompt}],
                            max_tokens=4000  # टोकن की सीमा को अधिकतम किया गया है ताकि लंबा आउटपुट मिले
                        )
                        
                        part_content = response.choices[0].message.content
                        full_script += f"\n\n--- [ भाग / Part {i} ] ---\n\n" + part_content
                        previous_context = part_content

                    st.text_area("आपकी पूरी स्क्रिप्ट (Long-Form):", value=full_script, height=450)
                    
                    # डाउनलोड बटन ताकि आप इसे आसानी से सेव कर सकें
                    st.download_button(
                        label="📥 Download Script as Text File",
                        data=full_script,
                        file_name=f"script_{topic[:15].strip()}.txt",
                        mime="text/plain"
                    )

                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
            st.warning("कृपया पहले टॉपिक दर्ज करें!")
