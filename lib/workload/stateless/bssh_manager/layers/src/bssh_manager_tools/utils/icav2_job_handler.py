#!/usr/bin/env python3

"""
Retrieve a job and get its status
"""
from libica.openapi.v2 import ApiClient, ApiException
from libica.openapi.v2.api.job_api import JobApi
from libica.openapi.v2.model.job import Job

from bssh_manager_tools.utils.icav2_configuration_helper import get_icav2_configuration


def get_job(job_id: str) -> Job:
    configuration = get_icav2_configuration()

    with ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = JobApi(api_client)

    # example passing only required values which don't have defaults set
    try:
        # Retrieve a job.
        api_response: Job = api_instance.get_job(job_id)
    except ApiException as e:
        raise ApiException("Exception when calling JobApi->get_job: %s\n" % e)

    return api_response





