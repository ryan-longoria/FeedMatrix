import os
import logging
import boto3
from datetime import datetime, timezone
import uuid

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Combines the process of generating pre-signed URLs for a rendered video and the exported
    After Effects project file from an S3 bucket, then sends both links in an SNS notification email.
    
    Environment Variables:
      - TARGET_BUCKET: Name of the S3 bucket where files are stored.
      - SNS_TOPIC_ARN: ARN of the SNS topic for notifications.
    
    To prevent overwriting existing files, unique file names are generated using the current UTC timestamp
    (as a timezone-aware object) and a UUID.
    
    Returns:
      dict: A dictionary containing the status, video_url, project_url, and the unique keys used,
            or an error message.
    """
    bucket = os.environ.get("TARGET_BUCKET")
    if not bucket:
        error_msg = "TARGET_BUCKET environment variable not set."
        logger.error(error_msg)
        return {"error": error_msg}

    sns_topic_arn = os.environ.get("SNS_TOPIC_ARN")
    if not sns_topic_arn:
        error_msg = "SNS_TOPIC_ARN environment variable not set."
        logger.error(error_msg)
        return {"error": error_msg}

    s3 = boto3.client("s3")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    unique_id = uuid.uuid4().hex
    video_key = f"anime_post_{timestamp}_{unique_id}.mp4"
    project_key = f"exports/anime_template_exported_{timestamp}_{unique_id}.aep"

    try:
        video_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": video_key},
            ExpiresIn=604800
        )
    except Exception as e:
        logger.exception("Error generating presigned URL for video file: %s", e)
        return {"error": "Failed to generate presigned URL for video file."}

    try:
        project_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": project_key},
            ExpiresIn=604800
        )
    except Exception as e:
        logger.exception("Error generating presigned URL for project file: %s", e)
        return {"error": "Failed to generate presigned URL for project file."}

    subject = "New AnimeUtopia Post is Ready!"
    message = (
        f"Your new post has been processed.\n\n"
        f"Video URL: {video_url}\n\n"
        f"After Effects Project URL: {project_url}"
    )

    sns = boto3.client("sns")
    try:
        sns.publish(
            TopicArn=sns_topic_arn,
            Subject=subject,
            Message=message
        )
    except Exception as e:
        logger.exception("Error publishing SNS notification: %s", e)
        return {"error": "Failed to send SNS notification."}

    logger.info("Notification sent successfully.")
    return {
        "status": "notification_sent",
        "video_url": video_url,
        "project_url": project_url,
        "video_key": video_key,
        "project_key": project_key
    }
