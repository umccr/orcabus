"""
Token Service JWT rotation

How rotation works:
https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotating-secrets.html

Template code based on PostgreSQL database secret rotation:
https://docs.aws.amazon.com/secretsmanager/latest/userguide/reference_available-rotation-templates.html
https://github.com/aws-samples/aws-secrets-manager-rotation-lambdas/blob/master/SecretsManagerRDSPostgreSQLRotationSingleUser/lambda_function.py

Impls Note: The following implementation code flow intentionally keeps it similar to the original AWS template code^^.
It reads a bit ugly; fully ACK. But, the point is; to keep the rotation logic closer to the advocated AWS style guide
and, one can do diff check left <> right from the template code. Feel free to refactor down the track, if any.
"""
import base64
import json
import logging
import os
from datetime import datetime, timezone

import boto3

from cognitor import CognitoTokenService, ServiceUserDto

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

token_srv = CognitoTokenService(
    user_pool_id=os.environ['USER_POOL_ID'],
    user_pool_app_client_id=os.environ['USER_POOL_APP_CLIENT_ID']
)

service_user_secret_id = os.environ['SERVICE_USER_SECRET_ID']
service_info_endpoint = os.getenv('SERVICE_INFO_ENDPOINT', None)  # TODO we need stable service info endpoint


def lambda_handler(event, context):
    """Secrets Manager Token Service JWT Rotation Handler

    This handler rotates Cognito service user JWT credential.

    The Secret SecretString is expected to be a JSON string with the following format:
    {
        'id_token': <mandatory: id_token>,
        ...,
    }

    Args:
        event (dict): Lambda dictionary of event parameters. These keys must include the following:
            - SecretId: The secret ARN or identifier
            - ClientRequestToken: The ClientRequestToken of the secret version
            - Step: The rotation step (one of createSecret, setSecret, testSecret, or finishSecret)

        context (LambdaContext): The Lambda runtime information

    Raises:
        ResourceNotFoundException: If the secret with the specified arn and stage does not exist

        ValueError: If the secret is not properly configured for rotation

        KeyError: If the secret json does not contain the expected keys

    """
    arn = event['SecretId']
    token = event['ClientRequestToken']
    step = event['Step']

    # Setup the client
    service_client = boto3.client('secretsmanager')

    # Make sure the version is staged correctly
    metadata = service_client.describe_secret(SecretId=arn)
    if "RotationEnabled" in metadata and not metadata['RotationEnabled']:
        logger.error("Secret %s is not enabled for rotation" % arn)
        raise ValueError("Secret %s is not enabled for rotation" % arn)
    versions = metadata['VersionIdsToStages']
    if token not in versions:
        logger.error("Secret version %s has no stage for rotation of secret %s." % (token, arn))
        raise ValueError("Secret version %s has no stage for rotation of secret %s." % (token, arn))
    if "AWSCURRENT" in versions[token]:
        logger.info("Secret version %s already set as AWSCURRENT for secret %s." % (token, arn))
        return
    elif "AWSPENDING" not in versions[token]:
        logger.error("Secret version %s not set as AWSPENDING for rotation of secret %s." % (token, arn))
        raise ValueError("Secret version %s not set as AWSPENDING for rotation of secret %s." % (token, arn))

    # Call the appropriate step
    if step == "createSecret":
        create_secret(service_client, arn, token)

    elif step == "setSecret":
        set_secret(service_client, arn, token)

    elif step == "testSecret":
        test_secret(service_client, arn, token)

    elif step == "finishSecret":
        finish_secret(service_client, arn, token)

    else:
        logger.error("lambda_handler: Invalid step parameter %s for secret %s" % (step, arn))
        raise ValueError("Invalid step parameter %s for secret %s" % (step, arn))


def create_secret(service_client, arn, token):
    """Generate a new secret

    This method first checks for the existence of a secret for the passed in token. If one does not exist, it will
    generate a new secret and put it with the passed in token.

    Args:
        service_client (client): The secrets manager service client

        arn (string): The secret ARN or other identifier

        token (string): The ClientRequestToken associated with the secret version

    Raises:
        ValueError: If the current secret is not valid JSON

        KeyError: If the secret json does not contain the expected keys

    """
    # Make sure the current secret exists
    current_dict = _get_secret_dict(service_client, arn, "AWSCURRENT")

    # Now try to get the secret version, if that fails, put a new secret
    try:
        _get_secret_dict(service_client, arn, "AWSPENDING", token)
        logger.info("createSecret: Successfully retrieved secret for %s." % arn)
    except service_client.exceptions.ResourceNotFoundException:
        # Get Cognito Service User login credential info from another (peer) rotating secret from Secret Manager
        resp = service_client.get_secret_value(SecretId=service_user_secret_id)
        service_user_info = json.loads(resp['SecretString'])
        # Generate new token object
        current_dict = token_srv.generate_service_user_tokens(
            user_dto=ServiceUserDto(
                username=service_user_info['username'],
                password=service_user_info['password'],
                email=service_user_info['email']
            )
        )
        # Put the secret
        service_client.put_secret_value(SecretId=arn, ClientRequestToken=token, SecretString=json.dumps(current_dict), VersionStages=['AWSPENDING'])
        logger.info("createSecret: Successfully put secret for ARN %s and version %s." % (arn, token))


def set_secret(service_client, arn, token):
    """Set the pending secret in the database

    This method tries to login to the database with the AWSPENDING secret and returns on success. If that fails, it
    tries to login with the AWSCURRENT and AWSPREVIOUS secrets. If either one succeeds, it sets the AWSPENDING password
    as the user password in the database. Else, it throws a ValueError.

    Args:
        service_client (client): The secrets manager service client

        arn (string): The secret ARN or other identifier

        token (string): The ClientRequestToken associated with the secret version

    Raises:
        ResourceNotFoundException: If the secret with the specified arn and stage does not exist

        ValueError: If the secret is not valid JSON or valid credentials are found to login to the database

        KeyError: If the secret json does not contain the expected keys

    """
    try:
        previous_dict = _get_secret_dict(service_client, arn, "AWSPREVIOUS")
    except (service_client.exceptions.ResourceNotFoundException, KeyError):
        previous_dict = None
    current_dict = _get_secret_dict(service_client, arn, "AWSCURRENT")
    pending_dict = _get_secret_dict(service_client, arn, "AWSPENDING", token)

    # First try to login with the pending secret, if it succeeds, return
    id_token = pending_dict['id_token']
    if _is_valid_jwt(id_token):
        logger.info("setSecret: AWSPENDING secret is already set as valid JWT in Cognito User for secret arn %s." % arn)
        return

    # Now try the current password
    id_token = current_dict['id_token']

    # If both current and pending do not work, try previous
    if not _is_valid_jwt(id_token) and previous_dict:
        id_token = previous_dict['id_token']

    # If we still don't have a connection, raise a ValueError
    if not _is_valid_jwt(id_token):
        logger.error("setSecret: Unable to verify Cognito JWT with previous, current, or pending secret of secret arn %s" % arn)
        raise ValueError("Unable to verify Cognito JWT with previous, current, or pending secret of secret arn %s" % arn)

    # Now set the password to the pending password
    # noop: NOTE we do not have to set any password, etc... at external service like database
    logger.info("setSecret: Successfully set JWT for Service User in Cognito for secret arn %s." % (arn))


def test_secret(service_client, arn, token):
    """Test the pending secret against the database

    This method tries to log into the database with the secrets staged with AWSPENDING and runs
    a permissions check to ensure the user has the correct permissions.

    Args:
        service_client (client): The secrets manager service client

        arn (string): The secret ARN or other identifier

        token (string): The ClientRequestToken associated with the secret version

    Raises:
        ResourceNotFoundException: If the secret with the specified arn and stage does not exist

        ValueError: If the secret is not valid JSON or valid credentials are found to login to the database

        KeyError: If the secret json does not contain the expected keys

    """
    # Try to login with the pending secret, if it succeeds, return
    pending_dict = _get_secret_dict(service_client, arn, "AWSPENDING", token)
    id_token = pending_dict['id_token']
    if _is_valid_jwt(id_token):
        # Being able to generate tokens using pending username/password consider success.
        logger.info("testSecret: Successfully set Cognito Service User JWT with AWSPENDING secret in %s." % arn)
        return
    else:
        logger.error("testSecret: Unable to verify Cognito JWT with pending secret of secret ARN %s" % arn)
        raise ValueError("Unable to verify Cognito JWT with pending secret of secret ARN %s" % arn)


def finish_secret(service_client, arn, token):
    """Finish the rotation by marking the pending secret as current

    This method finishes the secret rotation by staging the secret staged AWSPENDING with the AWSCURRENT stage.

    Args:
        service_client (client): The secrets manager service client

        arn (string): The secret ARN or other identifier

        token (string): The ClientRequestToken associated with the secret version

    """
    # First describe the secret to get the current version
    metadata = service_client.describe_secret(SecretId=arn)
    current_version = None
    for version in metadata["VersionIdsToStages"]:
        if "AWSCURRENT" in metadata["VersionIdsToStages"][version]:
            if version == token:
                # The correct version is already marked as current, return
                logger.info("finishSecret: Version %s already marked as AWSCURRENT for %s" % (version, arn))
                return
            current_version = version
            break

    # Finalize by staging the secret version current
    service_client.update_secret_version_stage(SecretId=arn, VersionStage="AWSCURRENT", MoveToVersionId=token, RemoveFromVersionId=current_version)
    logger.info("finishSecret: Successfully set AWSCURRENT stage to version %s for secret %s." % (token, arn))


# --- module internal functions


def _get_secret_dict(service_client, arn, stage, token=None):
    """Gets the secret dictionary corresponding for the secret arn, stage, and token

    This helper function gets credentials for the arn and stage passed in and returns the dictionary by parsing the
    JSON string

    Args:
        service_client (client): The secrets manager service client

        arn (string): The secret ARN or other identifier

        token (string): The ClientRequestToken associated with the secret version, or None if no validation is desired

        stage (string): The stage identifying the secret version

    Returns:
        SecretDictionary: Secret dictionary

    Raises:
        ResourceNotFoundException: If the secret with the specified arn and stage does not exist

        ValueError: If the secret is not valid JSON

    """
    required_fields = ['id_token']

    # Only do VersionId validation against the stage if a token is passed in
    if token:
        secret = service_client.get_secret_value(SecretId=arn, VersionId=token, VersionStage=stage)
    else:
        secret = service_client.get_secret_value(SecretId=arn, VersionStage=stage)
    plaintext = secret['SecretString']
    secret_dict = json.loads(plaintext)

    # Run validations against the secret
    for field in required_fields:
        if field not in secret_dict:
            raise KeyError("%s key is missing from secret JSON" % field)

    # Parse and return the secret JSON string
    return secret_dict


def _is_valid_jwt(this_id_token: str) -> bool:
    """
    The following should be a good self-contained JWT check for now.

    We could do a bit more lengthy check here. But that typically the required process at client side code. And, may
    require crypto library to verifying the signature with well-known jwks, etc. See below.
    https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html
    """
    tok_vec = this_id_token.split('.')

    if len(tok_vec) != 3:
        return False

    tok_payload = json.loads(str(base64.b64decode(tok_vec[1] + "=="), "utf-8"))

    tok_use = tok_payload['token_use']
    iat = tok_payload['iat']
    exp = tok_payload['exp']

    iat_dt = datetime.fromtimestamp(iat, timezone.utc)
    exp_dt = datetime.fromtimestamp(exp, timezone.utc)
    delta = exp_dt - iat_dt

    # all these must be true
    return delta.days == 1 and tok_use == 'id'
