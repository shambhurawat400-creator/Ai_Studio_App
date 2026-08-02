import streamlit as st
import urllib.parse
from datetime import datetime

def render_image_page():
    st.subheader("🎨 Pro Text-to-Image Studio")
    st.write("साफ़ चेहरों और शानदार लाइटिंग के साथ हाई-क्वालिटी इमेज बनाएं:")

    if "image_history" not in st.session_state:
        st.session_state.image_history = []
    if "saved_projects" not in st.session_state:
        st.session_state.saved_projects = []

    img_prompt = st.text_area("✨ Prompt Box (मुख्य विवरण):", placeholder="Family sitting sadly, clearly visible faces, expressive features...")
    neg_prompt = st.text_area("🚫 Negative Prompt (जो चीज़ें इमेज में नहीं चाहिए):", placeholder="dark shadows on face, hidden face, blurry, low quality, bad anatomy")

    st.markdown("### 🎭 Style Selection (शैलियों का चयन)")
    style_option = st.selectbox("चुनें अपना पसंदीदा आर्ट स्टाइल:", [
        "Cinematic", "Realistic", "Anime", "Pixar", "3D", 
        "2D", "Cartoon", "Fantasy", "Sci-Fi", 
        "Watercolor", "Oil Painting"
    ])

    col1, col2, col3 = st.columns(3)
    
    with col1:
        ratio_option = st.selectbox("📐 Aspect Ratio", ["Portrait (9:16) - Best for Faces", "Square (1:1)", "Landscape (16:9)"])
        if "9:16" in ratio_option:
            width, height = 720, 1280
        elif "1:1" in ratio_option:
            width, height = 1024, 1024
        else:
            width, height = 1280, 720

    with col2:
        quality_mode = st.selectbox("⚡ Quality Mode", ["Ultra HD (4K Sharp Face)", "HD Quality (1080p)", "Standard"])
        if "Ultra HD" in quality_mode:
            width, height = int(width * 1.25), int(height * 1.25)

    with col3:
        num_images = st.slider("🔢 Number of Images", 1, 4, 1)

    if st.button("🚀 Generate Images Now", type="primary", use_container_width=True):
        if img_prompt.strip():
            with st.spinner(f"🎨 {style_option} स्टाइल और साफ़ चेहरों के साथ इमेज रेंडर हो रही है..."):
                
                #强制 face illumination & visibility tags ताकि चेहरा अंधेरे में न छुपे
                face_visibility = "face clearly visible, bright studio portrait lighting on faces, sharp eyes, highly detailed facial features, no dark shadows on face"
                
                style_tags_map = {
                    "Cinematic": f"cinematic portrait, professional key lighting on face, depth of field, 8k, {face_visibility}",
                    "Realistic": f"hyper-realistic portrait, highly detailed facial features, perfectly illuminated face, sharp focus, 8k, {face_visibility}",
                    "Anime": f"high quality anime portrait, beautifully lit expressive face, detailed eyes, {face_visibility}",
                    "Pixar": f"3d disney pixar style character render, brightly lit expressive face, {face_visibility}",
                    "3D": f"octane render, 3d character close-up, perfect facial lighting, highly detailed face, {face_visibility}",
                    "2D": f"classic 2d vector character illustration, clean lines, clear bright facial expression",
                    "Cartoon": f"fun cartoon style, clear expressive face, bright well-lit colors",
                    "Fantasy": f"magical fantasy character portrait, glowing facial highlights, detailed face, {face_visibility}",
                    "Sci-Fi": f"futuristic sci-fi character portrait, neon facial illumination, detailed face, {face_visibility}",
                    "Watercolor": f"soft watercolor portrait painting, artistic brush strokes, clear bright face",
                    "Oil Painting": f"classic oil painting portrait on canvas, rich textured brushwork, clear illuminated face"
                }

                current_style_tag = style_tags_map.get(style_option, f"masterpiece, 8k, {face_visibility}")
                clean_input = img_prompt.strip()
                final_prompt = f"{clean_input}, {current_style_tag}"
                
                # Negative prompt to block dark or hidden faces completely
                default_neg = "dark shadows on face, hidden face, black face, blurry, deformed features, low quality, bad anatomy"
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

                st.success(f"✨ साफ़ चेहरों के साथ {num_images} इमेज तैयार हैं!")

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
