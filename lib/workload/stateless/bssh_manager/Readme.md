# BSSH Manager

The bssh manager runs performs the following logic

* Handles the ICAv2 AutoLaunch Workflow Session event that kicks off BCLConvert in the BaseSpace Managed ICAv2 Project.
* Copies data from BSSH to our own ICAv2 project

## Lambdas in this directory

All lambdas run on python 3.11 or higher.

## Workflow Session Handler

The Basespace Workflow Session will emit a completion event that can be imported by the workflow session handler.

The workflow session handler is a step function that has one main lambda

This lambda then performs the following tasks

1. Get the output directory of the underlying BCLConvert run
2. Collect the bssh_output.json file from the BCLConvert run output folder
3. Collect the basespace run id from the bssh output json
4. Collect the run id from the run info xml
5. Collect the fastq list csv file from the BCLConvert run output folder
6. Collect the samplesheet path from the BCLConvert run output folder (as we might need this to go into the cttso directories)
7. Query the metadata manager (the portal APIs will do for now), to determine where the outputs should go?
    * All outputs will go to the byob cache bucket, 
    * but for ctTSOv2, we will also need to copy some outputs to the ctTSOv2 cache directory
8. Return a manifest of icav2 uris where each key represents a ICAv2 data uri (file) and the value is a list of icav2 uris where each uri is a destination for a given file.

The step function then completes by submitting an event with the manifest as the payload

## The manifest inverter

This converts the dictionary from a dictionary where the keys are source uris and the values are lists of destination uris 
to a list of dicts, where for each dictionary there is a destination uri key and a source uri key that contains the list of source uris that need to go to this destination.  
This reduces the number of jobs to equal only the number of folders required to be generated, rather than the number of files multiplied by the number of locations the files need to be copied to.  

## The CopyData handler

The CopyData handler AWS step function takes in a destination URI and a list of source URIs and calls the ICAv2 CopyDataBatch job.  

This will copy all the files in the source URIs to the destination URI.  

The CopyData handler returns the job id of the copy data batch API.

## Job Status Handler

The Job Status handler will query a copybatchjob and return a boolean.  

True if the workflow has succeeded and false if it has failed (or been terminated).  

A None value will be returned if the job is still running.

## Event Handling


