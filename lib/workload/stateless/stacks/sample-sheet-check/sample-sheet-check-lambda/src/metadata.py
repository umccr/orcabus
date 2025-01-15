import os
import urllib.request
from typing import List
import json

# Grab api constant from environment variable
METADATA_DOMAIN_NAME = os.environ.get("METADATA_DOMAIN_NAME", "metadata.dev.umccr.org")
METADATA_API_PATH = 'api/v1/library'


def get_metadata_record_from_array_of_field_name(auth_header: str, field_name: str,
                                                 value_list: List[str]):
    # Define header request
    headers = {
        'Authorization': auth_header
    }

    # Removing any duplicates for api efficiency
    value_list = list(set(value_list))

    # Result variable
    query_result = []

    max_number_of_library_per_api_call = 300
    for i in range(0, len(value_list), max_number_of_library_per_api_call):

        # Define start and stop element from the list
        start_index = i
        end_index = start_index + max_number_of_library_per_api_call

        array_to_process = value_list[start_index:end_index]

        # Define query string
        query_param_string = f'&{field_name}='.join(array_to_process)
        query_param_string = f'?{field_name}=' + query_param_string  # Appending name at the beginning

        query_param_string = query_param_string + f'&rowsPerPage=1000'  # Add Rows per page (1000 is the maximum rows)

        url = f"https://{METADATA_DOMAIN_NAME.strip('.')}/{METADATA_API_PATH.strip('/')}/{query_param_string}"
        # Make sure no data is left, looping data until the end
        while url is not None:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                if response.status < 200 or response.status >= 300:
                    raise ValueError(f'Non 20X status code returned')

                response_json = json.loads(response.read().decode())
                query_result.extend(response_json["results"])
                url = response_json["links"]["next"]
    return query_result
