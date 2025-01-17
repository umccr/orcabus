"""
Cognito Service User credential rotation

How rotation works:
https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotating-secrets.html

Template code based on PostgreSQL database secret rotation:
https://docs.aws.amazon.com/secretsmanager/latest/userguide/reference_available-rotation-templates.html
https://github.com/aws-samples/aws-secrets-manager-rotation-lambdas/blob/master/SecretsManagerRDSPostgreSQLRotationSingleUser/lambda_function.py

Impls Note: The following implementation code flow intentionally keeps it similar to the original AWS template code^^.
It reads a bit ugly; fully ACK. But, the point is; to keep the rotation logic closer to the advocated AWS style guide
and, one can do diff check left <> right from the template code. Feel free to refactor down the track, if any.
"""
import json
import logging
import os

import boto3

from cognitor import CognitoTokenService, ServiceUserDto

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

token_srv = CognitoTokenService(
    user_pool_id=os.environ['USER_POOL_ID'],
    user_pool_app_client_id=os.environ['USER_POOL_APP_CLIENT_ID']
)


def lambda_handler(event, context):
    """Secrets Manager Cognito Service User Handler

    The Secret SecretString is expected to be a JSON string with the following format:
    {
        'username': <required: username>,
        'password': <required: password>,
        'email': <optional: email>
    }

    Args:
        event (dict): Lambda dictionary of event parameters. These keys must include the following:
            - SecretId: The secret ARN or identifier
            - ClientRequestToken: The ClientRequestToken of the secret version
            - Step: The rotation step (one of createSecret, setSecret, testSecret, finishSecret or resetPendingSecret)

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

    elif step == "resetPendingSecret":
        reset_pending_secret(service_client, arn, token)

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
        # Generate a random password
        current_dict['password'] = token_srv.generate_password()
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

    # First try to rotate using pending secret, if it succeeds, return
    is_rotated = _rotate(pending_dict, arn)
    if is_rotated:
        logger.info("setSecret: AWSPENDING secret is already set as password in Cognito User for secret arn %s." % arn)
        return

    # If rotation with pending secret didn't work then fall back to current secret

    # Make sure the user from current and pending match
    if current_dict['username'] != pending_dict['username']:
        logger.error("setSecret: Attempting to modify user %s other than current user %s" % (pending_dict['username'], current_dict['username']))
        raise ValueError("Attempting to modify user %s other than current user %s" % (pending_dict['username'], current_dict['username']))

    # Now try the current password
    is_rotated = _rotate(current_dict, arn)

    # If both current and pending do not work, try previous as last resort
    if not is_rotated and previous_dict:

        # Make sure the user/host from previous and pending match
        if previous_dict['username'] != pending_dict['username']:
            logger.error("setSecret: Attempting to modify user %s other than previous valid user %s" % (pending_dict['username'], previous_dict['username']))
            raise ValueError("Attempting to modify user %s other than previous valid user %s" % (pending_dict['username'], previous_dict['username']))

        is_rotated = _rotate(previous_dict, arn)

    # If we still don't have a connection, raise a ValueError
    if not is_rotated:
        logger.error("setSecret: Unable to log into Cognito with previous, current, or pending secret of secret arn %s" % arn)
        raise ValueError("Unable to log into Cognito with previous, current, or pending secret of secret arn %s" % arn)


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
    tokens = _generate_new_tokens_for(pending_dict)  # test whether we can generate tokens using pending secret
    if _is_valid(tokens):
        # Being able to generate tokens using pending username/password consider success.
        logger.info("testSecret: Successfully signed into Cognito with AWSPENDING secret in %s." % arn)
        return
    else:
        logger.error("testSecret: Unable to log into Cognito with pending secret of secret ARN %s" % arn)
        raise ValueError("Unable to log into Cognito with pending secret of secret ARN %s" % arn)


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


def reset_pending_secret(service_client, arn, token):
    """Clears the pending secret so that a new one can be generated.

    Args:
        service_client (client): The secrets manager service client

        arn (string): The secret ARN or other identifier

        token (string): The ClientRequestToken associated with the secret version

    """
    secret = service_client.get_secret_value(
        SecretId=arn, VersionId=token, VersionStage="AWSPENDING"
    )
    version_id = secret["VersionId"]

    service_client.update_secret_version_stage(
        SecretId=arn, VersionStage="AWSPENDING", RemoveFromVersionId=version_id
    )
    logger.info(
        "resetPendingSecret: Successfully removed AWSPENDING stage from version %s for secret %s."
        % (token, arn)
    )


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
    required_fields = ['username', 'password']

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


def _rotate(this_dict, arn) -> bool:
    """
    Try to rotate user password in Cognito. If any exception is raised, returns False. Otherwise, returns True.
    """
    try:
        token_srv.rotate_service_user_password(user_dto=ServiceUserDto(
            username=this_dict['username'],
            password=this_dict['password'],
            email=this_dict['email'],
        ))
        logger.info("setSecret: Successfully set password for user %s in Cognitor for secret arn %s." % (this_dict['username'], arn))
        return True
    except Exception as e:
        logger.error(e)
        return False


def _generate_new_tokens_for(this_dict: dict) -> dict:
    """
    Generate JWT (id_token, refresh_token, access_token, ...) tokens for the given Service User `this_dict` credential.
    Note, this always return the newly generated tokens that is valid as long as the pass-in `this_dict`
    Service User login cred works.
    """
    user_dto = ServiceUserDto(
        username=this_dict['username'],
        password=this_dict['password'],
        email=this_dict['email']
    )
    return token_srv.generate_service_user_tokens(user_dto=user_dto)


def _is_valid(tokens: dict) -> bool:
    return 'id_token' in tokens.keys()
