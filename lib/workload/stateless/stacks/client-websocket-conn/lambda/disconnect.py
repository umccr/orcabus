import boto3
import os

def lambda_handler(event, context):
    # Get table name from environment variable
    assert 'CONNECTION_TABLE' in os.environ, "CONNECTION_TABLE environment variable is not set"
    connections_table_name = os.environ['CONNECTION_TABLE']
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(connections_table_name)

    connection_id = event['requestContext']['connectionId']
    
    try:
        table.delete_item(Key={'ConnectionId': connection_id})
        return {'statusCode': 200}
    except Exception as e:
        print(f"Error deleting connection: {e}")
        return {'statusCode': 500, 'body': str(e)}