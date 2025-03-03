from django.db import transaction
from django.utils import timezone
import logging

from sequence_run_manager.models.sequence import Sequence, LibraryAssociation
from sequence_run_manager_proc.services.bssh_srv import BSSHService
from sequence_run_manager.fields import sanitize_orcabus_id

logger = logging.getLogger(__name__)

ASSOCIATION_STATUS = "ACTIVE"


def check_or_create_sequence_run_libraries_linking(payload: dict):
    """
    Check if libraries are linked to the sequence run;
    if not, create the linking
    """
    sequence_run = Sequence.objects.get(sequence_run_id=payload["id"])
    if not sequence_run:
        logger.error(f"Sequence run {payload['id']} not found when checking or creating sequence run libraries linking")
        raise ValueError(f"Sequence run {payload['id']} not found")
    
    # if libraries are already linked, skip
    if LibraryAssociation.objects.filter(sequence=sequence_run).exists():
        return
    
    bssh_srv = BSSHService()
    run_details = bssh_srv.get_run_details(payload["apiUrl"])
    return create_sequence_run_libraries_linking(sequence_run, run_details)


@transaction.atomic
def create_sequence_run_libraries_linking(sequence_run: Sequence, run_details: dict):
    """
    Create sequence run libraries linking
    """
    linked_libraries = BSSHService.get_libraries_from_run_details(run_details)
    
    if linked_libraries:
        for library_id in linked_libraries:
                # create the library association
                LibraryAssociation.objects.create(
                    sequence=sequence_run,
                    library_id=library_id,
                    association_date=timezone.now(),  # Use timezone-aware datetime
                    status=ASSOCIATION_STATUS,
                )
        logger.info(f"Library associations created for sequence run {sequence_run.sequence_run_id}, linked libraries: {linked_libraries}")


# metadata manager service
# TODO ( thinking about if this is necessary): 
#   1. check if the library is exist/active in the metadata manager
#   2. get the library details (library id) from the metadata manager
#   3. create the library record in the database

# def get_libraries_from_metadata_manager(auth_header: str, library_id_array: list[str]):
#     """
#     Get libraries from metadata manager:
#     return a list of dicts with the following keys:
#     [
#         {
#         "orcabusId": "string",
#         "projectSet": [
#             ...
#         ],
#         "sample": {
#             ...
#         },
#         "subject": {
#             ...
#         },
#         "libraryId": "string",
#         "phenotype": "normal",
#         "workflow": "clinical",
#         "quality": "very-poor",
#         "type": "10X",
#         "assay": "string",
#         "coverage": 0,
#         "overrideCycles": "string"
#         }
#     ]
#     """
#     try:
#         metadata_response = get_metadata_record_from_array_of_field_name(auth_header=auth_header,
#                                                                          field_name='library_id',
#                                                                          value_list=library_id_array)
#     except Exception as e:
#         raise Exception("Fail to fetch metadata api for library id in the sample sheet")
    
#     return metadata_response


# def get_metadata_record_from_array_of_field_name(auth_header: str, field_name: str,
#                                                  value_list: List[str]):
#     """
#     Get metadata record from array of field name
#     """
#     METADATA_DOMAIN_NAME = os.environ.get("METADATA_DOMAIN_NAME", "metadata.dev.umccr.org")
#     METADATA_API_PATH = 'api/v1/library'
#     # Define header request
#     headers = {
#         'Authorization': auth_header
#     }

#     # Removing any duplicates for api efficiency
#     value_list = list(set(value_list))

#     # Result variable
#     query_result = []

#     max_number_of_library_per_api_call = 300
#     for i in range(0, len(value_list), max_number_of_library_per_api_call):

#         # Define start and stop element from the list
#         start_index = i
#         end_index = start_index + max_number_of_library_per_api_call

#         array_to_process = value_list[start_index:end_index]

#         # Define query string
#         query_param_string = f'&{field_name}='.join(array_to_process)
#         query_param_string = f'?{field_name}=' + query_param_string  # Appending name at the beginning

#         query_param_string = query_param_string + f'&rowsPerPage=1000'  # Add Rows per page (1000 is the maximum rows)

#         url = f"https://{METADATA_DOMAIN_NAME.strip('.')}/{METADATA_API_PATH.strip('/')}/{query_param_string}"
#         # Make sure no data is left, looping data until the end
#         while url is not None:
#             req = urllib.request.Request(url, headers=headers)
#             with urllib.request.urlopen(req) as response:
#                 if response.status < 200 or response.status >= 300:
#                     raise ValueError(f'Non 20X status code returned')

#                 response_json = json.loads(response.read().decode())
#                 query_result.extend(response_json["results"])
#                 url = response_json["links"]["next"]
#     return query_result
