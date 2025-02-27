import json
import os
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

BUCKET_NAME = os.environ.get("BUCKET_NAME", "your-s3-bucket")

s3 = boto3.client("s3")


def lambda_handler(event, context):
    """
    Store the processed post data in S3 as a JSON file.

    Args:
        event (dict): Event data containing a 'post' key with post details.
        context (object): Lambda context object.

    Returns:
        dict: Dictionary indicating storage status and S3 key used.
    """
    post = event.get("post")
    if not post:
        post = event.get("processedContent", {}).get("post", {})

    if not post:
        error_msg = "No 'post' data found in event."
        logger.error(error_msg)
        return {"status": "error", "error": error_msg}

    json_data = json.dumps(post, indent=4)
    s3_key = "most_recent_post.json"

    try:
        s3.put_object(Bucket=BUCKET_NAME, Key=s3_key, Body=json_data)
        logger.info("Post data stored in S3 bucket '%s' with key '%s'.", BUCKET_NAME, s3_key)
        return {"status": "stored", "s3_key": s3_key}
    except Exception as e:
        logger.exception("Failed to store post data in S3: %s", e)
        return {"status": "error", "error": str(e)}
