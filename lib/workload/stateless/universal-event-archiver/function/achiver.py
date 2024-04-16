import json
import boto3
from datetime import datetime, timezone
import os
import re
import logging

# Initialize S3 client
s3 = boto3.client('s3')

# The name of the bucket
BUCKET_NAME = os.getenv('BUCKET_NAME')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    
    # Current timestamp
    now = datetime.now(timezone.utc)
    time_stamp = str(now.timestamp()) # for object name
    time_stamp_details = now.strftime("%Y-%m-%d__%H-%M-%S") # for tagging
    
    # Extract the event title (type) from detail type
    event_title = sanitize_string(event.get('detail-type', 'undefinedEvent'))
    
    # Formatting the S3 key with year/month/day partitioning
    key = f'events/{now.year}/{now.month:02}/{now.day:02}/{event_title+'_'+time_stamp}.json'

    # Convert the event to JSON
    event_json = json.dumps(event)
    default_tags = {
        'event_type': event_title,
        'event_time': time_stamp_details,
    }

    # Write the JSON to an S3 bucket
    try:
        s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=event_json, Tagging='&'.join([f'{k}={v}' for k, v in default_tags.items()]))
        logger.info("Event stored:", key)
    except Exception as e:
        logger.error("Error storing event:", str(e))
        raise e

    return {
        'statusCode': 200,
        'body': json.dumps('Event archived successfully! Archived path: '+ key)
    }

def sanitize_string(input_string):
    return re.sub(r'[^\w]+', '_', input_string.strip()).strip('_')