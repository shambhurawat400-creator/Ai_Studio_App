import streamlit as st
import urllib.parse
from datetime import datetime
import time

def render_image_page():
    st.subheader("🎨 Free Pro Storybook Studio")
    st.write("बिना किसी खर्च के शानदार क्वालिटी और साफ़ चेहरों वाली इमेज बनाएं:")

    if "image_history" not in st.session_state:
        st.session_state.image_history = []
    if "saved_projects" not in st.session_state:
        st.session_state.saved_projects = []

    # Prompt Box
    img_prompt = st.text_area("✨ Prompt Box (मुख्य विवरण):", placeholder="An old grandmother crying, a sad man reading a letter, village room, detailed faces...")
    
    # Negative Prompt Box (ताकि ब्लर या खराब इमेज न आए)
    neg_prompt = st.text_area("🚫 Negative Prompt (जो चीज़ें इमेज में नहीं चाहिए):", value="blurry, distorted face, low quality, bad anatomy, dark shadows, ugly")

    st.markdown("### 🎭 Style Selection (शैलियों का चयन)")
    style_option = st.selectbox("चुनें अपना पसंदीदा आर्ट स्टाइल:", [
        "Indian Storybook Illustration (बेस्ट)",
        "2D Animation / Cartoon",
        "Cinematic Story Frame",
        "Classic Oil Painting",
        "Watercolor Art"
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
        quality_mode = st.selectbox("⚡ Quality Mode", ["HD Quality", "Standard"])
        if "HD" in quality_mode:
            width, height = int(width * 1.2), int(height * 1.2)

    with col3:
        num_images = st.slider("🔢 Number of Images", 1, 4, 1)

    if st.button("🚀 Generate Free Images Now", type="primary", use_container_width=True):
        if img_prompt.strip():
            
            # Loading Progress Bar
            progress_text = "✨ AI फ्री मॉडल से बेहतरीन क्वालिटी तैयार कर रहा है..."
            my_bar = st.progress(0, text=progress_text)
            for percent_complete in range(100):
                time.sleep(0.008)
                my_bar.progress(percent_complete + 1, text=f"{progress_text} ({percent_complete + 1}%)")
            time.sleep(0.2)
            my_bar.empty()

            with st.spinner("🖼️ इमेज लोड हो रही है..."):
                
                # Quality boosters for free model
                free_boost = "extremely detailed faces, sharp focus, clean lines, vibrant colors, masterpiece, 8k resolution"
                
                style_tags_map = {
                    "Indian Storybook Illustration (बेस्ट)": f"classic Indian storybook vector illustration, beautifully drawn characters and room background, {free_boost}",
                    "2D Animation / Cartoon": f"professional 2d animation cell, clean outlines, vibrant clear lighting, {free_boost}",
                    "Cinematic Story Frame": f"cinematic story frame, warm ambient lighting, highly detailed background, {free_boost}",
                    "Classic Oil Painting": f"classic oil painting on canvas, rich textured brushwork, masterpiece, {free_boost}",
                    "Watercolor Art": f"soft watercolor painting style, artistic brush strokes, clear background, {free_boost}"
                }

                current_style_tag = style_tags_map.get(style_option, free_boost)
                clean_input = img_prompt.strip()
                final_prompt = f"{clean_input}, {current_style_tag}"
                
                final_neg = neg_prompt.strip() if neg_prompt.strip() else "blurry, low quality"

                encoded_prompt = urllib.parse.quote(final_prompt)
                encoded_neg = urllib.parse.quote(final_neg)
                
                generated_urls = []
                for i in range(num_images):
                    seed_val = datetime.now().microsecond + i
                    # Using free flux model URL
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={seed_val}&model=flux&nologo=true&negative={encoded_neg}"
                    generated_urls.append(image_url)

                st.success(f"✨ शानदार क्वालिटी की {num_images} इमेज तैयार हैं!")

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
