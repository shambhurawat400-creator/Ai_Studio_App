import streamlit as st
import urllib.parse
from datetime import datetime
import time

def render_image_page():
    st.subheader("🎨 Pro Text-to-Image Studio (Patreon Quality)")
    st.write("बेहतरीन टेक्सचर, शार्प डिटेल्स और शानदार क्वालिटी के साथ इमेज बनाएं (Free API Boosted):")

    if "image_history" not in st.session_state:
        st.session_state.image_history = []
    if "saved_projects" not in st.session_state:
        st.session_state.saved_projects = []

    img_prompt = st.text_area("✨ Prompt Box (मुख्य विवरण):", placeholder="A cinematic portrait of an old village woman stopping Rahul, dramatic lighting, masterpiece...")
    neg_prompt = st.text_area("🚫 Negative Prompt (जो चीज़ें इमेज में नहीं चाहिए):", placeholder="blurry, ugly, deformed hands, low quality, text")

    st.markdown("### 🎭 Style Selection (शैलियों का चयन)")
    style_option = st.selectbox("चुनें अपना पसंदीदा आर्ट स्टाइल:", [
        "Cinematic Masterpiece", "Midjourney Style", "Ultra Realistic", 
        "Anime (Studio Ghibli)", "Pixar Style 3D", 
        "2D Illustration", "Fantasy Art", "Sci-Fi Concept", 
        "Watercolor Painting", "Oil Painting"
    ])

    col1, col2, col3 = st.columns(3)
    
    with col1:
        ratio_option = st.selectbox("📐 Aspect Ratio", ["Portrait (9:16) - Mobile", "Landscape (16:9) - Desktop", "Square (1:1)"])
        if "16:9" in ratio_option:
            width, height = 1280, 720
        elif "9:16" in ratio_option:
            width, height = 720, 1280
        else:
            width, height = 1024, 1024

    with col2:
        quality_mode = st.selectbox("⚡ Quality Mode", ["Ultra HD (Best Texture)", "High Quality", "Standard"])
        if "Ultra HD" in quality_mode:
            width, height = int(width * 1.4), int(height * 1.4)

    with col3:
        num_images = st.slider("🔢 Number of Images", 1, 4, 1)

    if st.button("🚀 Generate Premium Quality Images", type="primary", use_container_width=True):
        if img_prompt.strip():
            with st.spinner(f"✨ {style_option} और एडवांस बूस्टर के साथ इमेज रेंडर हो रही है... कृपया प्रतीक्षा करें..."):
                
                # --- Progress Bar (0.7 seconds) ---
                progress_bar = st.progress(0)
                for percent_complete in range(100):
                    time.sleep(0.007)
                    progress_bar.progress(percent_complete + 1)
                progress_bar.empty()
                # --- End of Progress Bar ---

                # --- Master Enhancement Engine ---
                # These tags are combined to force the free FLUX model to produce higher quality output.
                mj_v6_tags = "--ar 9:16 --v 6.0 --style raw --niji 6" # Just a hint, not actual Midjourney code
                master_tags = f"extremely detailed, 8k resolution, cinematic lighting, intricate textures, masterpiece, photorealistic, {mj_v6_tags}"
                
                style_tags_map = {
                    "Cinematic Masterpiece": f"cinematic film still, {master_tags}, dramatic shadows, color graded",
                    "Midjourney Style": f"midjourney style, high contrast, richly detailed, {master_tags}, complex composition",
                    "Ultra Realistic": f"hyper-realistic photograph, raw photo, 8k uhd, dslr, {master_tags}, sharp focus",
                    "Anime (Studio Ghibli)": f"studio ghibli style, vibrant colors, detailed background, {master_tags}, anime art",
                    "Pixar Style 3D": f"3d disney pixar style animation, cute, volumetric lighting, {master_tags}, expressive character",
                    "2D Illustration": f"classic 2d vector illustration, clean lines, professional art, {master_tags}",
                    "Fantasy Art": f"magical fantasy art, ethereal glow, intricate details, {master_tags}, epic atmosphere",
                    "Sci-Fi Concept": f"futuristic sci-fi concept art, high-tech details, neon lights, {master_tags}",
                    "Watercolor Painting": f"soft watercolor painting, artistic brushwork, textured paper, {master_tags}",
                    "Oil Painting": f"classic oil painting, impasto texture, rich colors, {master_tags}, masterpiece on canvas"
                }

                current_style_tag = style_tags_map.get(style_option, f"{master_tags}")
                clean_input = img_prompt.strip()
                final_prompt = f"{clean_input}, {current_style_tag}"
                
                # Aggressive negative tags to prevent blur and distortion
                default_neg = "blurry, ugly, deformed hands, distorted face, low quality, bad anatomy, text, watermark, signature, out of focus"
                if neg_prompt.strip():
                    final_neg = f"{neg_prompt.strip()}, {default_neg}"
                else:
                    final_neg = default_neg

                encoded_prompt = urllib.parse.quote(final_prompt)
                encoded_neg = urllib.parse.quote(final_neg)
                
                generated_urls = []
                for i in range(num_images):
                    seed_val = datetime.now().microsecond + i
                    # Using 'flux' model with explicit quality parameters for better texture
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={seed_val}&model=flux&nologo=true&negative={encoded_neg}&quality=95&upscale=true"
                    generated_urls.append(image_url)

                st.success(f"🎉 सफलतापूर्वक {num_images} प्रीमियम इमेज तैयार हो गई हैं!")

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
            st.info("कोई प्रोजेक्ट सेव नहीं है。")

    with tab2:
        st.subheader("पिछली जनरेट की गई इमेजेस (History)")
        if st.session_state.image_history:
            for h_idx, hist in enumerate(st.session_state.image_history[:5]):
                st.write(f"**Style:** {hist['style']} | **Prompt:** {hist['prompt']}")
                st.image(hist['url'], width=250)
                st.write("---")
        else:
            st.info("इतिहास (History) खाली है。")
