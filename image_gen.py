import streamlit as st
import urllib.parse
from datetime import datetime
import time

def render_image_page():
    st.subheader("🎨 Pro Text-to-Image Studio with Face Booster")
    st.write("चेहरे के परफेक्ट डिटेल्स, शानदार लाइटिंग और सुपर-फास्ट क्वालिटी के साथ इमेज बनाएं:")

    if "image_history" not in st.session_state:
        st.session_state.image_history = []
    if "saved_projects" not in st.session_state:
        st.session_state.saved_projects = []

    img_prompt = st.text_area("✨ Prompt Box (मुख्य विवरण):", placeholder="Old village woman stopping Rahul, front face clearly visible, expressive eyes, detailed facial features...")
    neg_prompt = st.text_area("🚫 Negative Prompt (जो चीज़ें इमेज में नहीं चाहिए):", placeholder="silhouette, dark face, hidden face, blurry eyes, low quality")

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
        quality_mode = st.selectbox("⚡ Quality Mode", ["Ultra HD (4K Masterpiece)", "HD Quality (1080p)", "Standard"])
        if "Ultra HD" in quality_mode:
            width, height = int(width * 1.3), int(height * 1.3)

    with col3:
        num_images = st.slider("🔢 Number of Images", 1, 4, 1)

    if st.button("🚀 Generate Images Now", type="primary", use_container_width=True):
        if img_prompt.strip():
            with st.spinner(f"🎨 {style_option} स्टाइल और फेस बूस्टर के साथ इमेज रेंडर हो रही है..."):
                
                # Progress Bar (0.5 seconds)
                progress_bar = st.progress(0)
                for percent_complete in range(100):
                    time.sleep(0.005)
                    progress_bar.progress(percent_complete + 1)
                progress_bar.empty()
                
                # --- Ultimate Face Clarity & Front Lighting Engine ---
                face_and_vfx_boost = "face clearly visible from front, perfectly illuminated facial features, crystal clear sharp eyes, vibrant rich color grading, stunning visual effects, 8k resolution, masterpiece, highly detailed textures"
                
                style_tags_map = {
                    "Cinematic": f"cinematic film portrait, front key lighting, {face_and_vfx_boost}, depth of field",
                    "Realistic": f"hyper-realistic photography, sharp focus on face, {face_and_vfx_boost}, photorealistic",
                    "Anime": f"high quality anime art, studio ghibli style, clear expressive face, {face_and_vfx_boost}",
                    "Pixar": f"3d disney pixar style animation, bright facial lighting, expressive eyes, {face_and_vfx_boost}",
                    "3D": f"octane render, 3d character art, perfect face illumination, {face_and_vfx_boost}",
                    "2D": f"classic 2d vector art, clean sharp lines, clearly visible face and expression, {face_and_vfx_boost}",
                    "Cartoon": f"fun cartoon style, bold outlines, bright expressive face, {face_and_vfx_boost}",
                    "Fantasy": f"magical fantasy art, glowing facial highlights, clear detailed face, {face_and_vfx_boost}",
                    "Sci-Fi": f"futuristic sci-fi art, neon facial illumination, clear details, {face_and_vfx_boost}",
                    "Watercolor": f"soft watercolor painting style, clear facial features, {face_and_vfx_boost}",
                    "Oil Painting": f"classic oil painting on canvas, clear illuminated face, {face_and_vfx_boost}"
                }

                current_style_tag = style_tags_map.get(style_option, f"masterpiece, {face_and_vfx_boost}")
                clean_input = img_prompt.strip()
                final_prompt = f"{clean_input}, {current_style_tag}"
                
                # Strong negative prompt to completely ban dark silhouettes and hidden faces
                default_neg = "silhouette, backlighting, dark face, shadow on face, hidden face, blurry eyes, closed eyes, deformed, low quality"
                if neg_prompt.strip():
                    final_neg = f"{neg_prompt.strip()}, {default_neg}"
                else:
                    final_neg = default_neg

                encoded_prompt = urllib.parse.quote(final_prompt)
                encoded_neg = urllib.parse.quote(default_neg)
                
                generated_urls = []
                for i in range(num_images):
                    seed_val = datetime.now().microsecond + i
                    # Using flux model with enhanced parameters for maximum clarity
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={seed_val}&model=flux&nologo=true&negative={encoded_neg}"
                    generated_urls.append(image_url)

                st.success(f"✨ साफ़ चेहरे और शानदार क्वालिटी की {num_images} इमेज तैयार हैं!")

                cols = st.columns(min(num_images, 2))
                for idx, url in enumerate(generated_urls):
                    with cols[idx % len(cols)]:
                        st.image(url, caption=f"Style: {style_option} | Face Boosted | #{idx+1}", use_column_width=True)
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
