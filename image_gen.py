import streamlit as st
import urllib.parse
from datetime import datetime

def render_image_page():
    st.subheader("🎨 Pro Text-to-Image Studio")
    st.write("क्रिस्टल-क्लियर आँखों, शार्प बैकग्राउंड और एडवांस स्टाइल्स के साथ हाई-क्वालिटी इमेज बनाएं:")

    if "image_history" not in st.session_state:
        st.session_state.image_history = []
    if "saved_projects" not in st.session_state:
        st.session_state.saved_projects = []

    img_prompt = st.text_area("✨ Prompt Box (मुख्य विवरण):", placeholder="Family sitting in a room, clearly visible sharp eyes, highly detailed background house interior...")
    neg_prompt = st.text_area("🚫 Negative Prompt (जो चीज़ें इमेज में नहीं चाहिए):", placeholder="blurry eyes, closed eyes, out of focus background, blurry walls, low quality")

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
            with st.spinner(f"🎨 {style_option} स्टाइल और फुल शार्प बैकग्राउंड के साथ इमेज रेंडर हो रही है..."):
                
                ultra_clarity_tags = "extremely detailed sharp eyes, crystal clear pupils, perfectly focused background, sharp room interior, highly detailed house environment, 8k resolution, flawless clarity"
                
                style_tags_map = {
                    "Cinematic": f"cinematic wide shot, balanced lighting across entire room, sharp background details, {ultra_clarity_tags}",
                    "Realistic": f"hyper-realistic photography, sharp focus on both subject and background house, {ultra_clarity_tags}",
                    "Anime": f"high quality anime art, sharp detailed eyes, clear background scenery, {ultra_clarity_tags}",
                    "Pixar": f"3d disney pixar style animation, sharp detailed environment, expressive eyes, {ultra_clarity_tags}",
                    "3D": f"octane render, 3d environment design, sharp textures on walls and furniture, {ultra_clarity_tags}",
                    "2D": f"classic 2d vector art, clean sharp lines, fully visible background house details",
                    "Cartoon": f"fun cartoon style, bright clean background, expressive clear eyes",
                    "Fantasy": f"magical fantasy art, crystal clear background environment, detailed eyes, {ultra_clarity_tags}",
                    "Sci-Fi": f"futuristic sci-fi art, high-tech sharp background details, clear eyes, {ultra_clarity_tags}",
                    "Watercolor": f"soft watercolor painting style, clear background architecture, detailed face",
                    "Oil Painting": f"classic oil painting on canvas, rich background textures, clear facial expressions"
                }

                current_style_tag = style_tags_map.get(style_option, f"masterpiece, 8k, {ultra_clarity_tags}")
                clean_input = img_prompt.strip()
                final_prompt = f"{clean_input}, {current_style_tag}"
                
                default_neg = "blurry eyes, closed eyes, out of focus background, blurry house, foggy background, low quality, deformed anatomy"
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

                st.success(f"✨ क्रिस्टल-क्लियर आँखों और बैकग्राउंड के साथ {num_images} इमेज तैयार हैं!")

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
