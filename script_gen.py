import streamlit as st

def render_script_page(groq_client):
    st.subheader("📜 AI Video & Story Script Writer")
    topic = st.text_input("स्क्रिप्ट का टॉपिक/विषय दर्ज करें:", placeholder="जैसे: Horror story near a haunted well")
    script_type = st.selectbox("प्रकार:", ["YouTube Video (Full Script)", "Instagram Reel / Shorts", "Horror Story / Storytelling"])

    if st.button("Generate Script ✍️", type="primary", use_container_width=True):
        if topic.strip():
            with st.spinner("AI स्क्रिप्ट लिख रहा है..."):
                try:
                    prompt = f"Write a detailed {script_type} in Hindi/Hinglish on topic: '{topic}'. Include scene details and dialogues."
                    response = groq_client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": prompt}])
                    st.text_area("आपकी स्क्रिप्ट:", value=response.choices[0].message.content, height=350)
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
                    st.warning("कृपया पहले टॉपिक दर्ज करें!")
