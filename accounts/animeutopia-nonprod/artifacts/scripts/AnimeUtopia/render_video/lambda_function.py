import os
import json
import logging
import boto3
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Trigger the video rendering process on a Windows EC2 instance using SSM.
    Waits for the instance to become "running" before sending the SSM command.

    Args:
        event (dict): Event data containing a 'post' key with post details.
        context (object): Lambda context object.

    Returns:
        dict: Dictionary indicating the status of the video render trigger.
    """
    post = event.get("post", {})
    instance_id = os.environ.get("INSTANCE_ID")
    if not instance_id:
        error_msg = "INSTANCE_ID environment variable not set."
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
    try:
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={
                "commands": [
                    "afterfx.exe -r automate_aftereffects.jsx"
                ]
            }
        )
        logger.info("SSM command sent successfully: %s", response)
        return {"status": "video_render_triggered", "ssm_command": response}
    except Exception as e:
        logger.exception("Failed to send SSM command: %s", e)
        return {"error": f"Failed to send SSM command: {e}"}
