import streamlit as st
import urllib.parse
from datetime import datetime
import time

def render_image_page():
    st.subheader("🎨 Pro Text-to-Image Studio with Smart VFX")
    st.write("सुपर-फास्ट लोडिंग, ऑटोमैटिक VFX और शार्प क्वालिटी के साथ इमेज बनाएं:")

    if "image_history" not in st.session_state:
        st.session_state.image_history = []
    if "saved_projects" not in st.session_state:
        st.session_state.saved_projects = []

    img_prompt = st.text_area("✨ Prompt Box (मुख्य विवरण):", placeholder="A magical forest with glowing lights, vibrant colors, cinematic VFX...")
    neg_prompt = st.text_area("🚫 Negative Prompt (जो चीज़ें इमेज में नहीं चाहिए):", placeholder="blurry, dark, dull colors, deformed")

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
            with st.spinner(f"🎨 {style_option} स्टाइल और स्मार्ट VFX के साथ इमेज रेंडर हो रही है..."):
                
                # --- Hyper-Fast Progress Bar Simulation (0.5 seconds) ---
                progress_bar = st.progress(0)
                for percent_complete in range(100):
                    time.sleep(0.005) # Fast speed: 100 steps * 0.005s = 0.5 seconds
                    progress_bar.progress(percent_complete + 1)
                
                progress_bar.empty() # Remove progress bar after completion
                # --- End of Progress Bar ---

                # --- Smart VFX & Clarity Enhancement ---
                smart_vfx = "stunning visual effects, vibrant rich color grading, dramatic lighting, professional VFX, masterpiece"
                clarity_boost = "extremely detailed, sharp focus, high definition, 8k resolution"
                
                style_tags_map = {
                    "Cinematic": f"cinematic film still, {smart_vfx}, {clarity_boost}, depth of field",
                    "Realistic": f"hyper-realistic, {smart_vfx}, {clarity_boost}, photorealistic, sharp focus",
                    "Anime": f"high quality anime art, studio ghibli style, vibrant colors, {smart_vfx}",
                    "Pixar": f"3d disney pixar style animation, cute, {smart_vfx}, vibrant lighting",
                    "3D": f"octane render, 3d blender art, volumetric lighting, {smart_vfx}",
                    "2D": f"classic 2d vector art, clean lines, professional illustration, {smart_vfx}",
                    "Cartoon": f"fun cartoon style, bold outlines, bright expressive colors, {smart_vfx}",
                    "Fantasy": f"magical fantasy art, ethereal glow, {smart_vfx}, mythical environment",
                    "Sci-Fi": f"futuristic sci-fi concept art, cyberpunk neon lights, {smart_vfx}",
                    "Watercolor": f"soft watercolor painting style, artistic brush strokes, {smart_vfx}",
                    "Oil Painting": f"classic oil painting on canvas, rich textured brushwork, {smart_vfx}"
                }

                current_style_tag = style_tags_map.get(style_option, f"masterpiece, {smart_vfx}, {clarity_boost}")
                clean_input = img_prompt.strip()
                final_prompt = f"{clean_input}, {current_style_tag}"
                
                default_neg = "blurry, dark, dull colors, deformed, bad anatomy, ugly"
                if neg_prompt.strip():
                    final_neg = f"{neg_prompt.strip()}, {default_neg}"
                else:
                    final_neg = default_neg

                encoded_prompt = urllib.parse.quote(final_prompt)
                encoded_neg = urllib.parse.quote(final_neg)
                
                generated_urls = []
                for i in range(num_images):
                    seed_val = datetime.now().microsecond + i
                    # Using 'flux' model for best quality and ensuring VFX is applied
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={seed_val}&model=flux&nologo=true&negative={encoded_neg}"
                    generated_urls.append(image_url)

                st.success(f"✨ शानदार VFX और {num_images} इमेज तैयार हैं!")

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
