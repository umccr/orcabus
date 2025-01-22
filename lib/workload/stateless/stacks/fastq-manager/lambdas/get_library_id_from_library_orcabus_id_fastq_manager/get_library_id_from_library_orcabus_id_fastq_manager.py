#!/usr/bin/env python3

"""
Use the metadata tools layer to get the library id from the library orcabus id
"""

from os import environ

# Metadata imports
from metadata_tools import (
    # Orcabus helpers
    get_orcabus_token,
    # Library helpers
    get_library_from_library_orcabus_id
)


def handler(event, context):
    """
    Lambda handler.

    # Use the environment variables to customize the behavior of the function
    # Based on the use case
    ENV VAR VALUE is required
    ENV VAR FROM_ORCABUS or FROM_ID is required
    ENV VAR CONTEXT is required, one of 'subject', 'sample', 'library', 'project'
    ENV VAR RETURN_STR or RETURN_OBJ is required

    :param event:
    :param context:
    :return:
    """

    # Get the orcabus token
    environ['ORCABUS_TOKEN'] = get_orcabus_token()

    # Get value from the event object
    library_orcabus_id = event['library_orcabus_id']

    # Get the library object
    library_obj = get_library_from_library_orcabus_id(library_orcabus_id)

    # Return the library id from the library object
    return {
        "library_id": library_obj['libraryId']
    }



# if __name__ == "__main__":
#     # Import the json module
#     import json
#
#     # Set the environment variables
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "library_orcabus_id": "lib.01J9T97T3CZKPB51BQ5PCT968R"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "library_id": "LPRJ240775"
#     # }
