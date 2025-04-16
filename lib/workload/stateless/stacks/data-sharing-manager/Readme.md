# Data Sharing Manager

## Description

The sharing manager works two main ways, as a 'push' or 'pull' step.

Inputs are configured into the API, and then the step function is launched.  

For pushing sharing types, if configuration has not been tried with the '--dryrun' flag first, the API will return an error. 
This is so we don't go accidentally pushing data to the wrong place.

A job will then be scheduled and ran in the background, a user can check the status of the job by checking the job status in the API.


### Push or Pull?

When pushing, we use the s3 steps copy manager to 'push' data to a bucket. We assume that we have access to this bucket.
When pulling, we generate a presigned url containing a script that can be used to download the data.


### Pushing Outputs

Once a Job has completed pushing data, the job response object can be queried to gather the following information:
* fastq data that was pushed
* portal run ids that were pushed
* list the s3 objects that were pushed.


### Invoking a job

The Job API launch comprises the following inputs:

* instrumentRunIdList: The list of instrument run ids to be shared (used for fastq sharing only), can be used in tandem alongside one of the metadata attributes of libraryId, subjectId, individualId or projectId and will take an intersection of the two for fastq data.
* libraryIdList: A list of library ids to be shared. Cannot be used alongside subjectIdList, individualIdList or projectIdList.
* subjectIdList: A list of subject ids to share. Cannot be used alongside libraryIds, projectIdList or individualIdList.
* projectIdList: A list of project names to share. Cannot be used alongside libraryIds, subjectIdList or individualIdList.
* dataTypeList: A list of data types to share. Can be one or more of: 
  * 'Fastq'
  * 'SecondaryAnalysis'
* defrostArchivedFastqs: A boolean flag to determine if we should de-frost archived fastqs. This is only used for fastq data types.
  If set to true, and the fastq data is archived, the data de-frosted will be triggered but the workflow will not wait for the data to be de-frosted and will fail with a DataDefrostingError.  
* secondaryAnalysisWorkflowList: A list of secondary analysis workflows to share, can be used in tandem with data types. 
  The possible values are one or more of:
  * cttsov2 (or dragen-tso500-ctdna)
  * tumor-normal (or dragen-wgts-dna)
  * wts (or dragen-wgts-rna)
  * oncoanalyser-wgts-dna
  * oncoanalyser-wgts-rna
  * oncoanalyser-wgts-dna-rna
  * rnasum
  * umccrise
  * sash
* portalRunIdList: A list of portal run ids to share. 
  For secondaryanalysis data types, this parameter will take precedence over any metadata specified or secondary workflow types specified.
* portalRunIdExclusionList: A list of portal run ids NOT to share.
  For secondaryanalysis data types, this parameter can be used in tandem with metadata or secondary workflow types specified. 
  This is useful if a known workflow has been repeated and we do not wish to share the original.  
* shareType: The type of share, must be one of 'push' or 'pull'
* shareDestination: The destination of the share, only required if shareType is 'push'. Can be an 'icav2' or 's3' uri.
* dryrun: A boolean flag, used when we set the push type to true to determine if we should actually push the data or instead just print out to the console the list of s3 objects we would have sent. 


### Steps Functions Output

* The steps function will output two attributes:
  * limsCsv presigned url - a presigned url to download a csv file containing the lims metadata to share
  * data-download script presigned url - a presigned url to download a bash script that can be used to download the data.

  
### Data Download Url for Pulling Data

The data download script will have the following options:

* --data-download-path - the root path of the data to be downloaded, this directory must already exist.
* --dryrun | --dry-run - a flag to indicate that the script should not download the data, but instead print the commands that would be run and directories that would be created.
* --check-size-only    - a flag to skip any downloading if the existing file is the same size as the file to be downloaded.
* --skip-existing      - a flag to skip downloading files that already exist in the destination directory (regardless of size).
* --print-summary      - a flag to print a summary of the files that would be downloaded and the total size of the download.



  
