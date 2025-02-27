import os
import json
import logging
import boto3
import time
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def default_serializer(o):
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(f"Type {type(o)} not serializable")


def wait_for_ssm_registration(ssm_client, instance_id, timeout=300, interval=10):
    waited = 0
    while waited < timeout:
        info = ssm_client.describe_instance_information()
        registered_ids = [
            i["InstanceId"] for i in info.get("InstanceInformationList", [])
            if i.get("PingStatus") == "Online"
        ]
        if instance_id in registered_ids:
            logger.info("Instance %s is registered with SSM.", instance_id)
            return True
        else:
            logger.info("Instance %s not yet registered with SSM. Waiting...", instance_id)
            time.sleep(interval)
            waited += interval
    return False


def lambda_handler(event, context):
    """
    Trigger the video rendering process on a Windows EC2 instance using SSM.
    Waits for the instance to become "running" and registered with SSM before sending the command.
    """
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
    if not wait_for_ssm_registration(ssm, instance_id):
        error_msg = f"Instance {instance_id} did not register with SSM within timeout."
        logger.error(error_msg)
        return {"error": error_msg}
    
    try:
        ssm_response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunPowerShellScript",
            Parameters={
                "commands": [
                    "afterfx.exe -r automate_aftereffects.jsx"
                ]
            }
        )
        logger.info("SSM command sent successfully: %s", ssm_response)
        response_dict = {
            "status": "video_render_triggered",
            "ssm_command": ssm_response
        }
        serialized = json.dumps(response_dict, default=default_serializer)
        return json.loads(serialized)
    except Exception as e:
        logger.exception("Failed to send SSM command: %s", e)
        return {"error": f"Failed to send SSM command: {e}"}
