import os
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Combines the process of generating a pre-signed URL for a rendered video and
    generating a pre-signed URL for the exported After Effects project file that was
    previously uploaded to S3. It sends both links in an SNS notification email.
    
    Environment Variables:
      - TARGET_BUCKET: Name of the S3 bucket where files are stored.
      - SNS_TOPIC_ARN: ARN of the SNS topic for notifications.
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

    try:
        video_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": "anime_post.mp4"},
            ExpiresIn=3600
        )
    except Exception as e:
        logger.exception("Error generating presigned URL for video file: %s", e)
        return {"error": "Failed to generate presigned URL for video file."}

    s3_project_key = "exports/anime_template_exported.aep"

    try:
        project_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": s3_project_key},
            ExpiresIn=3600
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
        "project_url": project_url
    }
