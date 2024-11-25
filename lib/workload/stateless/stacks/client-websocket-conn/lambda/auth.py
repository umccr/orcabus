import os
import logging
import jwt
import requests
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def generate_policy(principal_id, effect, resource):
    return {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'execute-api:Invoke',
                'Effect': effect,
                'Resource': resource
            }]
        }
    }

def get_public_key():
    """Get Cognito public key for JWT verification"""
    url = f'https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json'
    try:
        response = requests.get(url)
        return response.json()['keys'][0]  # Get the first key
    except Exception as e:
        logger.error(f"Error getting public key: {str(e)}")
        raise

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Simple Lambda authorizer for WebSocket"""
    logger.info("WebSocket authorization request")
    # Get environment variables
    assert 'COGNITO_USER_POOL_ID' in os.environ, "COGNITO_USER_POOL_ID is not set"
    assert 'COGNITO_REGION' in os.environ, "COGNITO_REGION is not set"
    
    COGNITO_USER_POOL_ID = os.environ['COGNITO_USER_POOL_ID']
    COGNITO_REGION = os.environ.get('COGNITO_REGION', 'ap-southeast-2')
    try:
        # Get token from headers
        # Check both header and querystring
        auth_token = None
        if event.get('headers', {}).get('Authorization'):
            auth_token = event['headers']['Authorization']
        elif event.get('queryStringParameters', {}).get('Authorization'):
            auth_token = event['queryStringParameters']['Authorization']
    
        if not auth_token:
            return generate_policy('user', 'Deny', event['methodArn'])
    

        # Get public key
        public_key = get_public_key()
        
        # Verify token
        decoded = jwt.decode(
            auth_token,
            public_key,
            algorithms=['RS256'],
            issuer=f'https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}'
        )
        
        # Generate allow policy
        return generate_policy(decoded['sub'], 'Allow', event['methodArn'])
    except Exception as e:
        logger.error(f"Authorization failed: {str(e)}")
        # Return deny policy
        return generate_policy('unauthorized', 'Deny', event['methodArn'])
