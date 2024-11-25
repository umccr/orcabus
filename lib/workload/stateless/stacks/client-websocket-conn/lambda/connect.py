import boto3
import os

def lambda_handler(event, context):
    # Get table names from environment variables
    assert 'CONNECTION_TABLE' in os.environ, "CONNECTION_TABLE environment variable is not set"
    connections_table_name = os.environ['CONNECTION_TABLE']

    dynamodb = boto3.resource('dynamodb')
    connections_table = dynamodb.Table(connections_table_name)

    connection_id = event['requestContext']['connectionId']
    
    try:
        # Store connection
        connections_table.put_item(
            Item={'connectionId': connection_id}
        )
        return {'statusCode': 200}
    except Exception as e:
        print(f"Error storing connection: {e}")
        return {'statusCode': 500, 'body': str(e)}
