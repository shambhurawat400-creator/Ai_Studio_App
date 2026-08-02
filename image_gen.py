import streamlit as st
import urllib.parse
from datetime import datetime

def render_image_page():
    st.subheader("🎨 Ultra HD 3D Pixar Studio")
    st.write("डिस्टिंस और पिक्सर जैसी हाई-क्वालिटी 3D कार्टून इमेज बनाएं:")

    if "image_history" not in st.session_state:
        st.session_state.image_history = []
    if "saved_projects" not in st.session_state:
        st.session_state.saved_projects = []

    img_prompt = st.text_area("✨ Prompt Box (मुख्य विवरण):", placeholder="Cute animals looking at a glowing magical star trapped in wooden sticks, forest background...")
    neg_prompt = st.text_area("🚫 Negative Prompt (जो चीज़ें इमेज में नहीं चाहिए):", placeholder="blurry, low quality, deformed, ugly, bad anatomy")

    st.markdown("### 🎭 Style Selection (शैलियों का चयन)")
    style_option = st.selectbox("चुनें अपना पसंदीदा आर्ट स्टाइल:", [
        "3D Pixar / Disney Animation", 
        "Cinematic 3D Render", 
        "Hyper-Realistic", 
        "Anime Style", 
        "Fantasy Magic"
    ])

    col1, col2, col3 = st.columns(3)
    
    with col1:
        ratio_option = st.selectbox("📐 Aspect Ratio", ["Portrait (9:16) - Best for Mobile", "Square (1:1)", "Landscape (16:9)"])
        if "9:16" in ratio_option:
            width, height = 720, 1280
        elif "1:1" in ratio_option:
            width, height = 1024, 1024
        else:
            width, height = 1280, 720

    with col2:
        quality_mode = st.selectbox("⚡ Quality Mode", ["Ultra HD (4K Masterpiece)", "HD Quality (1080p)"])
        if "Ultra HD" in quality_mode:
            width, height = int(width * 1.3), int(height * 1.3)

    with col3:
        num_images = st.slider("🔢 Number of Images", 1, 4, 1)

    if st.button("🚀 Generate Pixar Quality Image", type="primary", use_container_width=True):
        if img_prompt.strip():
            with st.spinner(f"✨ पिक्सर स्टूडियो क्वालिटी में इमेज रेंडर हो रही है... कृपया प्रतीक्षा करें..."):
                
                # DALL-E 3 & Pixar style high-end rendering tags for texture, lighting and fur details
                pixar_master_tags = "3d disney pixar style animation, unreal engine 5 render, cinematic volumetric sunlight, glowing magic particles, highly detailed fur and textures, crystal clear sharp expressive eyes, masterpiece, 8k resolution, photorealistic lighting"
                
                style_tags_map = {
                    "3D Pixar / Disney Animation": f"3d disney pixar style animation, cute expressive characters, {pixar_master_tags}",
                    "Cinematic 3D Render": f"cinematic 3d render, dramatic golden hour lighting, octane render, {pixar_master_tags}",
                    "Hyper-Realistic": f"hyper-realistic photography, sharp focus, incredibly detailed textures, {pixar_master_tags}",
                    "Anime": f"high quality studio ghibli anime art, vibrant colors, detailed line art, {pixar_master_tags}",
                    "Fantasy": f"magical fantasy art, ethereal glowing atmosphere, epic lighting, {pixar_master_tags}"
                }

                current_style_tag = style_tags_map.get(style_option, pixar_master_tags)
                clean_input = img_prompt.strip()
                final_prompt = f"{clean_input}, {current_style_tag}"
                
                default_neg = "blurry, deformed eyes, low quality, bad anatomy, ugly, flat colors, bad lighting"
                if neg_prompt.strip():
                    final_neg = f"{neg_prompt.strip()}, {default_neg}"
                else:
                    final_neg = default_neg

                encoded_prompt = urllib.parse.quote(final_prompt)
                encoded_neg = urllib.parse.quote(default_neg)
                
                generated_urls = []
                for i in range(num_images):
                    seed_val = datetime.now().microsecond + i
                    # Using advanced flux/prodia parameters via pollinations for better texture
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={seed_val}&model=flux-realism&nologo=true&negative={encoded_neg}"
                    generated_urls.append(image_url)

                st.success(f"🎉 शानदार पिक्सर क्वालिटी की {num_images} इमेज तैयार हैं!")

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
