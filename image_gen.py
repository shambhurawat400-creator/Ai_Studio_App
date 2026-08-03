import streamlit as st
import urllib.parse
from datetime import datetime

def render_image_page():
    st.subheader("🎨 Pro Text-to-Image Studio")
    st.write("शार्प चेहरे, स्पष्ट आँखें और परफेक्ट बैकग्राउंड के साथ हाई-क्वालिटी इमेज बनाएं:")

    if "image_history" not in st.session_state:
        st.session_state.image_history = []
    if "saved_projects" not in st.session_state:
        st.session_state.saved_projects = []

    img_prompt = st.text_area("✨ Prompt Box (मुख्य विवरण):", placeholder="An Indian grandmother crying, a sad man reading a letter, and a young girl, highly detailed room, clear eyes, sharp focus...")
    neg_prompt = st.text_area("🚫 Negative Prompt (जो चीज़ें इमेज में नहीं चाहिए):", placeholder="blurry eyes, distorted face, out of focus background, dark shadows, low quality")

    st.markdown("### 🎭 Style Selection (शैलियों का चयन)")
    style_option = st.selectbox("चुनें अपना पसंदीदा आर्ट स्टाइल:", [
        "Indian Storybook Illustration (बेस्ट क्वालिटी)",
        "2D Cartoon / Animation",
        "Cinematic", 
        "Realistic", 
        "Anime", 
        "Pixar", 
        "3D", 
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
        quality_mode = st.selectbox("⚡ Quality Mode", ["Ultra HD (High Detail)", "HD Quality (1080p)", "Standard"])
        if "Ultra HD" in quality_mode:
            width, height = int(width * 1.25), int(height * 1.25)

    with col3:
        num_images = st.slider("🔢 Number of Images", 1, 4, 1)

    if st.button("🚀 Generate High Quality Images", type="primary", use_container_width=True):
        if img_prompt.strip():
            with st.spinner(f"🎨 {style_option} स्टाइल में क्रिस्टल-क्लियर इमेज तैयार हो रही है..."):
                
                # Bulletproof tags for absolute clarity, sharp eyes and crystal clear background
                ultimate_clarity = "extremely detailed sharp eyes, crystal clear facial features, fully focused sharp background, perfectly lit room, vibrant rich colors, masterwork illustration, 8k resolution"
                face_enhancers = "codeformer, gfpgan, realistic_vision_inpainting_v4" # Adding face fixing techniques
                
                style_tags_map = {
                    "Indian Storybook Illustration (बेस्ट क्वालिटी)": f"classic Indian storybook vector illustration, clean sharp outlines, warm soft lighting, beautifully drawn characters and clear indoor room background, {ultimate_clarity}",
                    "2D Cartoon / Animation": f"professional 2d animation cell, clean outlines, vibrant clear lighting, {ultimate_clarity}",
                    "Cinematic": f"cinematic story frame, balanced warm lighting, highly detailed background, {ultimate_clarity}",
                    "Realistic": f"hyper-realistic painting, detailed textures, sharp lighting, {ultimate_clarity}",
                    "Anime": f"high quality anime art, expressive clear eyes, beautiful sharp background, {ultimate_clarity}",
                    "Pixar": f"3d disney pixar style animation, cute, vibrant lighting, sharp focus, {ultimate_clarity}",
                    "3D": f"octane render, 3d art, sharp volumetric lighting, {ultimate_clarity}",
                    "2D": f"classic 2d vector art, clean lines, professional illustration, {ultimate_clarity}",
                    "Cartoon": f"fun cartoon style, bold outlines, bright expressive colors, sharp details",
                    "Fantasy": f"magical fantasy art, ethereal glow, detailed sharp environment, {ultimate_clarity}",
                    "Sci-Fi": f"futuristic sci-fi art, high-tech sharp details, {ultimate_clarity}",
                    "Watercolor": f"soft watercolor painting style, artistic brush strokes, clear background, {ultimate_clarity}",
                    "Oil Painting": f"classic oil painting on canvas, rich textured brushwork, masterpiece, {ultimate_clarity}"
                }

                current_style_tag = style_tags_map.get(style_option, ultimate_clarity)
                clean_input = img_prompt.strip()
                final_prompt = f"{clean_input}, {current_style_tag}"
                
                # Explicit negative prompt for face clarity
                default_neg = "blurry eyes, closed eyes, out of focus background, dark shadows on face, low quality, bad anatomy, distorted features"
                if neg_prompt.strip():
                    final_neg = f"{neg_prompt.strip()}, {default_neg}"
                else:
                    final_neg = default_neg

                encoded_prompt = urllib.parse.quote(final_prompt)
                encoded_neg = urllib.parse.quote(final_neg)
                
                generated_urls = []
                for i in range(num_images):
                    seed_val = datetime.now().microsecond + i
                    # Switched to 'turbo' model for crisp, sharp rendering and added negative prompt parameter in URL
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={seed_val}&model=turbo&nologo=true&negative={encoded_neg}&face_enhancers={face_enhancers}"
                    generated_urls.append(image_url)

                st.success(f"✨ शार्प क्वालिटी की {num_images} इमेज तैयार हैं!")

                # Fix: Removed the `st.write(idx)` or any index printing that caused the '0' error
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
