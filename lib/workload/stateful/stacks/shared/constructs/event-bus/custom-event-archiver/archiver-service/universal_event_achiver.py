import json
import boto3
import os
import re
import logging
from datetime import datetime, timezone

# Initialize S3 client
s3 = boto3.client('s3')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    #assert the environment variable is set
    assert os.getenv('BUCKET_NAME'), "BUCKET_NAME environment variable is not set"
    
    BUCKET_NAME = os.getenv('BUCKET_NAME')
    
    # Current timestamp
    now = datetime.now(timezone.utc)
    time_stamp = str(now.timestamp()) # for object name
    time_stamp_formated = now.strftime("%Y-%m-%d__%H-%M-%S") # for tagging
    
    # Extract the event title (type) from detail type
    event_type = sanitize_string(event.get('detail-type', 'undefinedEvent'))
    
    # Formatting the S3 key with year/month/day partitioning
    key = f'events/year={now.year}/month={now.month:02}/day={now.day:02}/{event_type+'_'+time_stamp}.json'

    # Convert the event to JSON
    event_json = json.dumps(event)
    default_tags = {
        'event_type': event_type,
        'event_time': time_stamp_formated,
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