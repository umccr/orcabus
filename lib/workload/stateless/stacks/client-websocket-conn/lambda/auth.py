import os
import logging
import jwt
import requests
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get environment variables
COGNITO_USER_POOL_ID = os.environ['COGNITO_USER_POOL_ID']
COGNITO_REGION = os.environ.get('COGNITO_REGION', 'ap-southeast-2')

def get_public_key():
    """Get Cognito public key for JWT verification"""
    url = f'https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json'
    try:
        response = requests.get(url)
        return response.json()['keys'][0]  # Get the first key
    except Exception as e:
        logger.error(f"Error getting public key: {str(e)}")
        raise

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Simple Lambda authorizer for WebSocket"""
    logger.info("WebSocket authorization request")
    
    try:
        # Get token from headers
        token = event.get('headers', {}).get('Authorization', '').replace('Bearer ', '')
        if not token:
            raise Exception('No token provided')

        # Get public key
        public_key = get_public_key()
        
        # Verify token
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            issuer=f'https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}'
        )
        
        # Generate allow policy
        return {
            'principalId': decoded['sub'],
            'policyDocument': {
                'Version': '2012-10-17',
                'Statement': [{
                    'Action': 'execute-api:Invoke',
                    'Effect': 'Allow',
                    'Resource': event['methodArn']
                }]
            },
            'context': {
                'userId': decoded['sub']
            }
        }
        
    except Exception as e:
        logger.error(f"Authorization failed: {str(e)}")
        # Return deny policy
        return {
            'principalId': 'unauthorized',
            'policyDocument': {
                'Version': '2012-10-17',
                'Statement': [{
                    'Action': 'execute-api:Invoke',
                    'Effect': 'Deny',
                    'Resource': event['methodArn']
                }]
            }
        }