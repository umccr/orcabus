import boto3
import json
import os

def lambda_handler(event, context):
    
    assert os.environ['CONNECTION_TABLE'] is not None, "CONNECTION_TABLE environment variable is not set"
    assert os.environ['WEBSOCKET_API_ENDPOINT'] is not None, "WEBSOCKET_API_ENDPOINT environment variable is not set"
    
    # Get environment variables
    connections_table_name = os.environ['CONNECTION_TABLE']
   
    # connections URL with replace wss:// header to https
    websocket_endpoint = os.environ['WEBSOCKET_API_ENDPOINT'].replace('wss://', 'https://')

    dynamodb = boto3.resource('dynamodb')
    connections_table = dynamodb.Table(connections_table_name)

    # Initialize API Gateway client
    apigw_client = boto3.client('apigatewaymanagementapi', 
        endpoint_url=websocket_endpoint)

    print(f"Received event: {event}, websocket endpoint: {websocket_endpoint}")
    
    try:
        # Initialize response data
        data = event
        response_data = {
            'type': data.get('type', ''),
            'message': data.get('message', '')
        }
        
        # Broadcast to all connections
        connections = connections_table.scan()['Items']
        
        for connection in connections:
            connection_id = connection['ConnectionId']
            try:
                apigw_client.post_to_connection(
                    ConnectionId=connection_id,
                    Data=json.dumps(response_data)
                )
            except apigw_client.exceptions.GoneException:
                # Remove stale connection
                connections_table.delete_item(Key={'connectionId': connection_id})
            except Exception as e:
                print(f"Failed to post message to {connection_id}: {e}")
    
        return {'statusCode': 200}
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid JSON in request body'})
        }
    except KeyError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Missing required field: {str(e)}'})
        }
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
        
        
#  test case
#  curl -X POST https://<api-id>.execute-api.<region>.amazonaws.com/Prod/message -H "Content-Type: application/json" -d '{"type": "test", "message": "Hello, world!"}'
#  invoke lambda function from aws console, cmd: aws lambda invoke --function-name <function-name> --payload '{"type": "test", "message": "Hello, world!"}' response.json
#  check cloudwatch logs for response