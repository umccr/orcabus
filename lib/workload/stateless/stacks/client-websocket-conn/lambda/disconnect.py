import boto3
import os

def lambda_handler(event, context):
    # Get table name from environment variable
    connections_table_name = os.environ['CONNECTION_TABLE']
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(connections_table_name)

    connection_id = event['requestContext']['connectionId']
    
    try:
        table.delete_item(Key={'ConnectionId': connection_id})
        return {'statusCode': 200}
    except Exception as e:
        return {'statusCode': 500, 'body': str(e)}