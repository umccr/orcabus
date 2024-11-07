import os
import boto3

client = boto3.client('verifiedpermissions')


def handler(event, context):
    response = {
        "isAuthorized": False,
    }

    auth_token = event["headers"]["authorization"]

    try:

        if auth_token:
            
            if auth_token.lower().startswith("bearer "):
                auth_token = auth_token.split(" ")[1]
            
            avp_response = client.is_authorized_with_token(
                policyStoreId=os.environ.get("POLICY_STORE_ID"),
                identityToken=auth_token,
            )

            return {
                "isAuthorized": avp_response.get("decision", None) == "ALLOW",
            }
        else:
            return response
    except BaseException:
        return response
