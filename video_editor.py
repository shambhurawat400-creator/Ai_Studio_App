try:
    from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips
except ImportError:
    from moviepy import AudioFileClip, ImageClip, concatenate_videoclips


def create_story_video(scenes: list, output_file: str = "final_story_video.mp4") -> str:
    video_clips = []
    audio_clips = []

    try:
        for scene in scenes:
            audio = AudioFileClip(scene["audio"])
            duration = max(audio.duration, 1.0)

            img = ImageClip(scene["image"]).with_duration(duration) if hasattr(ImageClip(scene["image"]), "with_duration") else ImageClip(scene["image"]).set_duration(duration)
            img = img.resized(height=720) if hasattr(img, "resized") else img.resize(height=720)
            img = img.with_audio(audio) if hasattr(img, "with_audio") else img.set_audio(audio)

            video_clips.append(img)
            audio_clips.append(audio)

        final_video = concatenate_videoclips(video_clips, method="compose")

        final_video.write_videofile(
            output_file,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=2,
            logger=None,
        )
        return output_file

    finally:
        for clip in video_clips:
            clip.close()
        for a_clip in audio_clips:
            a_clip.close()
