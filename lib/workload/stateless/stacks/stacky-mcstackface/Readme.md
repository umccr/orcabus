# Stacky McStackFace

This CDK stack will imitate the events of the workflow run manager.  

There are three main parts of this stack: 

## A - Glue the BCLConvertManager to the BSSHFastqCopyManager

This Construct is known as Scotch. A stock-standard glue.  

> This will be all one construct

### Construct A (part 1)

Input Event Source: `orcabus.workflowmanager`
Input Event DetailType: `WorkflowRunStateChange`
Input Event status: `complete`

Output Event source: `orcabus.instrumentmanager`
Output Event DetailType: `InstrumentRunStateChange`
Output Event status: `libraryrunidsregistered`

* The UpdateDataBaseOnNewSampleSheet Construct
  * Subscribes to the BCLConvertManagerEventHandler Stack outputs and updates the database:
    * Registers all library run ids in the samplesheet
    * Appends libraryrunids to the library ids in the samplesheet
    * For a given library id, queries the current athena database to collect metadata for the library
      * assay
      * type
      * workflow etc.

### Construct A (part 2)

Input Event Source: `orcabus.workflowmanager`
Input Event DetailType: `WorkflowRunStateChange`
Input Event status: `complete`

Output Event source: `orcabus.bsshfastqcopyinputeventglue`
Output Event DetailType: `WorkflowRunStateChange`
Output Event status: `complete`

* The BsshFastqCopyManagerInputMaker Construct
  * Subscribes to the BCLConvertManagerEventHandler Stack outputs and creates the input for the BSSHFastqCopyManager
  * Pushes an event payload of the input for the BsshFastqCopyManagerReadyEventSubmitter


## Part B - Glue the BSSHFastqCopyManager to BCLConvertInteropQC

> This will be all one construct


### Construct B (Part 1)

Input Event Source: `orcabus.workflowmanager`
Input Event DetailType: `WorkflowRunStateChange`
Input Event status: `complete`

Output Event source: `orcabus.instrumentmanager`
Output Event DetailType: `InstrumentRunStateChange`
Output Event status: `fastqlistrowsregistered`

* The UpdateDataBaseOnNewFastqListRows Construct
  * Subscribes to the BSSHFastqCopyManagerEventHandler Construct outputs and updates the database:
    * Registers all fastq list rows in the database and tie them to the libraryrunid
    * Appends libraryrunids to the library ids in the samplesheet
    * Pushes an event to say that some fastq list rows have been added to the database, with a list of affected library ids and the instrument run id

### Construct B (Part 2)

Input Event Source: `orcabus.workflowmanager`
Input Event DetailType: `WorkflowRunStateChange`
Input Event status: `complete`

Output Event source: `orcabus.bclconvertinteropqcinputeventglue`
Output Event DetailType: `WorkflowRunStateChange`
Output Event status: `complete`

* The BCLConvertInteropQCInputMaker Construct
  * Subscribes to the BSSHFastqCopyManagerEventHandler Construct outputs and creates the input for the BCLConvertInteropQC
  * Pushes an event payload of the input for the BCLConvertInteropQCReadyEventSubmitter
    
## Part C - Glue the FastqListRow Output Event to the ctTSOv2ReadySfn

> This will be all one stack

The most important glue of them all. Super Glue!

### Construct C (Part 1)

Input Event Source: `orcabus.instrumentrunmanager`
Input Event DetailType: `InstrumentRunStateChange`
Input Event status: `fastqlistrowregistered`

Output Event source: `orcabus.cttsov2inputeventglue`
Output Event DetailType: `WorkflowRunDraftStateChange`
Output Event status: `awaitinginput`

* The fastqListRowsToctTSOv2InputMaker Construct
  * Subscribes to the FastqListRowEventHandler Construct outputs and creates the input for the ctTSOv2ReadySfn
  * Pushes an event payload of the input for the ctTSOv2ReadyEventSubmitters
  * From the awaiting input event, we then generate a workflow ready status for each of the cttso run workflows


### Construct C (Part 2)

Input Event source: `orcabus.cttsov2inputeventglue`
Input Event DetailType: `WorkflowRunDraftStateChange`
Input Event status: `awaitinginput`

Output Event source: `orcabus.cttsov2inputeventglue`
Output Event DetailType: `WorkflowRunStateChange`
Output Event status: `ready`

* The ctTSOv2InputMaker, subscribes to the cttsov2 input event glue (itself) and generates a ready event for the ctTSOv2ReadySfn
  * For the cttso v2 workflow we require a samplesheet, a set of fastq list rows (provided in the last step)
  * However, in order to be 'ready' we need to use a few more variables such as  
    * icaLogsUri,
    * analysisOutputUri
    * cacheUri
    * projectId
    * userReference


## Part D - Glue the FastqListRow Output Event to the wgtsQcReadySfn


### Construct D - (Part 1)

Input Event Source: `orcabus.instrumentrunmanager`
Input Event DetailType: `InstrumentRunStateChange`
Input Event status: `fastqlistrowregistered`

Output Event source: `orcabus.wgtsinputeventglue`
Output Event DetailType: `WorkflowRunDraftStateChange`
Output Event status: `awaitinginput`

* The fastqListRowsToWgtsQcInputMaker Construct
  * Subscribes to the FastqListRowEventHandler Construct outputs and creates the input for the wgtsQcReadySfn
  * Pushes an event payload of the input for the wgtsQcReadyEventSubmitters
  * From the awaiting input event, we then generate a workflow ready status for each of the WGTS QC Run Workflows


### Construct D - (Part 2)

Input Event source: `orcabus.wgtsinputeventglue`
Input Event DetailType: `WorkflowRunDraftStateChange`
Input Event status: `awaitinginput`

Output Event source: `orcabus.wgtsinputeventglue`
Output Event DetailType: `WorkflowRunStateChange`
Output Event status: `ready`

* The wgtsQcInputMaker, subscribes to the wgts input event glue (itself) and generates a ready event for the wgtsQcReadySfn
  * The awaiting input event is almost ready, however we need to use a few more variables such as 
    * icaLogsUri,
    * analysisOutputUri
    * cacheUri
    * projectId
    * userReference
