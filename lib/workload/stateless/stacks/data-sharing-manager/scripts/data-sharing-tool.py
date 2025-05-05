#!/usr/bin/env python3

"""
data-sharing-tool ::: Data sharing packager

Usage:
    data-sharing-tool <command> [<args>...]

Command:
    help                    Print this help message and exit
    generate-package        Generate a package
    list-packages           List package jobs
    get-package-status      Get Package Status
    view-package-report     View the package report
    push-package            Push a package to a destination
    presign-package         Presign a package
    list-push-jobs          List push jobs
    get-push-job-status     Get status of a push job
"""

# Imports
import json
import sys
from os import environ
from pathlib import Path
from textwrap import dedent

from time import sleep
from docopt import docopt
import requests
import pandas as pd
import pandera as pa
from pandera.typing import DataFrame
from typing import Optional, List, Dict, TypedDict
import typing
import boto3
from requests import HTTPError
from subprocess import call

if typing.TYPE_CHECKING:
    from mypy_boto3_ssm import SSMClient
    from mypy_boto3_secretsmanager import SecretsManagerClient

# Global
DATA_SHARING_PREFIX = 'data-sharing'
AWS_HOSTNAME_SSM_PATH = '/hosted_zone/umccr/name'
AWS_ORCABUS_TOKEN_SECRET_ID = 'orcabus/token-service-jwt'
AWS_PRODUCTION_ACCOUNT_ID = '472057503814'

# Models
class PackageRequestResponseDict(TypedDict):
    id: str
    packageName: str
    stepsExecutionArn: str
    status: str
    requestTime: str
    completionTime: Optional[str]
    hasExpired: bool


class PackageRequestDict(TypedDict):
    libraryIdList: List[str]
    dataTypeList: List[str]
    portalRunIdList: Optional[List[str]]


class PushJobRequestResponseDict(TypedDict):
    id: str
    stepFunctionsExecutionArn: str
    status: str
    startTime: str
    packageId: str
    shareDestination: str
    logUri: str
    endTime: Optional[str]
    errorMessage: Optional[str]

# Dataframe models
class LimsManifestDataFrame(pa.DataFrameModel):
    sequencing_run_id: str = pa.Field(nullable=True)
    sequencing_run_date: str = pa.Field(nullable=True)
    library_id: str = pa.Field(nullable=True)
    internal_subject_id: str = pa.Field(nullable=True)
    external_subject_id: str = pa.Field(nullable=True)
    sample_id: str = pa.Field(nullable=True)
    external_sample_id: str = pa.Field(nullable=True)
    experiment_id: str = pa.Field(nullable=True)
    project_id: str = pa.Field(nullable=True)
    owner_id: str = pa.Field(nullable=True)
    workflow: str = pa.Field(nullable=True)
    phenotype: str = pa.Field(nullable=True)
    type: str = pa.Field(nullable=True)
    assay: str = pa.Field(nullable=True)
    quality: str = pa.Field(nullable=True)
    source: str = pa.Field(nullable=True)
    truseq_index: str = pa.Field(nullable=True)
    load_datetime: str = pa.Field(nullable=True)
    partition_schema_name: str = pa.Field(nullable=True)
    partition_name: str = pa.Field(nullable=True)


class WorkflowManifestDataFrame(pa.DataFrameModel):
    portal_run_id: str = pa.Field(nullable=True)
    library_id: str = pa.Field(nullable=True)
    workflow_name: str = pa.Field(nullable=True)
    workflow_version: str = pa.Field(nullable=True)
    workflow_status: str = pa.Field(nullable=True)
    workflow_start: str = pa.Field(nullable=True)
    workflow_end: str = pa.Field(nullable=True)
    workflow_duration: int = pa.Field(coerce=True, nullable=True)
    workflow_comment: str = pa.Field(nullable=True)
    partition_schema_name: str = pa.Field(nullable=True)
    partition_name: str = pa.Field(nullable=True)


# AWS functions
def get_hostname() -> str:
    ssm_client: SSMClient = boto3.client('ssm')
    return ssm_client.get_parameter(
        Name=AWS_HOSTNAME_SSM_PATH
    )['Parameter']['Value']


def get_orcabus_token() -> str:
    secrets_manager_client: SecretsManagerClient = boto3.client('secretsmanager')
    return json.loads(
        secrets_manager_client.get_secret_value(
            SecretId=AWS_ORCABUS_TOKEN_SECRET_ID
        )['SecretString']
    )['id_token']


# Request functions
def get_base_api() -> str:
    return f"https://{DATA_SHARING_PREFIX}.{get_hostname()}"


def get_default_get_headers() -> Dict:
    return {
        "Accept": "application/json",
        "Authorization": f"Bearer {get_orcabus_token()}",
    }


def get_default_post_headers() -> Dict:
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {get_orcabus_token()}",
    }


def create_package(
        package_name: str,
        package_request: PackageRequestDict
) -> str:
    """
    Create a package request
    :param package_name:
    :param package_request:
    :return:
    """
    response = requests.post(
        headers=get_default_post_headers(),
        json={
            "packageName": package_name,
            "packageRequest": package_request,
        },
        url=f"{get_base_api()}/api/v1/package",
    )

    try:
        response.raise_for_status()
    except HTTPError as e:
        raise HTTPError(f"Got an error, response was {response.text}") from e

    return response.json()['id']


def list_packages(package_name: Optional[str]) -> List[PackageRequestResponseDict]:
    response = requests.get(
        headers=get_default_get_headers(),
        params=dict(filter(
            lambda kv: kv[1] is not None,
            {
                "packageName": package_name,
                "rowsPerPage": 1000
            }.items()
        )),
        url=f"{get_base_api()}/api/v1/package",
    )

    try:
        response.raise_for_status()
    except HTTPError as e:
        raise HTTPError(f"Got an error, response was {response.text}") from e

    return list(filter(
        lambda package_obj_iter_: package_obj_iter_['packageName'] == package_name,
        response.json()['results']
    ))


def list_push_jobs(package_id: Optional[str]) -> List[PushJobRequestResponseDict]:
    response = requests.get(
        headers=get_default_get_headers(),
        params=dict(filter(
            lambda kv: kv[1] is not None,
            {
                "packageId": package_id,
                "rowsPerPage": 1000
            }.items()
        )),
        url=f"{get_base_api()}/api/v1/push",
    )

    try:
        response.raise_for_status()
    except HTTPError as e:
        raise HTTPError(f"Got an error, response was {response.text}") from e

    return response.json()['results']


def get_package(package_id: str) -> PackageRequestResponseDict:
    response = requests.get(
        headers=get_default_get_headers(),
        url=f"{get_base_api()}/api/v1/package/{package_id}",
    )

    try:
        response.raise_for_status()
    except HTTPError as e:
        raise HTTPError(f"Got an error, response was {response.text}") from e

    return response.json()


def get_push_job(push_job_id: Optional[str]) -> PushJobRequestResponseDict:
    response = requests.get(
        headers=get_default_get_headers(),
        url=f"{get_base_api()}/api/v1/push/{push_job_id}",
    )

    try:
        response.raise_for_status()
    except HTTPError as e:
        raise HTTPError(f"Got an error, response was {response.text}") from e

    return response.json()


def get_package_report(package_id: str) -> str:
    response = requests.get(
        headers=get_default_get_headers(),
        url=f"{get_base_api()}/api/v1/package/{package_id}:getSummaryReport",
    )

    try:
        response.raise_for_status()
    except HTTPError as e:
        raise HTTPError(f"Got an error, response was {response.text}") from e

    return response.text


def push_package(package_id: str, location_uri: str) -> str:
    response = requests.post(
        headers=get_default_post_headers(),
        json={
            "shareDestination": location_uri,
        },
        url=f"{get_base_api()}/api/v1/package/{package_id}:push"
    )

    try:
        response.raise_for_status()
    except HTTPError as e:
        raise HTTPError(f"Got an error, response was {response.text}") from e

    return response.json()['id']


def presign_package(package_id: str) -> str:
    response = requests.get(
        headers=get_default_get_headers(),
        url=f"{get_base_api()}/api/v1/package/{package_id}:presign"
    )

    try:
        response.raise_for_status()
    except HTTPError as e:
        raise HTTPError(f"Got an error, response was {response.text}") from e

    return response.text


# Sub functions
def generate_package(
        package_name: str,
        lims_manifest: DataFrame[LimsManifestDataFrame],
        workflow_manifest: Optional[DataFrame[WorkflowManifestDataFrame]] = None,
        exclude_primary_data: bool = False,
        defrost_archived_fastqs: bool = False
) -> str:
    """
    Given a package name, the manifest for the LIMS and an optional workflow manifest,
    generate and launch a package request.
    :param defrost_archived_fastqs:
    :param exclude_primary_data:
    :param package_name:
    :param lims_manifest:
    :param workflow_manifest:
    :return:
    """

    # Get library ids from the lims manifest
    library_ids = lims_manifest['library_id'].unique().tolist()

    # Get the portal run ids from the workflow manifest
    if workflow_manifest is not None:
        portal_run_ids = workflow_manifest['portal_run_id'].unique().tolist()
    else:
        portal_run_ids = None

    # Create the package request payload
    package_request: PackageRequestDict = {
        "libraryIdList": library_ids,
        "dataTypeList": (
            (["FASTQ"] if exclude_primary_data else []) +
            (["SECONDARY_ANALYSIS"] if workflow_manifest is not None else [])
        ),
        "portalRunIdList": portal_run_ids,
        "defrostArchivedFastqs": True if defrost_archived_fastqs else False
    }

    return create_package(
        package_name=package_name,
        package_request=package_request,
    )


class Command:
    def __init__(self, command_argv):
        # Initialise any req vars
        self.cli_args = self._get_args(command_argv)

    def _get_args(self, command_argv):
        """
        Get the command line arguments
        :param command_argv:
        :return:
        """
        return docopt(
            dedent(self.__doc__),
            argv=command_argv,
            options_first=False
        )


class GeneratePackageSubCommand(Command):
    """
    Usage:
        data-sharing-tool generate-package help
        data-sharing-tool generate-package (--package-name=<package_name>)
                                           (--lims-manifest-csv=<lims_manifest_csv_path>)
                                           [--workflow-manifest-csv=<workflow_manifest_csv_path>]
                                           [--exclude-primary-data]
                                           [--defrost-archived-fastqs]
                                           [--wait]

    Description:
      Generate a package, use the athena mart tables to generate the lims and workflow manifest files,
      more help can be found in the README.md file

    Options:
      --package-name=<package_name>                          Name of the package
      --lims-manifest-csv=<lims_manifest_csv_path>           The LIMS manifest CSV file
      --workflow-manifest-csv=<workflow_manifest_csv_path>   The workflow manifest CSV file
      --exclude-primary-data                                 Exclude FASTQ files from the package
                                                             Only applicable if --workflow-manifest-csv is provided
      --defrost-archived-fastqs                              defrost archive fastqs if fastqs are in archive
      --wait                                                 Wait for the package to be created before exiting

    Environment variables:
      AWS_PROFILE       The AWS profile used by boto3

    Example:
        data-sharing-tool generate-package --package-name 'latest-fastqs' --lims-manifest-csv /path/to/manifest.csv
    """

    def __init__(self, command_argv):
        super().__init__(command_argv)

        # Import args
        self.package_name = self.cli_args['--package-name']
        self.lims_manifest = self.cli_args['--lims-manifest-csv']
        self.workflow_manifest = self.cli_args['--workflow-manifest-csv']
        self.exclude_primary_data = self.cli_args['--exclude-primary-data']
        self.defrost_archived_fastqs = self.cli_args['--defrost-archived-fastqs']
        self.wait = self.cli_args['--wait']

        # Check args
        if not Path(self.lims_manifest).is_file():
            raise FileNotFoundError(f"LIMS manifest file {self.lims_manifest} does not exist")
        if self.workflow_manifest is not None and not Path(self.workflow_manifest).is_file():
            raise FileNotFoundError(f"Workflow manifest file {self.workflow_manifest} does not exist")

        # Check package name doesn't have any spaces or special characters
        if not self.package_name.replace("-", "").replace("_", "").isalnum():
            raise ValueError(f"Package name {self.package_name} contains invalid characters. Only alphanumeric characters are allowed.")

        # Generate the package
        package_id = generate_package(
            package_name=self.package_name,
            lims_manifest=pd.read_csv(self.lims_manifest),
            workflow_manifest=pd.read_csv(self.workflow_manifest) if self.workflow_manifest else None,
            exclude_primary_data=self.exclude_primary_data,
            defrost_archived_fastqs=self.defrost_archived_fastqs
        )

        if self.wait:
            print(f"Starting packaging with id '{package_id}'")
            while True:
                package_status = get_package(package_id)['status']
                if package_status == "SUCCEEDED":
                    print(f"Generated package: {json.dumps(package_id, indent=4)}")
                    break
                if package_status == "FAILED":
                    print(f"Package generation failed, see sfn logs '{get_package(package_id)['stepsExecutionArn']}' for more information")
                    break
                if get_package(package_id)['status'] == "RUNNING":
                    sleep(10)

        else:
            print(f"Generating package: {json.dumps(package_id, indent=4)}")


class ListPackagesSubCommand(Command):
    """
    Usage:
        data-sharing-tool list-packages help
        data-sharing-tool list-packages [--package-name=<package_name>]

    Description:
      List packages, you may specify the package name to filter by, this will match the
      --package-name parameter used in the generate-package command

    Options:
      --package-name=<package_name>  The package name to filter by

    Environment variables:
      AWS_PROFILE       The AWS profile used by boto3

    Example:
        data-sharing-tool list-packages --package-name 'latest-fastqs'
    """


    def __init__(self, command_argv):
        super().__init__(command_argv)
        # Import args
        self.package_name = self.cli_args['--package-name']

        # Generate the package
        print(json.dumps(
            list_packages(package_name=self.package_name),
            indent=4
        ))


class GetPackageStatusSubCommand(Command):
    """
    Usage:
        data-sharing-tool get-package-status help
        data-sharing-tool get-package-status (--package-id=<package_id>)

    Description:
      Get the status of a package

    Options:
      --package-id=<package_id>          The package id to get the status of

    Environment variables:
      AWS_PROFILE       The AWS profile used by boto3

    Example:
        data-sharing-tool get-package-status --package-id 'pkg.12345678910'
    """

    def __init__(self, command_argv):
        super().__init__(command_argv)
        # Import args
        self.package_id = self.cli_args['--package-id']

        # Generate the package
        print(json.dumps(
            get_package(package_id=self.package_id),
            indent=4
        ))


class ViewPackageReportSubCommand(Command):
    """
    Usage:
        data-sharing-tool view-package-report help
        data-sharing-tool view-package-report (--package-id=<package_id>)

    Description:
      View a package RMarkdown report.
      One can set the BROWSER environment variable (to say 'firefox') to open the report in a browser.

    Options:
      --package-id=<package_id>               View the package RMarkdown report

    Environment variables:
      AWS_PROFILE       The AWS profile used by boto3
      BROWSER           Can be used by xdg-utils to automatically open the presigned url directly into a browser

    Example:
        data-sharing-tool view-package-report --package-id 'pkg.12345678910'
    """

    def __init__(self, command_argv):
        super().__init__(command_argv)
        # Import args
        self.package_id = self.cli_args['--package-id']

        package_report_presigned_url = get_package_report(package_id=self.package_id).strip('"')

        # Check if the 'BROWSER' environment variable is set
        if 'BROWSER' in environ:
            call(
                [environ['BROWSER'], package_report_presigned_url]
            )

        # Generate the package report presigned url
        print(f"\"{package_report_presigned_url}\"")


class PushPackageSubCommand(Command):
    """
    Usage:
        data-sharing-tool push-package help
        data-sharing-tool push-package (--package-id=<package_id>)
                                       (--share-location=<share_location>)
                                       [--wait]

    Description:
      Push packages to a destination location. This can be either an S3 bucket with a prefix or an icav2 uri, in the
      format of icav2://<icav2-project-id>/path/to/prefix/

    Options:
      --package-id=<package_id>              The package id to push
      --share-location=<share_location>      The location to push the package to
      --wait                                 Don't terminate the command until the push job is complete

    Environment variables:
      AWS_PROFILE       The AWS profile used by boto3

    Example:
        data-sharing-tool push-package --package-id 'pkg.12345678910' --share-location s3://bucket/path/to/dest/prefix/
    """

    def __init__(self, command_argv):
        super().__init__(command_argv)
        # Import args
        self.package_id = self.cli_args['--package-id']
        self.share_location = self.cli_args['--share-location']
        self.wait = self.cli_args['--wait']

        # Generate the package report presigned url
        push_job_id = push_package(
            package_id=self.package_id,
            location_uri=self.share_location
        )

        if self.wait:
            print(f"Starting push job '{push_job_id}'")
            while True:
                package_status = get_push_job(push_job_id)['status']
                if package_status == "SUCCEEDED":
                    print(f"Generated push job: {json.dumps(push_job_id, indent=4)}")
                    break
                if package_status == "FAILED":
                    print(f"Push to destination failed, see sfn logs '{get_push_job(push_job_id)['stepFunctionsExecutionArn']}' for more information")
                    break
                if get_push_job(push_job_id)['status'] == "RUNNING":
                    sleep(10)
        else:
            print(
                f"Pushing package '{self.package_id}' to '{self.share_location}' with push job id '{push_job_id}'"
            )

class PresignPackageSubCommand(Command):
    """
    Usage:
        data-sharing-tool presign-package help
        data-sharing-tool presign-package (--package-id=<package_id>)

    Description:
      Presign a package.  This will generate a presigned url that can be used to download the package.
      The presigned urls in the shell script will be valid for one week before expiring.

    Options:
      --package-id=<package_id>             The package id to presign

    Environment variables:
      AWS_PROFILE       The AWS profile used by boto3
      BROWSER           Can be used by xdg-utils to automatically open the download script into a browser

    Example:
        data-sharing-tool presign-package --package-id 'pkg.12345678910'
    """

    def __init__(self, command_argv):
        super().__init__(command_argv)
        # Import args
        self.package_id = self.cli_args['--package-id']

        # Generate the package report presigned url
        package_script_presigned_url = presign_package(
            package_id=self.package_id
        ).strip('"')

        # Check if the 'BROWSER' environment variable is set
        if 'BROWSER' in environ:
            call(
                [environ['BROWSER'], package_script_presigned_url]
            )

        # Generate the package report presigned url
        print(f"\"{package_script_presigned_url}\"")


class ListPushJobsSubCommand(Command):
    """
    Usage:
        data-sharing-tool list-push-jobs help
        data-sharing-tool list-push-jobs [--package-id=<package_id>]

    Description:
      List Push Jobs.

      One can filter by a package id, this will match the --package-id parameter used in the push-package command.

    Options:
      --package-id=<package_id>

    Environment variables:
      AWS_PROFILE       The AWS profile used by boto3
      BROWSER           Can be used by xdg-utils to automatically open the download script into a browser

    Example:
        data-sharing-tool list-push-jobs --package-id 'pkg.12345678910'
    """

    def __init__(self, command_argv):
        super().__init__(command_argv)
        # Import args
        self.package_id = self.cli_args['--package-id']

        # Generate the package report presigned url
        print(json.dumps(
            list_push_jobs(package_id=self.package_id),
            indent=4
        ))


class GetPushJobStatusSubCommand(Command):
    """
    Usage:
        data-sharing-tool get-push-job-status help
        data-sharing-tool get-push-job-status [--push-job-id <push_job_id>]

    Description:
      Get Push Job status

    Options:
      --push-job-id=<push_job_id>

    Environment variables:
      AWS_PROFILE       The AWS profile used by boto3
      BROWSER           Can be used by xdg-utils to automatically open the download script into a browser

    Example:
        data-sharing-tool get-push-job-status --push-job-id 'psh.12345678910'
    """

    def __init__(self, command_argv):
        super().__init__(command_argv)
        # Import args
        self.push_job_id = self.cli_args['--push-job-id']

        # Generate the package report presigned url
        print(json.dumps(
            get_push_job(push_job_id=self.push_job_id),
            indent=4
        ))



# Subcommand functions
def _dispatch():
    # This variable comprises both the subcommand AND the args
    global_args: dict = docopt(dedent(__doc__), sys.argv[1:], options_first=True)

    command_argv = [global_args["<command>"]] + global_args["<args>"]

    cmd = global_args['<command>']

    # Yes, this is just a massive if-else statement
    if cmd == "help":
        # We have a separate help function for each subcommand
        print(dedent(__doc__))
        sys.exit(0)

    # Configuration commands
    elif cmd == "generate-package":
        subcommand = GeneratePackageSubCommand
    elif cmd == "list-packages":
        subcommand = ListPackagesSubCommand
    elif cmd == "get-package-status":
        subcommand = GetPackageStatusSubCommand
    elif cmd == "view-package-report":
        subcommand = ViewPackageReportSubCommand
    elif cmd == "push-package":
        subcommand = PushPackageSubCommand
    elif cmd == "presign-package":
        subcommand = PresignPackageSubCommand
    elif cmd == "list-push-jobs":
        subcommand = ListPushJobsSubCommand
    elif cmd == "get-push-job-status":
        subcommand = GetPushJobStatusSubCommand

    # NotImplemented Error
    else:
        print(dedent(__doc__))
        print(f"Could not find cmd \"{cmd}\". Please refer to usage above")
        sys.exit(1)

    # Check AWS_PROFILE env var
    if "AWS_PROFILE" not in environ:
        print("AWS_PROFILE environment variable not set. Please set it to the profile you want to use.")
        sys.exit(1)

    # Assume the role in AWS_PROFILE
    boto3.setup_default_session(
        profile_name=environ['AWS_PROFILE'],
    )

    # Check if the profile is valid
    account_id = boto3.client('sts').get_caller_identity()['Account']
    if not account_id == AWS_PRODUCTION_ACCOUNT_ID:
        print(f"Warning, you are not using the production account. You are using {account_id}")

    # Initialise / call the subcommand
    subcommand(command_argv)


def main():
    # If only the script name is provided, show help
    if len(sys.argv) == 1:
        sys.argv.append('help')
    try:
        _dispatch()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
