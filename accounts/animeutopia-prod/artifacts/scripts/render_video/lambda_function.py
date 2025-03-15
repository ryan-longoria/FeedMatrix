import datetime
import json
import os
import uuid
import numpy as np
import boto3
import requests

from moviepy import VideoFileClip
from moviepy.video.VideoClip import ColorClip, ImageClip, TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
import moviepy.video.fx as vfx
from PIL import ImageFont, ImageDraw, Image

s3 = boto3.client("s3")
font_path = "/usr/share/fonts/truetype/msttcorefonts/ariblk.ttf"


def dynamic_font_size(text, max_size, min_size, ideal_length):
    length = len(text)
    if length <= ideal_length:
        return max_size
    factor = (max_size - min_size) / ideal_length
    new_size = max_size - (length - ideal_length) * factor
    return int(new_size) if new_size > min_size else min_size


def measure_text_width(text, font_path, font_size):
    font = ImageFont.truetype(font_path, font_size)
    bbox = font.getbbox(text)
    width = bbox[2] - bbox[0]
    return width


def dynamic_split(text, font_path, font_size, max_width):
    if measure_text_width(text, font_path, font_size) <= max_width:
        return text, ""
    words = text.split()
    top_line = ""
    for i in range(1, len(words) + 1):
        candidate = " ".join(words[:i])
        if measure_text_width(candidate, font_path, font_size) <= max_width:
            top_line = candidate
        else:
            break
    bottom_line = " ".join(words[len(top_line.split()):])
    if len(words) - len(top_line.split()) > len(top_line.split()):
        candidate = " ".join(words[:len(top_line.split()) + 1])
        if measure_text_width(candidate, font_path, font_size) <= max_width:
            top_line = candidate
            bottom_line = " ".join(words[len(top_line.split()):])
    return top_line, bottom_line


def remove_white(frame):
    threshold = 240
    alpha = np.where(np.all(frame[:, :, :3] > threshold, axis=-1), 0, 255).astype("uint8")
    return np.dstack((frame, alpha))


def remove_black(frame):
    threshold = 15
    alpha = np.where(np.all(frame[:, :, :3] < threshold, axis=-1), 0, 255).astype("uint8")
    return np.dstack((frame, alpha))


def lambda_handler(event, context):
    bucket_name = os.environ.get("TARGET_BUCKET", "my-bucket")
    json_key = "most_recent_post.json"
    timestamp_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    folder = f"posts/animeutopia_{timestamp_str}"
    complete_key = f"{folder}/anime_post_complete.mp4"
    no_text_key = f"{folder}/anime_post_no_text.mp4"
    no_bg_key = f"{folder}/anime_post_no_bg.mov"
    no_text_no_bg_key = f"{folder}/anime_post_no_text_no_bg.mov"

    local_json = "/tmp/most_recent_post.json"
    s3.download_file(bucket_name, json_key, local_json)
    with open(local_json, "r", encoding="utf-8") as f:
        post_data = json.load(f)

    title_text = post_data.get("title", "No Title").upper()
    description_text = post_data.get("description", "")
    image_path = post_data.get("image_path", None)

    bg_local_path = "/tmp/background.jpg"
    if image_path and image_path.startswith("http"):
        try:
            resp = requests.get(image_path, timeout=10)
            with open(bg_local_path, "wb") as f:
                f.write(resp.content)
        except Exception as e:
            print("Image download failed:", e)
            bg_local_path = None
    elif image_path:
        try:
            s3.download_file(bucket_name, image_path, bg_local_path)
        except Exception as e:
            print("Failed to download image from S3:", e)
            bg_local_path = None

    logo_key = "artifacts/Logo.png"
    logo_local_path = "/tmp/Logo.png"
    try:
        s3.download_file(bucket_name, logo_key, logo_local_path)
    except Exception as e:
        print("Failed to download logo:", e)
        logo_local_path = None

    gradient_key = "artifacts/Black Gradient.png"
    gradient_local_path = "/tmp/Black_Gradient.png"
    try:
        s3.download_file(bucket_name, gradient_key, gradient_local_path)
    except Exception as e:
        print("Failed to download gradient:", e)
        gradient_local_path = None

    news_key = "artifacts/NEWS.mov"
    news_local_path = "/tmp/NEWS.mov"
    try:
        s3.download_file(bucket_name, news_key, news_local_path)
    except Exception as e:
        print("Failed to download news video:", e)
        news_local_path = None

    width, height = 1080, 1080
    duration_sec = 10

    if bg_local_path and os.path.exists(bg_local_path):
        bg_clip = (
            ImageClip(bg_local_path)
            .with_effects([vfx.Resize((width, height))])
            .with_duration(duration_sec)
        )
    else:
        bg_clip = (
            ColorClip(size=(width, height), color=(0, 0, 0), duration=duration_sec)
            .with_duration(duration_sec)
        )

    transparent_clip = ImageClip(
        np.zeros((height, width, 4), dtype="uint8")
    ).with_duration(duration_sec)

    if gradient_local_path and os.path.exists(gradient_local_path):
        gradient_clip = (
            ImageClip(gradient_local_path)
            .with_effects([vfx.Resize((width, height))])
            .with_duration(duration_sec)
        )
    else:
        gradient_clip = None

    if news_local_path and os.path.exists(news_local_path):
        raw_news = VideoFileClip(news_local_path).with_duration(duration_sec)
        scale_news = 750.0 / raw_news.w

        news_clip = raw_news.with_effects([
            vfx.Resize(scale_news),
        ])
        news_clip = news_clip.transform(lambda gf, t: remove_black(gf(t)))
        news_clip = news_clip.with_position((0, 0))
    else:
        news_clip = None

    base_margin = 15
    if logo_local_path and os.path.exists(logo_local_path):
        raw_logo = ImageClip(logo_local_path)
        scale_logo = 150 / raw_logo.w
        logo_clip = raw_logo.with_effects([vfx.Resize(scale_logo)]).with_duration(duration_sec)
        logo_clip = logo_clip.with_position((width - logo_clip.w - base_margin,
                                             height - logo_clip.h - base_margin))
        side_margin = max(logo_clip.w + base_margin, base_margin)
    else:
        logo_clip = None
        side_margin = base_margin

    available_width = width - (2 * side_margin)
    subtitle_side_margin = side_margin + 10
    available_subtitle_width = width - (2 * subtitle_side_margin)

    top_font_size = dynamic_font_size(title_text, max_size=60, min_size=30, ideal_length=20)
    bottom_font_size = top_font_size - 10 if top_font_size - 10 > 0 else top_font_size
    subtitle_font_size = dynamic_font_size(description_text, max_size=40, min_size=20, ideal_length=30)
    subtitle_font_size = min(subtitle_font_size, top_font_size)

    title_top, title_bottom = dynamic_split(title_text.upper(), font_path, top_font_size, available_width)
    subtitle_top, subtitle_bottom = dynamic_split(description_text.upper(), font_path, subtitle_font_size, available_subtitle_width)

    top_clip = (
        TextClip(
            text=title_top,
            font_size=top_font_size,
            color="#ec008c",
            font=font_path,
            size=(available_width, None),
            method="caption",
        )
        .with_duration(duration_sec)
    )

    bottom_clip = (
        TextClip(
            text=title_bottom,
            font_size=bottom_font_size,
            color="#ec008c",
            font=font_path,
            size=(available_width, None),
            method="caption",
        )
        .with_duration(duration_sec)
    )

    desc_top_clip = (
        TextClip(
            text=subtitle_top,
            font_size=subtitle_font_size,
            color="white",
            font=font_path,
            size=(available_subtitle_width, None),
            method="caption",
        )
        .with_duration(duration_sec)
    )

    desc_bottom_clip = (
        TextClip(
            text=subtitle_bottom,
            font_size=subtitle_font_size,
            color="white",
            font=font_path,
            size=(available_subtitle_width, None),
            method="caption",
        )
        .with_duration(duration_sec)
    )

    subtitle_bottom_y = height - 20 - desc_bottom_clip.h
    subtitle_top_y = subtitle_bottom_y - 10 - desc_top_clip.h
    bottom_title_y = subtitle_top_y - 12 - bottom_clip.h
    top_title_y = bottom_title_y - 10 - top_clip.h

    top_clip = top_clip.with_position((side_margin, top_title_y))
    bottom_clip = bottom_clip.with_position((side_margin, bottom_title_y))
    desc_top_clip = desc_top_clip.with_position((subtitle_side_margin, subtitle_top_y))
    desc_bottom_clip = desc_bottom_clip.with_position((subtitle_side_margin, subtitle_bottom_y))

    clips_complete = [bg_clip]
    if gradient_clip:
        clips_complete.append(gradient_clip)
    if news_clip:
        clips_complete.append(news_clip)
    clips_complete.extend([top_clip, bottom_clip, desc_top_clip, desc_bottom_clip])
    if logo_clip:
        clips_complete.append(logo_clip)

    complete_clip = CompositeVideoClip(clips_complete, size=(width, height)).with_duration(duration_sec)

    clips_no_text = [bg_clip]
    if gradient_clip:
        clips_no_text.append(gradient_clip)
    if news_clip:
        clips_no_text.append(news_clip)
    if logo_clip:
        clips_no_text.append(logo_clip)

    no_text_clip = CompositeVideoClip(clips_no_text, size=(width, height)).with_duration(duration_sec)

    clips_no_bg = [transparent_clip]
    if gradient_clip:
        clips_no_bg.append(gradient_clip)
    if news_clip:
        clips_no_bg.append(news_clip)
    clips_no_bg.extend([top_clip, bottom_clip, desc_top_clip, desc_bottom_clip])
    if logo_clip:
        clips_no_bg.append(logo_clip)

    no_bg_clip = CompositeVideoClip(clips_no_bg, size=(width, height)).with_duration(duration_sec)

    clips_no_text_no_bg = [transparent_clip]
    if gradient_clip:
        clips_no_text_no_bg.append(gradient_clip)
    if news_clip:
        clips_no_text_no_bg.append(news_clip)
    if logo_clip:
        clips_no_text_no_bg.append(logo_clip)

    no_text_no_bg_clip = CompositeVideoClip(clips_no_text_no_bg, size=(width, height)).with_duration(duration_sec)

    complete_local = "/tmp/anime_post_complete.mp4"
    no_text_local = "/tmp/anime_post_no_text.mp4"
    no_bg_local = "/tmp/anime_post_no_bg.mov"
    no_text_no_bg_local = "/tmp/anime_post_no_text_no_bg.mov"

    complete_clip.write_videofile(complete_local, fps=24, codec="libx264", audio=False)
    no_text_clip.write_videofile(no_text_local, fps=24, codec="libx264", audio=False)
    no_bg_clip.write_videofile(no_bg_local, fps=24, codec="png", audio=False)
    no_text_no_bg_clip.write_videofile(no_text_no_bg_local, fps=24, codec="png", audio=False)

    s3.upload_file(complete_local, bucket_name, complete_key)
    s3.upload_file(no_text_local, bucket_name, no_text_key)
    s3.upload_file(no_bg_local, bucket_name, no_bg_key)
    s3.upload_file(no_text_no_bg_local, bucket_name, no_text_no_bg_key)

    return {
        "status": "rendered",
        "video_keys": {
            "complete": complete_key,
            "no_text": no_text_key,
            "no_bg": no_bg_key,
            "no_text_no_bg": no_text_no_bg_key,
        },
    }
