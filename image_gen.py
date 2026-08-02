import streamlit as st
import urllib.parse
from datetime import datetime

def render_image_page():
    st.subheader("🎨 Ultra HD AI Image Generator with Advanced VFX")
    st.write("खास माहौल और सिनेमैटिक VFX के साथ हाई-क्वालिटी फोटो बनाएं:")

    img_prompt = st.text_area("फोटो का विवरण (Prompt):", placeholder="An Indian old village woman near a haunted well, dark moody atmospheric lighting, volumetric smoke")
    
    col1, col2 = st.columns(2)
    with col1:
        ratio_option = st.selectbox("📐 Aspect Ratio (साइज)", ["Landscape (16:9)", "Portrait (9:16)", "Square (1:1)"])
        if "16:9" in ratio_option:
            width, height = 1024, 576
        elif "9:16" in ratio_option:
            width, height = 576, 1024
        else:
            width, height = 768, 768

    with col2:
        vfx_style = st.selectbox("✨ माहौल और VFX", ["Horror / Eerie", "Cinematic Movie", "Photorealistic", "3D Animation / Pixar", "Cyberpunk / Neon Glow"])

    if st.button("Generate Ultra HD Image 🚀", type="primary", use_container_width=True):
        if img_prompt.strip():
            with st.spinner("⚡ VFX और लाइटिंग के साथ इमेज रेंडर हो रही है..."):
                clean_input = img_prompt.strip()
                if "Horror" in vfx_style:
                    vfx_tags = "dark moody atmosphere, volumetric fog, eerie shadows, cinematic horror lighting, masterpiece, 8k"
                elif "Cinematic" in vfx_style:
                    vfx_tags = "cinematic film still, dramatic lighting, depth of field, 8k, photorealistic"
                else:
                    vfx_tags = "ultra-detailed, sharp face focus, crystal clear, 8k resolution"

                final_prompt = f"{clean_input}, {vfx_tags}"
                encoded_prompt = urllib.parse.quote(final_prompt)
                seed_val = datetime.now().microsecond
                image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={seed_val}&model=flux&nologo=true"

                st.image(image_url, caption=f"Prompt: {img_prompt}", use_column_width=True)
                st.success("✨ 4K VFX इमेज तैयार है!")
        else:
            st.warning("कृपया पहले फोटो का विवरण दर्ज करें!")
