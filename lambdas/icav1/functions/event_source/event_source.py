import json
import os
import boto3
from botocore.errorfactory import ClientError
import logging
import eb_util

S3_STORE_EVENT_BUCKET_NAME = os.getenv('STORE_EVENT_BUCKET_NAME')
S3_CLIENT = boto3.client('s3')

# Constant Variables
ICA_EVENT_VERSION = "ICAV1"

# Logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event):
    logger.info("Processing event: ", json.dumps(event, indent=4))

    # Check if event has already arrived before
    s3_key = generate_key_from_event(event)
    logger.info(f"Checking if the following key exist. Key: {s3_key}")

    logger.info(f"Checking event existence in S3 store")
    try:
        object_metadata = S3_CLIENT.head_object(
            Bucket=S3_STORE_EVENT_BUCKET_NAME,
            Key=generate_key_from_event)
    except ClientError:
        logger.info("Result: No event match in S3 bucket")

    else:
        logger.info(f"Result: Object had exist from previous event. \n"
                    f"Object metadata: {json.dumps(object_metadata, indent=4)}")
        logger.info(f"Terminating...")
        raise ValueError

    # Storing event in
    logger.info(f"Storing event to s3 bucket")
    try:
        S3_CLIENT.Object.put_object(
            Body=event,
            Key=s3_key
        )
    except ClientError:
        logger.error(f"Something went wrong on storing event to the bucket.")
        # ... send to DLQ

    return event


def generate_key_from_event(event):
    event_records = event["Records"][0]

    event_type = event_records["messageAttributes"]["type"]["stringValue"]
    event_message_id = event_records["messageId"]

    return f"{ICA_EVENT_VERSION}/{eb_util.get_datestamp()}/{event_type}.{event_message_id}"
