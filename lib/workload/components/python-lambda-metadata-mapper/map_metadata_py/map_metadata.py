#!/usr/bin/env python3


# !/usr/bin/env python3

"""
This script is used to get the subject orcabus id from the subject id.
"""

# Standard imports
from os import environ

# Metadata imports
from metadata_tools import (
    # Orcabus helpers
    get_orcabus_token,
    # Subject helpers
    get_subject_from_subject_orcabus_id, get_subject_from_subject_id,
    # Sample helpers
    get_sample_from_sample_orcabus_id, get_sample_from_sample_id,
    # Library helpers
    get_library_from_library_orcabus_id, get_library_from_library_id,
    # Project helpers
    get_project_from_project_orcabus_id, get_project_from_project_id,
    # Individual helpers
    get_individual_from_individual_orcabus_id, get_individual_from_individual_id,
    # Contact helpers
    get_contact_from_contact_orcabus_id, get_contact_from_contact_id
)

# Globals
ALLOWED_CONTEXTS = ['individual', 'subject', 'sample', 'library', 'project', 'contact']


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
    value = event['value']

    # Check if FROM_ORCABUS or FROM_ID is set
    # But make sure not both are set
    # And that at least one is set
    if ('FROM_ORCABUS' in environ and 'FROM_ID' in environ) or (
            'FROM_ORCABUS' not in environ and 'FROM_ID' not in environ):
        raise ValueError("Either FROM_ORCABUS or FROM_ID must be set, but not both.")
    is_from_orcabus = 'FROM_ORCABUS' in environ

    # Get the context
    # And ensure that context is one of
    # 'subject', 'sample', 'library', 'project'
    if 'CONTEXT' not in environ:
        raise ValueError("CONTEXT must be set.")
    context = environ['CONTEXT']
    if context not in ALLOWED_CONTEXTS:
        raise ValueError(f"CONTEXT must be one of {' '.join(ALLOWED_CONTEXTS)}")

    # Get the return type
    # And ensure that it is one of 'id', 'object' and that not both are set
    if 'RETURN_STR' not in environ and 'RETURN_OBJ' not in environ:
        raise ValueError("RETURN_STR or RETURN_OBJ must be set.")
    if 'RETURN_STR' in environ and 'RETURN_OBJ' in environ:
        raise ValueError("RETURN_STR and RETURN_OBJ cannot be set at the same time.")
    is_return_obj = 'RETURN_OBJ' in environ

    # Get the object based on the context
    # For each context we then check if we need to return the object or the id
    # And by 'id' we mean the orcabus id or the business unique identifier

    # If the context is 'individual'
    if context == 'individual':
        # Get the individual object
        if is_from_orcabus:
            individual_obj = get_individual_from_individual_orcabus_id(value)
        else:
            individual_obj = get_individual_from_individual_id(value)

        # Return the individual object if RETURN_OBJ is set
        # Otherwise, return the orcabus id
        if is_return_obj:
            return individual_obj

        if is_from_orcabus:
            return {
                "individual_id": individual_obj['individualId']
            }
        else:
            return {
                "orcabus_id": individual_obj['orcabusId']
            }

    # If the context is 'subject'
    if context == 'subject':
        # Get the subject object
        if is_from_orcabus:
            subject_obj = get_subject_from_subject_orcabus_id(value)
        else:
            subject_obj = get_subject_from_subject_id(value)

        # Return the subject object if RETURN_OBJ is set
        # Otherwise, return the orcabus id
        if is_return_obj:
            return subject_obj

        if is_from_orcabus:
            return {
                "subject_id": subject_obj['subjectId']
            }
        else:
            return {
                "orcabus_id": subject_obj['orcabusId']
            }

    # If the context is 'sample'
    if context == 'sample':

        # Get the sample object
        if is_from_orcabus:
            sample_obj = get_sample_from_sample_orcabus_id(value)
        else:
            sample_obj = get_sample_from_sample_id(value)

        # Return the sample object if RETURN_OBJ is set
        # Otherwise, return the orcabus id
        if is_return_obj:
            return sample_obj

        if is_from_orcabus:
            return {
                "sample_id": sample_obj['sampleId']
            }
        else:
            return {
                "orcabus_id": sample_obj['orcabusId']
            }

    # If the context is 'library'
    if context == 'library':
        if is_from_orcabus:
            library_obj = get_library_from_library_orcabus_id(value)
        else:
            library_obj = get_library_from_library_id(value)

        if is_return_obj:
            return library_obj

        if is_from_orcabus:
            return {
                "library_id": library_obj['libraryId']
            }
        else:
            return {
                "orcabus_id": library_obj['orcabusId']
            }

    # If the context is 'project'
    if context == 'project':
        if is_from_orcabus:
            project_obj = get_project_from_project_orcabus_id(value)
        else:
            project_obj = get_project_from_project_id(value)

        if is_return_obj:
            return project_obj

        if is_from_orcabus:
            return {
                "project_id": project_obj['projectId']
            }
        else:
            return {
                "orcabus_id": project_obj['orcabusId']
            }

    # If the context is 'project'
    if context == 'contact':
        if is_from_orcabus:
            contact_obj = get_contact_from_contact_orcabus_id(value)
        else:
            contact_obj = get_contact_from_contact_id(value)

        if is_return_obj:
            return contact_obj

        if is_from_orcabus:
            return {
                "contact_id": contact_obj['contactId']
            }
        else:
            return {
                "orcabus_id": contact_obj['orcabusId']
            }


# if __name__ == "__main__":
#     import json
#
#     # Set the aws variables
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#
#     # Set the context variables
#     environ['CONTEXT'] = 'individual'
#     environ['FROM_ORCABUS'] = ''
#     environ['RETURN_STR'] = ''
#
#     # print(
#     #     json.dumps(
#     #         handler(
#     #             {
#     #                 "value": "idv.01J8EV7AVRB43911YD4WKZNCHK"
#     #             },
#     #             None
#     #         ),
#     #         indent=4
#     #     )
#     # )
#     #
#     # # {
#     # #     "individual_id": "SBJ05695"
#     # # }

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
#     # Set the context variables
#     environ['CONTEXT'] = 'subject'
#     environ['FROM_ID'] = ''
#     environ['RETURN_OBJ'] = ''
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "value": "VENTURE-24004301"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "orcabusId": "sbj.01J8ES921MV8VCY71SJPAS7D24",
#     #     "individualSet": [
#     #         {
#     #             "orcabusId": "idv.01J8ES90SEHD03JY5R0DR8K44H",
#     #             "individualId": null,
#     #             "source": "lab"
#     #         },
#     #         {
#     #             "orcabusId": "idv.01J8EV7ARC2ZF9X0FA243CSXA5",
#     #             "individualId": "SBJ05693",
#     #             "source": "lab"
#     #         }
#     #     ],
#     #     "librarySet": [
#     #         {
#     #             "orcabusId": "lib.01J8ES922VZT5S55T9HXPRZXC7",
#     #             "libraryId": "L2401462",
#     #             "phenotype": "normal",
#     #             "workflow": "qc",
#     #             "quality": "good",
#     #             "type": "WGS",
#     #             "assay": "TsqNano",
#     #             "coverage": 30.0,
#     #             "sample": "smp.01J8ES922C8KDSG3TWT8AEFCPZ",
#     #             "subject": "sbj.01J8ES921MV8VCY71SJPAS7D24"
#     #         }
#     #     ],
#     #     "subjectId": "VENTURE-24004301"
#     # }


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
#     # Set the context variables
#     environ['CONTEXT'] = 'sample'
#     environ['FROM_ID'] = ''
#     environ['RETURN_OBJ'] = ''
#
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "value": "PTC_TSqN240923"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "orcabusId": "smp.01J8ES92CBMCVE09FJSPADGYG1",
#     #     "sampleId": "PTC_TSqN240923",
#     #     "externalSampleId": "NA24385",
#     #     "source": "cell-line"
#     # }


# if __name__ == "__main__":
#     # Set the environment variables
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#
#     print(
#         handler(
#             {
#                 "subject_id": "VENTURE-24004301"
#             },
#             None
#         )
#     )


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
#     # Set the context variables
#     environ['CONTEXT'] = 'library'
#     environ['FROM_ORCABUS'] = ''
#     environ['RETURN_STR'] = ''
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "value": "lib.01J8ES92FTH314XSPZDWBA91E2"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "library_id": "L2401469"
#     # }


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
#     # Set the context variables
#     environ['CONTEXT'] = 'project'
#     environ['FROM_ORCABUS'] = ''
#     environ['RETURN_STR'] = ''
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "value": "prj.01J8ES70B12PTV40XAYF0GPW3C"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "project_id": "SEQC"
#     # }


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
#     # Set the context variables
#     environ['CONTEXT'] = 'contact'
#     environ['FROM_ORCABUS'] = ''
#     environ['RETURN_STR'] = ''
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "value": "ctc.01J8ES70ANRQQ4K71HQ9PZAEM6"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "contact_id": "Hofmann"
#     # }
