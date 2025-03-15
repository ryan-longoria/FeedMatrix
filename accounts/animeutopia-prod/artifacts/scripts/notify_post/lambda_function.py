import datetime
import json
import os
import uuid

import boto3
import logging
import requests
from datetime import timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    bucket = os.environ.get("TARGET_BUCKET")
    if not bucket:
        error_msg = "TARGET_BUCKET environment variable not set."
        logger.error(error_msg)
        return {"error": error_msg}

    teams_webhook_url = os.environ.get("TEAMS_WEBHOOK_URL")
    if not teams_webhook_url:
        error_msg = "TEAMS_WEBHOOK_URL environment variable not set."
        logger.error(error_msg)
        return {"error": error_msg}

    s3 = boto3.client("s3")
    timestamp = datetime.datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    unique_id = uuid.uuid4().hex

    video_keys = event.get("video_keys", {})
    if not video_keys:
        error_msg = "No video keys found in event."
        logger.error(error_msg)
        return {"error": error_msg}

    presigned_urls = {}
    for variant, key in video_keys.items():
        try:
            url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=604800
            )
            presigned_urls[variant] = url
        except Exception as e:
            logger.exception("Error generating presigned URL for %s: %s", variant, e)
            presigned_urls[variant] = None

    descriptions = {
        "complete": (
            "Complete Post: Contains background image, gradient, title & subtitle, "
            "news clip, and logo."
        ),
        "no_text": (
            "No Text: Contains background image, gradient, news clip, and logo; "
            "omits title & subtitle."
        ),
        "no_bg": (
            "No Background: Uses a transparent background (no background image) along with "
            "gradient, title & subtitle, news clip, and logo."
        ),
        "no_text_no_bg": (
            "No Text & No Background: Uses a transparent background and omits title & subtitle, "
            "leaving only gradient, news clip, and logo."
        ),
    }

    message_text = "Your new post has been processed!\n\n"
    for variant, url in presigned_urls.items():
        desc = descriptions.get(variant, variant)
        message_text += f"**{desc}**: [View Video]({url})\n\n"

    teams_payload = {"text": message_text}
    try:
        response = requests.post(
            teams_webhook_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(teams_payload)
        )
        response.raise_for_status()
    except Exception as e:
        logger.exception("Error posting message to Microsoft Teams: %s", e)
        return {"error": "Failed to post to Microsoft Teams channel."}

    logger.info("Message posted to Microsoft Teams successfully.")
    return {
        "status": "message_posted",
        "video_keys": video_keys,
        "video_urls": presigned_urls,
    }
