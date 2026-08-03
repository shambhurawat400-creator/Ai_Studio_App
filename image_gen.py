import streamlit as st
import urllib.parse
from datetime import datetime

def render_image_page():
    st.subheader("🎨 Free AI Text-to-Image Studio")
    st.write("अपना विवरण लिखें और शानदार तस्वीरें मुफ्त में बनाएं:")

    # --- Session State Initialization ---
    if "image_history" not in st.session_state:
        st.session_state.image_history = []
    if "saved_projects" not in st.session_state:
        st.session_state.saved_projects = []

    # --- UI Elements ---
    img_prompt = st.text_area("✨ Prompt Box (मुख्य विवरण):", placeholder="A futuristic city at sunset, neon lights, cinematic...")
    neg_prompt = st.text_area("🚫 Negative Prompt (जो चीज़ें इमेज में नहीं चाहिए):", placeholder="blurry, dark, low quality, deformed")

    st.markdown("### 🎭 Style Selection (शैलियों का चयन)")
    style_option = st.selectbox("चुनें अपना पसंदीदा आर्ट स्टाइल:", [
        "Cinematic", "Realistic", "Anime", "Pixar", "3D", 
        "2D", "Cartoon", "Fantasy", "Sci-Fi", 
        "Watercolor", "Oil Painting"
    ])

    col1, col2, col3 = st.columns(3)
    
    with col1:
        ratio_option = st.selectbox("📐 Aspect Ratio", ["Landscape (16:9)", "Portrait (9:16)", "Square (1:1)"])
        if "16:9" in ratio_option:
            width, height = 1280, 720
        elif "9:16" in ratio_option:
            width, height = 720, 1280
        else:
            width, height = 1024, 1024

    with col2:
        quality_mode = st.selectbox("⚡ Quality Mode", ["High Definition (HD)", "Standard"])
        if "HD" in quality_mode:
            width, height = int(width * 1.25), int(height * 1.25)

    with col3:
        num_images = st.slider("🔢 Number of Images", 1, 4, 1)

    # --- Generate Logic ---
    if st.button("🚀 Generate Images Now", type="primary", use_container_width=True):
        if img_prompt.strip():
            with st.spinner(f"🎨 {style_option} स्टाइल में इमेज रेंडर हो रही है... कृपया प्रतीक्षा करें."):
                
                # --- Style Enhancers ---
                # ये शब्द आपके प्रॉम्प्ट में जुड़कर इमेज की क्वालिटी और स्टाइल को बेहतर बनाते हैं।
                style_tags_map = {
                    "Cinematic": "cinematic lighting, detailed, high quality, 8k",
                    "Realistic": "photo-realistic, highly detailed, 8k resolution",
                    "Anime": "high quality anime art, vibrant colors",
                    "Pixar": "3d disney pixar style animation, cute",
                    "3D": "octane render, 3d blender art, volumetric lighting",
                    "2D": "classic 2d vector art, clean lines",
                    "Cartoon": "fun cartoon style, bright colors",
                    "Fantasy": "magical fantasy art, ethereal",
                    "Sci-Fi": "futuristic sci-fi concept art, neon",
                    "Watercolor": "soft watercolor painting style",
                    "Oil Painting": "classic oil painting on canvas"
                }
                
                current_style_tag = style_tags_map.get(style_option, "masterpiece, 8k")
                clean_input = img_prompt.strip()
                final_prompt = f"{clean_input}, {current_style_tag}"
                
                # --- Negative Prompt Handling ---
                if not neg_prompt.strip():
                    default_neg = "blurry, deformed eyes, low quality, bad anatomy"
                    final_neg = default_neg
                else:
                    final_neg = neg_prompt.strip()

                # --- URL Encoding (CRITICAL) ---
                # प्रॉम्प्ट में special characters (जैसे space, comma) को वेब के लिए safe URL में बदला जाता है।
                encoded_prompt = urllib.parse.quote(final_prompt)
                encoded_neg = urllib.parse.quote(final_neg)
                
                # --- Image URL Generation ---
                # यह Pollinations AI का फ्री API URL है। हम सीधे इमेज का लिंक बना रहे हैं।
                generated_urls = []
                for i in range(num_images):
                    # हर इमेज के लिए unique seed देने से वह अलग-अलग बनती है।
                    seed_val = datetime.now().microsecond + i
                    # model=flux is the best free model available on pollinations.ai
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={seed_val}&model=flux&nologo=true&negative={encoded_neg}"
                    generated_urls.append(image_url)

                st.success(f"✨ सफलतापूर्वक {num_images} इमेज तैयार हो गई हैं!")

                # --- Display & Save ---
                cols = st.columns(min(num_images, 2)) # 1 ya 2 columns mein dikhayega
                for idx, url in enumerate(generated_urls):
                    with cols[idx % len(cols)]:
                        # Image dikhata hai
                        st.image(url, caption=f"Style: {style_option} | #{idx+1}", use_column_width=True)
                        # Direct Download Link
                        st.markdown(f"[📥 Download Image {idx+1}]({url})")
                        
                        # Save Button
                        if st.button(f"💾 Save Project #{idx+1}", key=f"save_{seed_val}_{idx}"):
                            project_data = {"prompt": img_prompt, "style": style_option, "url": url}
                            if project_data not in st.session_state.saved_projects:
                                st.session_state.saved_projects.append(project_data)
                                st.success("📁 प्रोजेक्ट सफलतापूर्वक सेव हो गया!")

                # --- History Update ---
                st.session_state.image_history.insert(0, {"prompt": img_prompt, "style": style_option, "url": generated_urls[0]})
        else:
            st.warning("⚠️ कृपया पहले प्रॉम्प्ट बॉक्स में इमेज का विवरण (Prompt) दर्ज करें!")

    # --- Sidebar for History & Saved Projects ---
    st.sidebar.markdown("---")
    tab1, tab2 = st.sidebar.tabs(["📂 Saved Projects", "📜 Generation History"])

    with tab1:
        st.subheader("आपके सेव किए गए प्रोजेक्ट्स")
        if st.session_state.saved_projects:
            for p_idx, proj in enumerate(st.session_state.saved_projects):
                st.write(f"**{p_idx+1}. Style:** {proj['style']} | **Prompt:** {proj['prompt']}")
                st.image(proj['url'], width=300)
                st.write("---")
        else:
            st.info("कोई प्रोजेक्ट सेव नहीं है।")

    with tab2:
        st.subheader("पिछली जनरेट की गई इमेजेस (History)")
        if st.session_state.image_history:
            for h_idx, hist in enumerate(st.session_state.image_history[:5]):
                st.write(f"**Style:** {hist['style']} | **Prompt:** {hist['prompt']}")
                st.image(hist['url'], width=250)
                st.write("---")
        else:
            st.info("इतिहास (History) खाली है。")

if __name__ == "__main__":
    render_image_page()
