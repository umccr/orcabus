#!/usr/bin/env python3

"""
ICAv2 file utils
"""
import re
from pathlib import Path
from typing import List, Optional, Union
from urllib.parse import urlunparse

import libica
import requests
from libica.openapi.v2 import ApiClient, ApiException
from libica.openapi.v2.api.project_data_api import ProjectDataApi
from libica.openapi.v2.api.project_data_copy_batch_api import ProjectDataCopyBatchApi
from libica.openapi.v2.model.create_data import CreateData
from libica.openapi.v2.model.create_project_data_copy_batch import CreateProjectDataCopyBatch
from libica.openapi.v2.model.create_project_data_copy_batch_item import CreateProjectDataCopyBatchItem
from libica.openapi.v2.model.download import Download
from libica.openapi.v2.model.job import Job
from libica.openapi.v2.model.project_data import ProjectData
from libica.openapi.v2.model.project_data_copy_batch import ProjectDataCopyBatch

from .globals import LIBICAV2_DEFAULT_PAGE_SIZE
from .icav2_configuration_helper import get_icav2_configuration
from .logger import get_logger

logger = get_logger()


def get_uri_from_project_id_and_path(project_id: str, data_path: Union[str | Path]) -> str:
    """
    Use the urlunparse function to return the data path as a uri
    :return:
    """
    return str(urlunparse(("icav2", project_id, str(data_path), None, None, None)))


def project_data_as_uri(file_obj: ProjectData) -> str:
    """
    Return the file object as an icav2:// uri
    :param file_obj:
    :return:
    """
    return str(
        urlunparse((
            "icav2",
            file_obj.project_id,
            file_obj.data.details.path,
            None, None, None
        ))
    )


def get_data_object_from_id(project_id: str, data_id: str) -> ProjectData:
    # Get configuration
    configuration = get_icav2_configuration()

    # Enter a context with an instance of the API client
    with ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = ProjectDataApi(api_client)

    try:
        project_data_obj: ProjectData = api_instance.get_project_data(
            project_id=project_id,
            data_id=data_id
        )
    except ApiException as e:
        logger.error("Exception when calling ProjectDataApi->get_project_data: %s\n" % e)
        raise ApiException

    return project_data_obj


def create_folder_in_project(project_id: str, parent_folder_path: Path, folder_name: str) -> ProjectData:
    """
    Create a folder in a project
    """

    # Get the configuration
    configuration = get_icav2_configuration()

    # Enter a context with an instance of the API client
    with ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = ProjectDataApi(api_client)

    parent_folder_path = str(parent_folder_path.absolute()) + "/"
    if parent_folder_path == "//":
        parent_folder_path = "/"

    # example passing only required values which don't have defaults set
    try:
        # Create a project data.
        api_response: ProjectData = api_instance.create_data_in_project(
            project_id=project_id,
            create_data=CreateData(
                name=folder_name,
                folder_path=parent_folder_path,
                data_type="FOLDER",
            )
        )
    except ApiException as e:
        logger.error("Exception when calling ProjectDataApi->create_project_data: %s\n" % e)
        raise ApiException

    # Return the folder id
    return api_response


def get_folder_id_from_project_data_path(
        project_id: str,
        folder_path: Path,
        create_folder_if_not_found: bool = False
) -> str:
    """
    Need to take the parent of the path and list all folders non-recursively,
    match on the folder name and then return the folder id
    """

    # Get the configuration
    configuration = get_icav2_configuration()

    # Enter a context with an instance of the API client
    with ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = ProjectDataApi(api_client)

    parent_folder_path = str(folder_path.parent.absolute()) + "/"
    # Exception for when folder is in the top directory
    if parent_folder_path == '//':
        parent_folder_path = '/'

    # Add the folder name to the list of folder names to search on
    folder_name = [
        folder_path.name
    ]

    # example passing only required values which don't have defaults set
    try:
        # Retrieve the list of project data.
        data_items: List[ProjectData] = api_instance.get_project_data_list(
            project_id=project_id,
            parent_folder_path=parent_folder_path,
            filename=folder_name,
            filename_match_mode="EXACT",
            file_path_match_mode="FULL_CASE_INSENSITIVE",
            type="FOLDER"
        ).items
    except libica.openapi.v2.ApiException as e:
        logger.error("Exception when calling ProjectDataApi->get_project_data_list: %s\n" % e)
        raise ApiException

    # Get the folder id
    try:
        folder_id: ProjectData = next(
             filter(
                lambda data_iter: data_iter.data.details.path == str(folder_path) + "/",
                data_items
             )
        )
    except StopIteration:
        if create_folder_if_not_found:
            # Create the folder
            folder_id = create_folder_in_project(project_id=project_id, parent_folder_path=folder_path.parent, folder_name=folder_path.name)
        else:
            logger.error("Could not find folder id for folder: %s\n" % folder_path)
            raise StopIteration

    return folder_id.data.id


def get_icav2_file_contents(project_id: str, file_id: str) -> str:
    """
    Return the contents of a file
    """

    # Get the configuration
    configuration = get_icav2_configuration()

    # Enter a context with an instance of the API client
    with ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = ProjectDataApi(api_client)

    # example passing only required values which don't have defaults set
    try:
        # Retrieve a project data.
        api_response: Download = api_instance.create_download_url_for_data(project_id, file_id)
    except ApiException as e:
        logger.error("Got an exception retrieving project data download url: %s\n" % e)
        raise ApiException

    # Collect the url attribute
    url = api_response.url

    # Get the file contents
    response = requests.get(url)

    return response.text


def get_file_id_from_path(project_id: str, file_path: Path) -> str:
    """
    Need to take the parent of the path and list all files non-recursively,
    match on the file name and then return the file id
    """

    # Get the configuration
    configuration = get_icav2_configuration()

    # Enter a context with an instance of the API client
    with ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = ProjectDataApi(api_client)

    parent_folder_path = str(file_path.parent.absolute()) + "/"
    # Exception for when file is in the top directory
    if parent_folder_path == '//':
        parent_folder_path = '/'

    # Add the filename to the list of filenames to search on
    filename = [
        file_path.name
    ]

    # example passing only required values which don't have defaults set
    try:
        # Retrieve the list of project data.
        data_items: List[ProjectData] = api_instance.get_project_data_list(
            project_id=project_id,
            parent_folder_path=parent_folder_path,
            filename=filename,
            filename_match_mode="EXACT",
            file_path_match_mode="FULL_CASE_INSENSITIVE",
            type="FILE"
        ).items
    except libica.openapi.v2.ApiException as e:
        logger.error("Exception when calling ProjectDataApi->get_project_data_list: %s\n" % e)
        raise ApiException

    # Get the file id
    try:
        file_id = next(
             filter(
                lambda data_iter: data_iter.data.details.path == str(file_path),
                data_items
             )
        )
    except StopIteration:
        logger.error("Could not find file id for file: %s\n" % file_path)
        raise StopIteration

    return file_id.data.id


def project_data_copy_batch_handler(
        source_data_ids: List[str],
        destination_project_id: str,
        destination_folder_path: Path
) -> Job:
    """
    Copy a batch of files from one project to another
    """

    # Get the configuration
    configuration = get_icav2_configuration()

    # Enter a context with an instance of the API client
    with ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = ProjectDataCopyBatchApi(api_client)

    # example passing only required values which don't have defaults set
    try:
        # Copy a batch of project data.
        api_response: ProjectDataCopyBatch = api_instance.create_project_data_copy_batch(
            project_id=destination_project_id,
            create_project_data_copy_batch=CreateProjectDataCopyBatch(
                items=list(
                    map(
                        lambda source_data_id_iter: CreateProjectDataCopyBatchItem(
                            data_id=source_data_id_iter
                        ),
                        source_data_ids
                    )
                ),
                destination_folder_id=get_folder_id_from_project_data_path(
                    project_id=destination_project_id,
                    folder_path=destination_folder_path,
                    create_folder_if_not_found=True
                ),
                copy_user_tags=True,
                copy_technical_tags=True,
                copy_instrument_info=True,
                action_on_exist="SKIP"
            )
        )
    except ApiException as e:
        logger.error("Exception when calling ProjectDataApi->copy_project_data_batch: %s\n" % e)
        raise ApiException

    # Return the job ID for the project data copy batch
    return api_response.job


def list_data_non_recursively(
        project_id: str,
        parent_folder_id: Optional[str] = None,
        parent_folder_path: Optional[str] = None,
        sort: Optional[str] = ""
) -> List[ProjectData]:
    """
    List data non recursively
    :return:
    """
    # Check one of parent_folder_id and parent_folder_path is specified
    if parent_folder_id is None and parent_folder_path is None:
        logger.error("Must specify one of parent_folder_id and parent_folder_path")
        raise AssertionError
    elif parent_folder_id is not None and parent_folder_path is not None:
        logger.error("Must specify only one of parent_folder_id and parent_folder_path")
        raise AssertionError

    # Specify either parent_folder_id or parent_folder_path as a list
    parent_folder_ids = [parent_folder_id] if parent_folder_id is not None else []

    # Collect api instance
    with ApiClient(get_icav2_configuration()) as api_client:
        api_instance = ProjectDataApi(api_client)

    # Set other parameters
    page_size = LIBICAV2_DEFAULT_PAGE_SIZE
    page_offset = 0

    # Initialise data ids - we may need to extend the items multiple times
    data_ids: List[ProjectData] = []

    while True:
        # Attempt to collect all data ids
        try:
            if parent_folder_id is not None:
                # Retrieve the list of project data
                api_response = api_instance.get_project_data_list(
                    project_id=project_id,
                    parent_folder_id=parent_folder_ids,
                    page_size=str(page_size),
                    page_offset=str(page_offset),
                    sort=sort
                )
            else:
                # Retrieve the list of project data
                api_response = api_instance.get_project_data_list(
                    project_id=project_id,
                    parent_folder_path=parent_folder_path,
                    page_size=str(page_size),
                    page_offset=str(page_offset),
                    sort=sort
                )
        except ApiException as e:
            raise ValueError("Exception when calling ProjectDataApi->get_project_data_list: %s\n" % e)

        # Extend items list
        data_ids.extend(api_response.items)

        # Check page offset and page size against total item count
        if page_offset + page_size > api_response.total_item_count:
            break
        page_offset += page_size

    return data_ids


def find_data_recursively(project_id: str,
                          parent_folder_id: Optional[str] = None, parent_folder_path: Optional[str] = None,
                          name: Optional[str] = "", data_type: Optional[str] = None,
                          mindepth: Optional[int] = None, maxdepth: Optional[int] = None) -> List[ProjectData]:
    """
    Run a find on a data name
    :return:
    """
    # Matched data items thing we return
    matched_data_items: List[ProjectData] = []

    # Get top level items
    if parent_folder_id is None and parent_folder_path is None:
        logger.error("Must specify one of parent_folder_id or parent_folder_path")
        raise AssertionError
    elif parent_folder_id is not None:
        data_items: List[ProjectData] = list_data_non_recursively(project_id, parent_folder_id=parent_folder_id)
    elif parent_folder_path is not None:
        data_items: List[ProjectData] = list_data_non_recursively(project_id, parent_folder_path=parent_folder_path)

    # Check if we can pull out any items in the top directory
    if mindepth is None or mindepth <= 1:
        name_regex_obj = re.compile(name)
        for data_item in data_items:
            data_item_match = name_regex_obj.match(data_item.data.details.name)
            if data_type is not None and not data_item.data.details.data_type == data_type:
                continue
            if data_item_match is not None:
                matched_data_items.append(data_item)

    # Otherwise look recursively
    if maxdepth is None or not maxdepth <= 1:
        # Listing subfolders
        subfolders = list(
            filter(
                lambda x: x.data.details.data_type == "FOLDER",
                data_items
            )
        )
        for subfolder in subfolders:
            matched_data_items.extend(
                find_data_recursively(
                    project_id=project_id,
                    parent_folder_id=subfolder.data.id,
                    parent_folder_path=subfolder.data.details.path,
                    name=name,
                    data_type=data_type,
                    mindepth=mindepth-1 if mindepth is not None else None,
                    maxdepth=maxdepth-1 if maxdepth is not None else None
                )
            )

    return matched_data_items


def get_folder_path_from_folder_id(project_id: str, data_id: str):
    """
    Given a project id, and data_id return the folder path
    :param project_id:
    :param data_id:
    :return:
    """

    configuration = get_icav2_configuration()

    # Enter a context with an instance of the API client
    with ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = ProjectDataApi(api_client)

    # example passing only required values which don't have defaults set
    try:
        # Retrieve the list of project data.
        data_obj: ProjectData = api_instance.get_project_data(
            project_id=project_id,
            data_id=data_id
        )
    except libica.openapi.v2.ApiException as e:
        logger.error("Exception when calling ProjectDataApi->get_project_data_list: %s\n" % e)
        raise ApiException

    return data_obj.data.details.path


def find_data_recursively_bulk(
        project_id: str,
        parent_folder_id: Optional[str] = None,
        parent_folder_path: Optional[Path] = None,
        data_type: Optional[str] = None
) -> List[ProjectData]:
    """
    Runs a bulk find - because we're not sorting, we can use cursor based pagination
    :param project_id:
    :param parent_folder_path:
    :param data_type:
    :return:
    """

    if parent_folder_id is None and parent_folder_path is None:
        logger.error("Please specify one of parent_folder_id and parent_folder_path")

    # Get the parent folder path as a string
    if parent_folder_path is None:
        parent_folder_path = str(Path(get_folder_path_from_folder_id(project_id, parent_folder_id))) + "/"
    else:
        parent_folder_path = str(parent_folder_path.absolute()) + "/"

    # Initialise
    data_ids: List[ProjectData] = []
    # Collect api instance
    with ApiClient(get_icav2_configuration()) as api_client:
        api_instance = ProjectDataApi(api_client)

    # Set other parameters
    page_size = LIBICAV2_DEFAULT_PAGE_SIZE
    page_token = ""

    # Iterate over all pages
    while True:
        # Attempt to collect all data ids
        try:
            # Retrieve the list of project data
            api_response = api_instance.get_project_data_list(
                project_id=project_id,
                file_path=[parent_folder_path],
                file_path_match_mode="STARTS_WITH_CASE_INSENSITIVE",
                page_size=str(page_size),
                page_token=page_token,
                type=data_type
            )

        except ApiException as e:
            logger.error("Exception when calling ProjectDataApi->get_project_data_list: %s\n" % e)
            raise ApiException

        # Extend items list
        data_ids.extend(api_response.items)

        # Check page offset and page size against total item count
        page_token = api_response.next_page_token

        if page_token == "":
            break

    return data_ids


# Check file exists
def get_project_data(project_id: str, data_path: Path) -> ProjectData:
    """
    Get a project data object - useful for making sure if we want to upload a file that we delete the original?
    :param project_id:
    :param data_path:
    :return:
    """
    data_list = find_data_recursively(
        project_id=project_id,
        parent_folder_path=str(data_path.parent) + "/" if not data_path.parent == Path("/") else "/",
        name=data_path.name,
        maxdepth=1
    )

    if not len(data_list) == 1:
        logger.error(f"Could not find project data in project {project_id} with path {data_path}")
        raise FileNotFoundError

    return data_list[0]


def delete_project_data(project_id: str, data_id: str):
    """
    # FIXME - yet to try this, ended to using another solution for now that meant that this function
    # was not required
    Delete data id, this is useful if we need to overwrite data
    :param project_id:
    :param data_id:
    :return:
    """
    # Get the configuration
    icav2_configuration = get_icav2_configuration()

    # Enter a context with an instance of the API client
    with ApiClient(icav2_configuration) as api_client:
        # Create an instance of the API class
        api_instance = ProjectDataApi(api_client)

    # example passing only required values which don't have defaults set
    try:
        # Schedule this data for deletion.
        api_instance.delete_data(project_id, data_id)
    except ApiException as e:
        logger.error("Exception when calling ProjectDataApi->delete_data: %s\n" % e)
        raise ApiException


def upload_file_to_icav2(local_file_path: Path, project_id: str, data_path: Path):
    """
    # FIXME - yet to try this, ended to using another solution for now that meant that this function
    # was not required
    :param local_file_path:
    :param project_id:
    :param data_path:
    :return:
    """
    # Check the local file exists
    if not local_file_path.is_file():
        logger.error("Local file path does not exist: %s" % local_file_path)
        raise FileNotFoundError

    # Check if data exists and delete if so
    try:
        # Check if the project data exists already
        project_data: ProjectData = get_project_data(project_id, data_path)
    except FileNotFoundError:
        pass
    else:
        # Delete the existing project data
        delete_project_data(project_id, project_data.data.id)

    # Make a new file
    with libica.openapi.v2.ApiClient(get_icav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = ProjectDataApi(api_client)

    # Create data
    create_data = CreateData(
        name=data_path.name,
        folder_path=str(data_path.parent) + "/" if not data_path.parent == Path("/") else "/",
        data_type="FILE"
    )

    # Create the data object
    try:
        # Create data in this project.
        project_data_obj: ProjectData = api_instance.create_data_in_project(project_id, create_data)
    except ApiException as e:
        logger.error("Exception when calling ProjectDataApi->create_data_in_project: %s\n" % e)
        raise ApiException

    # example passing only required values which don't have defaults set
    try:
        # Retrieve an upload URL for this data.
        upload_url_response = api_instance.create_upload_url_for_data(
            project_id,
            project_data_obj.data.id,
            file_type="FILE"
        )
    except ApiException as e:
        logger.error("Exception when calling ProjectDataApi->create_upload_url_for_data: %s\n" % e)
        raise ApiException

    # Use the requests library to upload to the url
    upload_url = upload_url_response.url

    with open(local_file_path, "rb") as file_h:
        response = requests.put(upload_url, data=file_h)
