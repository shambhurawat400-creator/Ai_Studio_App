import streamlit as st
import urllib.parse
from datetime import datetime

def render_image_page():
    st.subheader("🎨 Pro Text-to-Image Studio")
    st.write("आपके लिखे गए प्रॉम्प्ट के अनुसार सटीक और बेहतरीन क्वालिटी की इमेज बनाएं:")

    if "image_history" not in st.session_state:
        st.session_state.image_history = []
    if "saved_projects" not in st.session_state:
        st.session_state.saved_projects = []

    img_prompt = st.text_area("✨ Prompt Box (मुख्य विवरण):", placeholder="Mohan shining a powerful flashlight deep inside the ancient dry well while others watch...")
    neg_prompt = st.text_area("🚫 Negative Prompt (जो चीज़ें इमेज में नहीं चाहिए):", placeholder="blurry, distorted, low quality, bad anatomy")

    st.markdown("### 🎭 Style Selection (शैलियों का चयन)")
    style_option = st.selectbox("चुनें अपना पसंदीदा आर्ट स्टाइल:", [
        "Cinematic Horror / Animation",
        "Indian Storybook Illustration",
        "Realistic", 
        "Anime", 
        "Pixar", 
        "3D", 
        "2D", 
        "Cartoon", 
        "Fantasy", 
        "Sci-Fi", 
        "Watercolor", 
        "Oil Painting"
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
        quality_mode = st.selectbox("⚡ Quality Mode", ["Ultra HD (4K)", "HD Quality (1080p)", "Standard"])
        if "Ultra HD" in quality_mode:
            width, height = int(width * 1.25), int(height * 1.25)

    with col3:
        num_images = st.slider("🔢 Number of Images", 1, 4, 1)

    if st.button("🚀 Generate Images Now", type="primary", use_container_width=True):
        if img_prompt.strip():
            with st.spinner(f"🎨 आपके प्रॉम्प्ट के अनुसार इमेज रेंडर हो रही है..."):
                
                # Minimal clean style suffix so AI focuses primarily on user prompt
                style_suffix_map = {
                    "Cinematic Horror / Animation": "cinematic horror animation style, highly detailed, 8k",
                    "Indian Storybook Illustration": "indian storybook illustration style, detailed, 8k",
                    "Realistic": "hyper-realistic, highly detailed, 8k resolution",
                    "Anime": "high quality anime style, detailed art",
                    "Pixar": "3d disney pixar animation style",
                    "3D": "octane render, 3d blender art, highly detailed",
                    "2D": "classic 2d vector art, clean lines",
                    "Cartoon": "fun cartoon style, bold outlines",
                    "Fantasy": "magical fantasy art style",
                    "Sci-Fi": "futuristic sci-fi concept art",
                    "Watercolor": "soft watercolor painting style",
                    "Oil Painting": "classic oil painting on canvas"
                }

                chosen_suffix = style_suffix_map.get(style_option, "masterpiece, 8k")
                
                # Directly using user prompt and adding chosen style smoothly
                clean_input = img_prompt.strip()
                final_prompt = f"{clean_input}, {chosen_suffix}"
                
                final_neg = neg_prompt.strip() if neg_prompt.strip() else "blurry, low quality, deformed, bad anatomy"

                encoded_prompt = urllib.parse.quote(final_prompt)
                encoded_neg = urllib.parse.quote(final_neg)
                
                generated_urls = []
                for i in range(num_images):
                    seed_val = datetime.now().microsecond + i
                    # Using flux model with exact user prompt mapping
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={seed_val}&model=flux&nologo=true&negative={encoded_neg}"
                    generated_urls.append(image_url)

                st.success(f"✨ सफलतापूर्वक {num_images} इमेज तैयार हो गई हैं!")

                cols = st.columns(min(num_images, 2))
                for idx, url in enumerate(generated_urls):
                    with cols[idx % len(cols)]:
                        st.image(url, caption=f"Style: {style_option} | #{idx+1}", use_column_width=True)
                        st.markdown(f"[📥 Download Image {idx+1}]({url})")
                        
                        if st.button(f"💾 Save Project #{idx+1}", key=f"save_{seed_val}_{idx}"):
                            project_data = {"prompt": img_prompt, "style": style_option, "url": url}
                            if project_data not in st.session_state.saved_projects:
                                st.session_state.saved_projects.append(project_data)
                                st.success("📁 प्रोजेक्ट सफलतापूर्वक सेव हो गया!")

                st.session_state.image_history.insert(0, {"prompt": img_prompt, "style": style_option, "url": generated_urls[0]})
        else:
            st.warning("⚠️ कृपया पहले प्रॉम्प्ट बॉक्स में इमेज का विवरण (Prompt) दर्ज करें!")

    st.markdown("---")
    tab1, tab2 = st.tabs(["📂 Saved Projects", "📜 Generation History"])

    with tab1:
        st.subheader("आपके सेव किए गए प्रोजेक्ट्स")
        if st.session_state.saved_projects:
            for p_idx, proj in enumerate(st.session_state.saved_projects):
                st.write(f"**{p_idx+1}. Style:** {proj['style']} | **Prompt:** {proj['prompt']}")
                st.image(proj['url'], width=300)
                st.markdown(f"[🔗 Direct Link]({proj['url']})")
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
            st.info("इतिहास (History) खाली है।")
