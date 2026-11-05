#!/usr/init/env python3
"""
Generates, extends, and edits videos using the Gemini Omni 1.2 Flash model via the google-genai Interactions API.
Includes self-contained Files API upload logic to prevent missing module errors.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import mimetypes
import re
import subprocess
import sys
import time
import urllib.parse
import uuid
from google import genai
from google.genai import types, errors

# Ensure stdout is unbuffered/line-buffered for real-time progress logs
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

DEFAULT_MODEL = "gemini-omni-1.2-flash"

def get_api_key():
    """Retrieves API key strictly from GEMINI_API_KEY environment variable."""
    return os.environ.get("GEMINI_API_KEY")

def strip_query_params(url):
    """Strips query parameters from URL for clean logging and security."""
    if not url:
        return ""
    parsed = urllib.parse.urlparse(url)
    return urllib.parse.urlunparse(parsed._replace(query=""))

def sanitize_error(err):
    """Sanitizes error messages by redacting API keys, tokens, query parameters, internal provider URLs, and raw response bodies."""
    if not err:
        return ""

    if isinstance(err, errors.APIError):
        parts = []
        if getattr(err, "code", None):
            parts.append(str(err.code))
        if getattr(err, "status", None):
            parts.append(f"({err.status})")
        if getattr(err, "message", None):
            parts.append(f": {err.message}")
        elif getattr(err, "details", None):
            parts.append(f": {err.details}")
        err_str = " ".join(parts) if parts else str(err)
    else:
        err_str = str(err)

    key = get_api_key()
    if key and len(key) >= 8:
        err_str = err_str.replace(key, "[REDACTED_KEY]")

    err_str = re.sub(r'AIza[0-9A-Za-z_\-]{30,}', '[REDACTED_KEY]', err_str)
    err_str = re.sub(r'AQ\.[0-9A-Za-z_\-]{20,}', '[REDACTED_KEY]', err_str)
    err_str = re.sub(r'ya29\.[0-9A-Za-z_\-]+', '[REDACTED_TOKEN]', err_str)
    err_str = re.sub(r'Bearer\s+[A-Za-z0-9_\-\.]+', 'Bearer [REDACTED_TOKEN]', err_str, flags=re.IGNORECASE)
    err_str = re.sub(r'([?&](?:key|api_key|apiKey|access_token|auth|signature)=)[^&\s"\'<>()]+', r'\1[REDACTED]', err_str)
    err_str = re.sub(r'https?://[a-zA-Z0-9.\-_]*\.corp\.goog[^\s"\'<>)]*', '[INTERNAL_HOST]', err_str)
    err_str = re.sub(r'https?://[a-zA-Z0-9.\-_]*\.sandbox\.googleapis\.com[^\s"\'<>)]*', '[SANDBOX_ENDPOINT]', err_str)
    err_str = re.sub(r'https?://(?:generativelanguage|aiplatform)\.googleapis\.com/v[0-9a-z_]+/', '[API_ENDPOINT]/', err_str)
    err_str = re.sub(r'\bbody\s*=.*\Z', 'body=[REDACTED_BODY]', err_str, flags=re.IGNORECASE | re.DOTALL)

    if "<html" in err_str.lower() or "<!doctype" in err_str.lower() or "<body" in err_str.lower():
        title_match = re.search(r'<title>(.*?)</title>', err_str, re.IGNORECASE)
        if title_match:
            err_str = f"HTTP Error Response: {title_match.group(1).strip()}"
        else:
            err_str = re.sub(r'<[^>]+>', ' ', err_str)

    err_str = re.sub(r'\s+', ' ', err_str).strip()
    if len(err_str) > 500:
        err_str = err_str[:497] + "..."

    return err_str

def is_file_uri(uri):
    """Returns True if the string is a standard Gemini File URI."""
    if not uri:
        return False
    return "files/" in uri and ("generativelanguage.googleapis.com" in uri or uri.startswith("files/"))

def normalize_file_uri(uri):
    """Normalizes any File API URI/reference to the standard format with query parameters stripped."""
    if not uri:
        return None
    match = re.search(r'files/([a-zA-Z0-9]+)', uri)
    if match:
        file_id = match.group(1)
        return f"https://generativelanguage.googleapis.com/files/{file_id}"
    return strip_query_params(uri)

def slugify(text):
    """Converts a text prompt into a safe, descriptive filename slug."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')[:50]

def detect_mime_type(file_path):
    """Determines MIME type based on file extension, falling back to standard mimetypes module."""
    ext = os.path.splitext(file_path)[1].lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".mp4": "video/mp4",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".pdf": "application/pdf",
        ".txt": "text/plain",
    }
    if ext in mime_map:
        return mime_map[ext]
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or "application/octet-stream"

def upload_file(file_path, display_name=None):
    """Performs an upload using google-genai SDK."""
    if not get_api_key():
        raise RuntimeError("Error: GEMINI_API_KEY environment variable is not set.")

    file_size = os.path.getsize(file_path)
    mime_type = detect_mime_type(file_path)

    if not display_name:
        display_name = os.path.basename(file_path)

    print(f"Preparing upload of '{file_path}' ({file_size} bytes, type: {mime_type})...")
    client = genai.Client(http_options=types.HttpOptions(timeout=300 * 1000))

    try:
        config = types.UploadFileConfig(
            display_name=display_name,
            mime_type=mime_type,
        )
        file_obj = client.files.upload(file=file_path, config=config)
        file_dict = json.loads(file_obj.model_dump_json())
        if "uri" in file_dict and file_dict["uri"]:
            file_dict["uri"] = strip_query_params(file_dict["uri"])
        if "mime_type" in file_dict:
            file_dict["mimeType"] = file_dict["mime_type"]
        return file_dict
    except errors.APIError as e:
        raise RuntimeError(f"API Error uploading file via SDK: {sanitize_error(e)}")
    except Exception as e:
        raise RuntimeError(f"Error uploading file via SDK: {sanitize_error(e)}")

def wait_for_active(file_name, poll_interval=3, max_attempts=60, backoff_factor=1.2, max_interval=15, max_timeout=600):
    """Polls the file status until state is ACTIVE or FAILED."""
    if not get_api_key():
        raise RuntimeError("Error: GEMINI_API_KEY environment variable is not set.")

    print(f"Waiting for file {file_name} to finish processing...")
    client = genai.Client(http_options=types.HttpOptions(timeout=30 * 1000))
    attempt = 0
    current_interval = poll_interval
    consecutive_errors = 0
    max_consecutive_errors = 5
    start_time = time.time()

    while attempt < max_attempts:
        if time.time() - start_time > max_timeout:
            raise TimeoutError(f"Error: Maximum timeout ({max_timeout}s) reached waiting for file {file_name} to become ACTIVE.")

        try:
            file_obj = client.files.get(name=file_name)
        except Exception as e:
            consecutive_errors += 1
            if consecutive_errors >= max_consecutive_errors:
                raise RuntimeError(f"Error checking status ({sanitize_error(e)}). Exiting.")
            time.sleep(current_interval)
            current_interval = min(current_interval * backoff_factor, max_interval)
            attempt += 1
            continue

        consecutive_errors = 0
        state = file_obj.state
        state_str = state.name if hasattr(state, "name") else str(state)

        if state == types.FileState.ACTIVE or state_str == "ACTIVE":
            print("File is ACTIVE and ready for generations!")
            file_dict = json.loads(file_obj.model_dump_json())
            if "uri" in file_dict and file_dict["uri"]:
                file_dict["uri"] = strip_query_params(file_dict["uri"])
            if "mime_type" in file_dict:
                file_dict["mimeType"] = file_dict["mime_type"]
            return file_dict
        elif state == types.FileState.FAILED or state_str == "FAILED":
            raise RuntimeError(f"Error: File processing failed on backend for '{file_name}' (State: FAILED)")

        print(f"Current state: {state_str}. Retrying in {current_interval:.1f}s...")
        time.sleep(current_interval)
        current_interval = min(current_interval * backoff_factor, max_interval)
        attempt += 1

    raise RuntimeError(f"Error: Maximum polling attempts ({max_attempts}) reached. File is still not ACTIVE.")

def parse_and_validate_duration(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        val = float(value)
    else:
        clean_value = str(value).strip().lower()
        if clean_value in ('none', ''):
            return None
        if clean_value.endswith('s'):
            clean_value = clean_value[:-1]
        try:
            val = float(clean_value)
        except ValueError:
            raise ValueError(f"Invalid duration value: '{value}'. Must be an integer.")
    val_int = int(val)
    if val_int < 3 or val_int > 15:
        raise ValueError(f"Duration must be between 3 and 15 seconds. Got {val_int}.")
    return f"{val_int}s"

def argparse_duration_type(value):
    if value is None or str(value).strip().lower() in ('none', ''):
        return None
    try:
        return parse_and_validate_duration(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e))

def parse_and_validate_resolution(value):
    if value is None:
        return None
    val = str(value).strip().lower()
    if val in ('none', ''):
        return None
    valid_resolutions = {"360p", "720p", "1080p", "4k"}
    if val in valid_resolutions:
        return val
    raise ValueError(f"Invalid resolution '{value}'. Supported: 360p, 720p, 1080p, 4k.")

def argparse_resolution_type(value):
    if value is None or str(value).strip().lower() in ('none', ''):
        return None
    try:
        return parse_and_validate_resolution(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e))

def resolve_or_upload_asset(asset_path, mime_type, strip_audio=False):
    if not asset_path:
        return None, None
    if not get_api_key():
        raise RuntimeError("Error: GEMINI_API_KEY environment variable is not set.")

    if is_file_uri(asset_path):
        normalized = normalize_file_uri(asset_path)
        return normalized, mime_type

    if os.path.exists(asset_path):
        upload_path = asset_path
        file_meta = upload_file(upload_path)
        file_name = file_meta.get("name")
        file_meta = wait_for_active(file_name)
        normalized = normalize_file_uri(file_meta.get("uri"))
        returned_mime = file_meta.get("mimeType") or file_meta.get("mime_type")
        return normalized, returned_mime
    else:
        raise FileNotFoundError(f"Asset path '{asset_path}' not found.")

def download_video_file(file_or_uri, output_path, client=None):
    if not file_or_uri:
        raise ValueError("Download error: file reference or URI is required.")
    if not get_api_key():
        raise RuntimeError("Error: GEMINI_API_KEY environment variable is not set.")
    if client is None:
        client = genai.Client()

    try:
        download_target = getattr(file_or_uri, "uri", file_or_uri)
        video_bytes = client.files.download(file=download_target)
        parent_dir = os.path.dirname(output_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(video_bytes)
        print(f"Video successfully saved to: {output_path}")
    except Exception as e:
        raise RuntimeError(f"Error downloading video file via SDK: {sanitize_error(e)}")

def generate_video(
    prompt,
    model=DEFAULT_MODEL,
    aspect_ratio="16:9",
    duration=None,
    resolution=None,
    first_frame=None,
    last_frame=None,
    image_path=None,
    image_reference=None,
    video_path=None,
    extend_video=None,
    video_reference=None,
    task=None,
    output_path="output.mp4",
    strip_audio=False,
    previous_interaction_id=None,
    timeout=600
):
    if not get_api_key():
        raise RuntimeError("Error: GEMINI_API_KEY environment variable is not set.")

    if last_frame and not first_frame:
        raise ValueError("--last-frame must be used with --first-frame.")

    duration = parse_and_validate_duration(duration)
    input_parts = []

    ref_images = []
    if image_path:
        ref_images.extend(image_path if isinstance(image_path, list) else [image_path])
    if image_reference:
        ref_images.extend(image_reference if isinstance(image_reference, list) else [image_reference])

    ref_videos = []
    if video_reference:
        ref_videos.extend(video_reference if isinstance(video_reference, list) else [video_reference])

    f1_uri, f1_mime = None, None
    if first_frame:
        f1_uri, f1_mime = resolve_or_upload_asset(first_frame, "image/png")
        input_parts.append({"type": "image", "uri": f1_uri, "mime_type": f1_mime})

    if last_frame:
        if last_frame == first_frame and f1_uri:
            input_parts.append({"type": "image", "uri": f1_uri, "mime_type": f1_mime})
        else:
            f2_uri, f2_mime = resolve_or_upload_asset(last_frame, "image/png")
            input_parts.append({"type": "image", "uri": f2_uri, "mime_type": f2_mime})

    for img in ref_images:
        img_uri, img_mime = resolve_or_upload_asset(img, "image/png")
        input_parts.append({"type": "image", "uri": img_uri, "mime_type": img_mime})

    if extend_video:
        ext_uri, ext_mime = resolve_or_upload_asset(extend_video, "video/mp4", strip_audio=strip_audio)
        input_parts.append({"type": "video", "uri": ext_uri, "mime_type": ext_mime})

    if video_path:
        paths = video_path if isinstance(video_path, list) else [video_path]
        for path in paths:
            vid_uri, vid_mime = resolve_or_upload_asset(path, "video/mp4", strip_audio=strip_audio)
            input_parts.append({"type": "video", "uri": vid_uri, "mime_type": vid_mime})

    for ref_vid in ref_videos:
        rv_uri, rv_mime = resolve_or_upload_asset(ref_vid, "video/mp4", strip_audio=strip_audio)
        input_parts.append({"type": "video", "uri": rv_uri, "mime_type": rv_mime})

    prompt_text = prompt
    if extend_video and not any(tok in prompt_text.lower() for tok in ("extend", "continue")):
        prompt_text = f"Extend this video. {prompt_text}"

    input_parts.append({"type": "text", "text": prompt_text})

    video_config = {"type": "video", "delivery": "uri"}
    if task != "extend":
        video_config["aspect_ratio"] = aspect_ratio
    if duration:
        video_config["duration"] = duration
    if resolution:
        video_config["resolution"] = parse_and_validate_resolution(resolution)

    generation_config = {"video_config": {"task": task}} if (task and not previous_interaction_id) else None

    client = genai.Client(http_options=types.HttpOptions(timeout=int(timeout) * 1000))
    create_kwargs = {"model": model, "input": input_parts, "response_format": video_config}
    if generation_config:
        create_kwargs["generation_config"] = generation_config
    if previous_interaction_id:
        create_kwargs["previous_interaction_id"] = previous_interaction_id

    try:
        interaction = client.interactions.create(**create_kwargs)
    except errors.APIError as e:
        raise RuntimeError(f"API Error generating video: {sanitize_error(e)}")
    except Exception as e:
        raise RuntimeError(f"Error generating video: {sanitize_error(e)}")

    output_video = interaction.output_video
    if not output_video or not output_video.uri:
        raise RuntimeError(f"No video content found in response for '{prompt}'.")

    download_video_file(output_video or output_video.uri, output_path, client=client)

def run_job(job):
    prompt = job.get("prompt")
    if not prompt:
        return {"job": job, "status": "SKIPPED", "error": "Empty prompt"}
    try:
        output_path = job.get("output") or f"media/output_{slugify(prompt)}.mp4"
        generate_video(prompt=prompt, output_path=output_path, **{k:v for k,v in job.items() if k not in ("prompt", "output")})
        return {"job": job, "status": "SUCCESS", "output_path": output_path}
    except Exception as e:
        return {"job": job, "status": "FAILED", "error": sanitize_error(e)}

class SanitizedArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, f"{self.prog}: error: {sanitize_error(message)}\n")

def main():
    parser = SanitizedArgumentParser(description="Generate, extend, and edit videos using Gemini Omni Flash via google-genai SDK.")
    parser.add_argument("prompt", nargs="?", help="Text prompt for video generation")
    parser.add_argument("--first-frame", "-f", help="Starting frame image")
    parser.add_argument("--last-frame", "-l", help="Final transition frame image")
    parser.add_argument("--image", "-i", action="append", dest="image", help="Reference image")
    parser.add_argument("--video", "-v", action="append", help="Source video")
    parser.add_argument("--extend", "-e", help="Video to extend")
    parser.add_argument("--video-reference", "-vr", action="append", dest="video_reference", help="Reference video")
    parser.add_argument("--task", choices=["text_to_video", "image_to_video", "reference_to_video", "edit", "extend"], default=None)
    parser.add_argument("--aspect-ratio", default="16:9", choices=["16:9", "9:16"])
    parser.add_argument("--duration", type=argparse_duration_type, default=None)
    parser.add_argument("--resolution", "-res", type=argparse_resolution_type, default=None)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--strip-audio", "-a", action="store_true")
    parser.add_argument("--previous-interaction-id")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--batch", help="Batch JSON file")
    parser.add_argument("--prompts-file", help="Prompts text file")
    parser.add_argument("--concurrency", type=int, default=3)

    args = parser.parse_args()

    if not get_api_key():
        print("Error: GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    if args.batch:
        with open(args.batch, "r", encoding="utf-8") as f:
            jobs = json.load(f)
    elif args.prompts_file:
        jobs = []
        with open(args.prompts_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    jobs.append({"prompt": line, "aspect_ratio": args.aspect_ratio, "duration": args.duration, "resolution": args.resolution, "model": args.model})
    else:
        if not args.prompt:
            parser.print_help()
            sys.exit(1)
        output_path = args.output if args.output else "media/output.mp4"
        try:
            generate_video(
                prompt=args.prompt, model=args.model, aspect_ratio=args.aspect_ratio,
                duration=args.duration, resolution=args.resolution, first_frame=args.first_frame,
                last_frame=args.last_frame, image_path=args.image, video_path=args.video,
                extend_video=args.extend, video_reference=args.video_reference, task=args.task,
                output_path=output_path, strip_audio=args.strip_audio,
                previous_interaction_id=args.previous_interaction_id, timeout=args.timeout
            )
            sys.exit(0)
        except Exception as e:
            print(f"Error: Generation failed: {sanitize_error(e)}", file=sys.stderr)
            sys.exit(1)

    results = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = {executor.submit(run_job, job): job for job in jobs}
        for future in as_completed(futures):
            results.append(future.result())

    print("\n" + "="*50)
    print("BATCH PARALLEL EXECUTION SUMMARY")
    print("="*50)
    for r in results:
        print(f"  [{r['status']}] '{r['job'].get('prompt')}' -> {r.get('output_path', r.get('error'))}")
    print("="*50)

if __name__ == "__main__":
    main()
