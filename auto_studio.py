import os
import json
import tempfile
import streamlit as st
from google import genai
from video_editor import create_story_video


def _get_gemini_client():
    api_key = None
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)


def generate_viral_story_package(niche_prompt: str, num_scenes: int = 4) -> dict:
    """
    Viral topic, Hindi story scenes, image prompts, aur YouTube metadata generate karta hai.
    """
    client = _get_gemini_client()
    if not client:
        raise RuntimeError("GEMINI_API_KEY set nahi hai.")

    prompt = f"""
You are a YouTube storytelling automation director for Indian audiences.
Topic / Niche idea: {niche_prompt}
Create a {num_scenes}-scene Hindi story (शुद्ध देसी हिंदी / emotional village & Ghibli style).

Return STRICT JSON ONLY with this exact structure:
{{
  "viral_title": "...",
  "description": "...",
  "tags": ["tag1", "tag2", "tag3"],
  "scenes": [
    {{
      "scene_no": 1,
      "narration": "Hindi voiceover line for this scene",
      "image_prompt": "Detailed visual prompt in English for image generation, no text in image"
    }}
  ]
}}
"""
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config={"temperature": 0.6},
    )
    raw = (response.text or "").strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Model ne valid JSON nahi diya.")
    return json.loads(raw[start : end + 1])


def render_auto_studio_page(supabase=None, user=None):
    st.subheader("🎬 Video Editing & YouTube Auto-Pilot Studio")
    st.write("Yahan se aap images + voice ko jodkar MP4 video edit kar sakte hain aur viral story workflow chala sakte hain:")

    tab_edit, tab_autopilot = st.tabs(["✂️ Video Editor (Images + Voice -> MP4)", "🚀 Viral Auto-Pilot & YouTube"])

    with tab_edit:
        st.markdown("### Scenes Ki Image Aur Voice Ko Jodkar MP4 Banayein")
        scene_count = st.number_input("Kitne scenes jodne hain?", min_value=1, max_value=10, value=2, step=1)
        scenes_input = []

        for idx in range(int(scene_count)):
            st.markdown(f"**Scene {idx + 1}**")
            c1, c2 = st.columns(2)
            with c1:
                img_file = st.file_uploader(f"Scene {idx + 1} Image (PNG/JPG)", type=["png", "jpg", "jpeg"], key=f"ve_img_{idx}")
            with c2:
                aud_file = st.file_uploader(f"Scene {idx + 1} Voiceover (MP3/WAV)", type=["mp3", "wav"], key=f"ve_aud_{idx}")

            if img_file and aud_file:
                scenes_input.append((img_file, aud_file))

        if st.button("🎞️ Render Final MP4 Video", type="primary", use_container_width=True):
            if len(scenes_input) != int(scene_count):
                st.warning("Har scene ke liye image aur audio dono upload karein.")
                return

            with st.spinner("Video render ho raha hai... Kripya pratiksha karein"):
                with tempfile.TemporaryDirectory() as tmpdir:
                    prepared_scenes = []
                    for i, (img_f, aud_f) in enumerate(scenes_input):
                        img_path = os.path.join(tmpdir, f"scene_{i}_{img_f.name}")
                        aud_path = os.path.join(tmpdir, f"scene_{i}_{aud_f.name}")
                        with open(img_path, "wb") as f:
                            f.write(img_f.getvalue())
                        with open(aud_path, "wb") as f:
                            f.write(aud_f.getvalue())
                        prepared_scenes.append({"image": img_path, "audio": aud_path})

                    out_mp4 = os.path.join(tmpdir, "final_story_video.mp4")
                    create_story_video(prepared_scenes, out_mp4)
                    with open(out_mp4, "rb") as f:
                        mp4_bytes = f.read()

                st.success("MP4 video taiyar ho gaya!")
                st.video(mp4_bytes)
                st.download_button(
                    label="📥 Download MP4 Video",
                    data=mp4_bytes,
                    file_name="final_story_video.mp4",
                    mime="video/mp4",
                )

    with tab_autopilot:
        st.markdown("### Viral Topic, Script & Scene Plan Generator")
        topic_idea = st.text_area(
            "Viral topic ya kahani ka idea likhein:",
            placeholder="Jaise: Gaav ke bachhon aur purane bargad ke ped ki bhavuk kahani...",
        )
        n_scenes = st.slider("Scenes ki sankhya", min_value=2, max_value=8, value=4)

        if st.button("✨ Generate Viral Story & Scene Prompts", type="primary"):
            if not topic_idea.strip():
                st.warning("Pehle topic ya idea likhein.")
                return
            with st.spinner("Viral title, script aur scene prompts ban rahe hain..."):
                try:
                    pkg = generate_viral_story_package(topic_idea.strip(), int(n_scenes))
                    st.session_state["last_viral_pkg"] = pkg
                except Exception as e:
                    st.error(f"Error: {e}")

        pkg = st.session_state.get("last_viral_pkg")
        if pkg:
            st.success(f"Title: {pkg.get('viral_title', '')}")
            st.write("**Description:**", pkg.get("description", ""))
            st.write("**Tags:**", ", ".join(pkg.get("tags", [])))
            for sc in pkg.get("scenes", []):
                st.markdown(f"**Scene {sc.get('scene_no')}**")
                st.write(f"- **Voiceover (Hindi):** {sc.get('narration')}")
                st.write(f"- **Image Prompt:** `{sc.get('image_prompt')}`")

        st.markdown("---")
        st.info("YouTube Channel Connect aur Auto-Upload ke liye agla step (`yt_auth.py` + `yt_uploader.py`) joda jayega.")
