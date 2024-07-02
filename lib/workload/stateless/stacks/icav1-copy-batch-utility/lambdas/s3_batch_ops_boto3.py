import boto3
import os
from urllib import parse
from botocore.client import Config
from botocore.exceptions import ClientError as S3ClientError
from boto3.s3.transfer import TransferConfig
import logging

## TODO: Figure out if we can leverage ETag cleverly for MD5 compute,
# separating its custom chunks prefix and retrieving the final computed sum,
# otherwise it could be too expensive to compute for each object.

# Define Environmental Variables
target_bucket = str(os.environ['destination_bucket'])
target_key = str(os.environ['destination_bucket_prefix'])
my_max_pool_connections = int(os.environ['max_pool_connections'])
my_max_concurrency = int(os.environ['max_concurrency'])
my_multipart_chunksize = int(os.environ['multipart_chunksize'])
my_max_attempts = int(os.environ['max_attempts'])

# ICAv1/GDS creds, accessible via SSM and populated by another lambda
ica_v1_aws_access_key_id=str(os.environ['ica_v1_aws_access_key_id']),
ica_v1_aws_secret_access_key=str(os.environ['ica_v1_aws_secret_access_key']), #pragma: allowlist secret
ica_v1_aws_session_token=str(os.environ['ica_v1_aws_session_token']),

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel('INFO')

# Enable Verbose logging for Troubleshooting
# boto3.set_stream_logger("")

# Set and Declare Configuration Parameters
transfer_config = TransferConfig(max_concurrency=my_max_concurrency, multipart_chunksize=my_multipart_chunksize)
config = Config(max_pool_connections=my_max_pool_connections, retries = {'max_attempts': my_max_attempts})
myargs = {'ACL': 'bucket-owner-full-control' }

# Instantiate S3 clients
s3Client = boto3.client('s3', config=config)
# destS3Client = boto3.client('s3',
#                             aws_access_key=ica_v1_aws_access_key_id,
#                             aws_secret_access_key=ica_v1_aws_secret_access_key, #pragma: allowlist secret
#                             aws_session_token=ica_v1_aws_session_token,
#                             config=config)

def handler(event, context):
    # Parse job parameters from Amazon S3 batch operations
    invocationId = event['invocationId']
    invocationSchemaVersion = event['invocationSchemaVersion']

    # Prepare results
    results = []

    # Parse Amazon S3 Key, Key Version, and Bucket ARN
    taskId = event['tasks'][0]['taskId']
    # use unquote_plus to handle various characters in S3 Key name
    s3Key = parse.unquote_plus(event['tasks'][0]['s3Key'], encoding='utf-8')
    s3Bucket = event['tasks'][0]['s3Bucket']

    try:
    # Prepare result code and string
        resultCode = None
        resultString = None

        # Construct Copy Object
        copy_source = {'Bucket': s3Bucket, 'Key': s3Key}

        # Initiate the Actual Copy Operation and include transfer config option
        logger.info(f"starting copy of object {s3Key} between SOURCEBUCKET: {s3Bucket} and DESTINATIONBUCKET: {s3Bucket}")
        # Note: This is a boto3 inject.py method: https://github.com/boto/boto3/blob/fb608de3453155578fd68a3a627e27b39f44647f/boto3/s3/inject.py#L371
        # We might need to segregate S3 s3clients into source/destination if destination S3 Batch IAM role/policies are not enough.
        response = s3Client.copy(copy_source, target_bucket, target_key, Config=transfer_config, ExtraArgs=myargs)
        # Confirm copy was successful
        logger.info("Successfully completed the copy process!")

        # Mark as succeeded
        resultCode = 'Succeeded'
        resultString = str(response)
    except S3ClientError as e:
        # log errors, some errors does not have a response, so handle them
        logger.error(f"Unable to complete requested operation, see Clienterror details below:")
        try:
            logger.error(e.response)
            errorCode = e.response.get('Error', {}).get('Code')
            errorMessage = e.response.get('Error', {}).get('Message')
            errorS3RequestID = e.response.get('ResponseMetadata', {}).get('RequestId')
            errorS3ExtendedRequestID = e.response.get('ResponseMetadata', {}).get('HostId')
            resultCode = 'PermanentFailure'
            resultString = '{}: {}: {}: {}'.format(errorCode, errorMessage, errorS3RequestID, errorS3ExtendedRequestID)
        except AttributeError:
            logger.error(e)
            resultCode = 'PermanentFailure'
            resultString = '{}'.format(str(e))
    finally:
        results.append({
        'taskId': taskId,
        'resultCode': resultCode,
        'resultString': resultString
        })

    return {
        'invocationSchemaVersion': invocationSchemaVersion,
        'treatMissingKeysAs': 'PermanentFailure',
        'invocationId': invocationId,
        'results': results
    }