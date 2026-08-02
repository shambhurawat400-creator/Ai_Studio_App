import streamlit as st
import urllib.parse
from datetime import datetime

def render_image_page():
    st.subheader("🎨 Pro Text-to-Image Studio")
    st.write("एडवांस कंट्रोल्स, नेगेटिव प्रॉम्प्ट और स्टाइल्स के साथ हाई-क्वालिटी इमेज बनाएं:")

    if "image_history" not in st.session_state:
        st.session_state.image_history = []
    if "saved_projects" not in st.session_state:
        st.session_state.saved_projects = []

    img_prompt = st.text_area("✨ Prompt Box (मुख्य विवरण):", placeholder="An Indian old village woman near a haunted well...")
    neg_prompt = st.text_area("🚫 Negative Prompt (जो चीज़ें इमेज में नहीं चाहिए):", placeholder="blurry, low quality, deformed, bad anatomy")

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
        quality_mode = st.selectbox("⚡ Quality Mode", ["Ultra HD (4K)", "HD Quality (1080p)", "Standard"])
        if "Ultra HD" in quality_mode:
            width, height = int(width * 1.25), int(height * 1.25)

    with col3:
        num_images = st.slider("🔢 Number of Images", 1, 4, 1)

    if st.button("🚀 Generate Images Now", type="primary", use_container_width=True):
        if img_prompt.strip():
            with st.spinner(f"🎨 {style_option} स्टाइल और {quality_mode} क्वालिटी में इमेज रेंडर हो रही है..."):
                
                # Face sharpness enhancers added safely to maintain old structure
                face_enhancers = "extremely detailed face, sharp focus on facial features and eyes, clear expression, high resolution"
                
                style_tags_map = {
                    "Cinematic": f"cinematic film still, dramatic lighting, depth of field, 8k, photorealistic, {face_enhancers}",
                    "Realistic": f"hyper-realistic, highly detailed, photorealistic, sharp focus, 8k resolution, {face_enhancers}",
                    "Anime": f"high quality anime art, studio ghibli style, vibrant colors, detailed line art, {face_enhancers}",
                    "Pixar": f"3d disney pixar style animation, cute, vibrant lighting, unreal engine 5 render, {face_enhancers}",
                    "3D": f"octane render, 3d blender art, volumetric lighting, highly detailed, {face_enhancers}",
                    "2D": f"classic 2d vector art, clean lines, professional illustration, clear face",
                    "Cartoon": f"fun cartoon style, bold outlines, bright expressive colors, clear face",
                    "Fantasy": f"magical fantasy art, ethereal glow, mythical environment, epic composition, {face_enhancers}",
                    "Sci-Fi": f"futuristic sci-fi concept art, cyberpunk neon lights, high-tech details, {face_enhancers}",
                    "Watercolor": f"soft watercolor painting style, artistic brush strokes, pastel paper texture, clear face",
                    "Oil Painting": f"classic oil painting on canvas, rich textured brushwork, masterpiece, clear face"
                }

                current_style_tag = style_tags_map.get(style_option, f"masterpiece, 8k, {face_enhancers}")
                clean_input = img_prompt.strip()
                final_prompt = f"{clean_input}, {current_style_tag}"
                
                # Handling negative prompt correctly including face blur protection
                default_neg = "blurry face, deformed features, low quality, bad anatomy, ugly"
                if neg_prompt.strip():
                    final_neg = f"{neg_prompt.strip()}, {default_neg}"
                else:
                    final_neg = default_neg

                encoded_prompt = urllib.parse.quote(final_prompt)
                encoded_neg = urllib.parse.quote(final_neg)
                
                generated_urls = []
                for i in range(num_images):
                    seed_val = datetime.now().microsecond + i
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
