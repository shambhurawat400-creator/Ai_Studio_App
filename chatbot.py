import streamlit as st
from groq import Groq

def render_chatbot_page(groq_client):
    st.subheader("💬 AI Chat Assistant")
    st.write("यहाँ आप AI से किसी भी तरह की मदद, आइडिया या सवाल पूछ सकते हैं:")

    # सुरक्षित तरीके से API Key सेट की गई है
    SECURE_API_KEY = "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"
    
    active_client = groq_client
    if not active_client:
        try:
            active_client = Groq(api_key=SECURE_API_KEY)
        except Exception:
            pass

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # पुराने मैसेज स्क्रीन पर दिखाएं
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # यूजर का नया मैसेज इनपुट लें
    if user_query := st.chat_input("अपना सवाल यहाँ पूछें..."):
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        if not active_client:
            st.error("🚨 API Client कनेक्ट नहीं हो पाया है!")
        else:
            with st.chat_message("assistant"):
                with st.spinner("AI सोच रहा है..."):
                    try:
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
