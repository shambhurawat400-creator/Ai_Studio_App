import streamlit as st
import urllib.parse
from datetime import datetime

def render_image_page():
    st.subheader("🎨 Pro Smart Text-to-Image Studio")
    st.write("प्रॉम्प्ट के हिसाब से ऑटोमैटिक शानदार VFX, शार्प आँखें और हाई-क्वालिटी इमेज बनाएं:")

    if "image_history" not in st.session_state:
        st.session_state.image_history = []
    if "saved_projects" not in st.session_state:
        st.session_state.saved_projects = []

    img_prompt = st.text_area("✨ Prompt Box (मुख्य विवरण):", placeholder="Family sitting in a bright colorful room, sharp details, vibrant lighting...")
    neg_prompt = st.text_area("🚫 Negative Prompt (जो चीज़ें इमेज में नहीं चाहिए):", placeholder="blurry eyes, dark shadows, dull colors, low quality, black and white")

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
        quality_mode = st.selectbox("⚡ Quality Mode", ["Ultra HD (Full Sharpness)", "HD Quality (1080p)", "Standard"])
        if "Ultra HD" in quality_mode:
            width, height = int(width * 1.25), int(height * 1.25)

    with col3:
        num_images = st.slider("🔢 Number of Images", 1, 4, 1)

    if st.button("🚀 Generate Images Now", type="primary", use_container_width=True):
        if img_prompt.strip():
            with st.spinner(f"🎨 {style_option} और ऑटोमैटिक स्मार्ट VFX के साथ इमेज रेंडर हो रही है..."):
                
                # Auto-Smart VFX and Color Enhancement Engine based on prompt context
                auto_smart_vfx = "stunning visual effects, vibrant rich color grading, glowing ambient rim lighting, highly detailed colorful environment, 8k resolution"
                ultra_clarity_tags = "extremely detailed sharp eyes, crystal clear pupils, perfectly focused background, rich colorful room interior, flawless clarity"
                
                style_tags_map = {
                    "Cinematic": f"cinematic wide shot, {auto_smart_vfx}, sharp background details, {ultra_clarity_tags}",
                    "Realistic": f"hyper-realistic photography, {auto_smart_vfx}, sharp focus on subject and background, {ultra_clarity_tags}",
                    "Anime": f"high quality anime art, {auto_smart_vfx}, sharp detailed eyes, clear background scenery, {ultra_clarity_tags}",
                    "Pixar": f"3d disney pixar style animation, {auto_smart_vfx}, sharp detailed environment, expressive eyes, {ultra_clarity_tags}",
                    "3D": f"octane render, {auto_smart_vfx}, 3d environment design, sharp textures, {ultra_clarity_tags}",
                    "2D": f"classic 2d vector art, clean sharp lines, {auto_smart_vfx}, fully visible background details",
                    "Cartoon": f"fun cartoon style, bright clean background, {auto_smart_vfx}, expressive clear eyes",
                    "Fantasy": f"magical fantasy art, {auto_smart_vfx}, crystal clear background environment, detailed eyes, {ultra_clarity_tags}",
                    "Sci-Fi": f"futuristic sci-fi art, {auto_smart_vfx}, high-tech sharp background details, clear eyes, {ultra_clarity_tags}",
                    "Watercolor": f"soft watercolor painting style, {auto_smart_vfx}, clear background architecture, detailed face",
                    "Oil Painting": f"classic oil painting on canvas, {auto_smart_vfx}, rich background textures, clear facial expressions"
                }

                current_style_tag = style_tags_map.get(style_option, f"masterpiece, 8k, {auto_smart_vfx}")
                clean_input = img_prompt.strip()
                final_prompt = f"{clean_input}, {current_style_tag}"
                
                default_neg = "blurry eyes, closed eyes, dull colors, black and white, monochrome, out of focus background, low quality"
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

                st.success(f"✨ ऑटोमैटिक शानदार कलर्स और VFX के साथ {num_images} इमेज तैयार हैं!")

                cols = st.columns(min(num_images, 2))
                for idx, url in enumerate(generated_urls):
                    with cols[idx % len(cols)]:
                        st.image(url, caption=f"Style: {style_option} | Auto-VFX Active | #{idx+1}", use_column_width=True)
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
