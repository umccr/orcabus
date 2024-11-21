import boto3
import os

def lambda_handler(event, context):
    # Get table names from environment variables
    connections_table_name = os.environ['CONNECTION_TABLE']

    dynamodb = boto3.resource('dynamodb')
    connections_table = dynamodb.Table(connections_table_name)

    connection_id = event['requestContext']['connectionId']
    
    try:
        # Store connection
        connections_table.put_item(
            Item={'ConnectionId': connection_id}
        )
    except Exception as e:
        return {'statusCode': 500, 'body': str(e)}

    return {'statusCode': 200}