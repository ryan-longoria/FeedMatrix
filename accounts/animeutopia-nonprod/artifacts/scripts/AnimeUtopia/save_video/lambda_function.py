import os
import logging
import boto3
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Trigger the Windows EC2 instance via SSM to upload the rendered video
    (anime_post.mp4) and the After Effects project file (anime_template_exported.aep)
    to the designated S3 bucket. The project file is stored under the 'exports/' prefix.
    """
    instance_id = os.environ.get("INSTANCE_ID")
    target_bucket = os.environ.get("TARGET_BUCKET")

    if not instance_id:
        error_msg = "INSTANCE_ID environment variable not set."
        logger.error(error_msg)
        return {"error": error_msg}

    if not target_bucket:
        error_msg = "TARGET_BUCKET environment variable not set."
        logger.error(error_msg)
        return {"error": error_msg}

    ec2 = boto3.client("ec2")
    waited = 0
    while waited < 300:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance_state = response["Reservations"][0]["Instances"][0]["State"]["Name"]
        if instance_state == "running":
            logger.info("Instance %s is running.", instance_id)
            break
        else:
            logger.info("Instance %s is in state '%s'. Waiting...", instance_id, instance_state)
            time.sleep(10)
            waited += 10
    else:
        error_msg = f"Instance {instance_id} did not become running within timeout."
        logger.error(error_msg)
        return {"error": error_msg}

    ssm = boto3.client("ssm")
    commands = [
        f'aws s3 cp "anime_post.mp4" "s3://{target_bucket}/anime_post.mp4"',
        f'aws s3 cp "anime_template_exported.aep" "s3://{target_bucket}/exports/anime_template_exported.aep"'
    ]

    try:
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunPowerShellScript",
            Parameters={"commands": commands}
        )
        logger.info("SSM command sent successfully: %s", response)
        return {"status": "video_upload_triggered", "ssm_command": response}
    except Exception as e:
        logger.exception("Failed to send SSM command: %s", e)
        return {"error": f"Failed to send SSM command: {e}"}
    