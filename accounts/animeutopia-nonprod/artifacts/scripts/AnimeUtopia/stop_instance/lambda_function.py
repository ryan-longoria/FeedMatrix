import os
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Lambda function to stop an EC2 instance.

    This function retrieves the EC2 instance ID and AWS region from the environment
    variables, creates an EC2 client using boto3, and attempts to stop the specified instance.

    Args:
        event (dict): AWS Lambda event data (not used in this function).
        context (object): AWS Lambda context object (provides runtime information).

    Returns:
        dict: A dictionary containing the status of the stop operation, the instance ID,
              and the response from the stop_instances call or an error message.
    """
    instance_id = os.environ.get("EC2_INSTANCE_ID")
    region = os.environ.get("AWS_REGION", "us-east-2")

    if not instance_id:
        error_msg = "EC2_INSTANCE_ID environment variable not set."
        logger.error(error_msg)
        return {"status": "error", "error": error_msg}

    ec2 = boto3.client("ec2", region_name=region)

    try:
        response = ec2.stop_instances(InstanceIds=[instance_id])
        logger.info("Stopping instance %s: %s", instance_id, response)
        return {
            "status": "instance_stopped",
            "instance_id": instance_id,
            "response": response,
        }
    except Exception as e:
        logger.exception("Error stopping instance %s: %s", instance_id, e)
        return {"status": "error", "error": str(e)}
