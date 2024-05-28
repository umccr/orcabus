# Stacky McStackFace

This CDK stack will imitate the events of the workflow run manager.  

There are three main parts of this stack: 

## A - Glue the BCLConvertManager to the BSSHFastqCopyManager

This Construct is known as Scotch. A stock-standard glue.  

> This will be all one construct

### Construct A (part 1)

Input Event Source: `orcabus.bclconvertmanager`
Input Event DetailType: `orcabus.workflowrunstatechange`
Input Event status: `succeeded`

Output Event source: `orcabus.workflowmanager`
Output Event DetailType: `orcabus.workflowrunstatechange`
Output Event status: `complete`

* The BCLConvertManagerEventHandler Construct
  * This will be triggered by the completion event from the BCLConvertManager stack.
  * Contains a standard workflow run statechange, and includes the samplesheet gz and the instrument run id
  * Pushes a workflow run manager event saying that the BCLConvert Manager has complete.

### Construct A (part 2)

Input Event Source: `orcabus.workflowmanager`
Input Event DetailType: `orcabus.workflowrunstatechange`
Input Event status: `complete`

Output Event source: `orcabus.instrumentmanager`
Output Event DetailType: `orcabus.instrumentRunStateChange`
Output Event status: `libraryrunidsregistered`

* The UpdateDataBaseOnNewSampleSheet Construct
  * Subscribes to the BCLConvertManagerEventHandler Stack outputs and updates the database:
    * Registers all library run ids in the samplesheet
    * Appends libraryrunids to the library ids in the samplesheet
    * For a given library id, queries the current athena database to collect metadata for the library
      * assay
      * type
      * workflow etc.

### Construct A (part 3)

Input Event Source: `orcabus.workflowmanager`
Input Event DetailType: `orcabus.workflowrunstatechange`
Input Event status: `complete`

Output Event source: `orcabus.bsshfastqcopyinputeventglue`
Output Event DetailType: `orcabus.workflowrunstatechange`
Output Event status: `complete`

* The BsshFastqCopyManagerInputMaker Construct
  * Subscribes to the BCLConvertManagerEventHandler Stack outputs and creates the input for the BSSHFastqCopyManager
  * Pushes an event payload of the input for the BsshFastqCopyManagerReadyEventSubmitter

### Construct A (part 4)

Input Event Source: `orcabus.bsshfastqcopymanagerinputeventglue`
Input Event DetailType: `orcabus.workflowrunstatechange`
Input Event status: `complete`

Output Event source: `orcabus.workflowmanager`
Output Event DetailType: `orcabus.workflowrunstatechange`
Output Event status: `ready`

* The BsshFastqCopyManagerReadyEventSubmitter Construct
  * Subscribes to the BCLConvertManagerEventHandler Stack outputs and generates a ready event for the BSSHFastqCopyManager


## Part B - Glue the BSSHFastqCopyManager to BCLConvertInteropQC

> This will be all one construct

This construct will be known as Selleys. 

### Construct B (Part 1)

Input Event Source: `orcabus.bsshfastqcopymanager`
Input Event DetailType: `orcabus.workflowrunstatechange`
Input Event status: `succeeded`

Output Event source: `orcabus.workflowmanager`
Output Event DetailType: `orcabus.workflowrunstatechange`
Output Event status: `complete`

* The BSSHFastqCopyManagerEventHandler Construct
  * This will be triggered by the completion event from the BSSHFastqCopyManager Construct.
  * Contains a standard workflow run statechange, the fastqlistrowgzipped, and instrument run id
  * Pushes a workflow run manager event saying that the BSSHFastqCopyManager has complete.

### Construct B (Part 2)

Input Event Source: `orcabus.workflowmanager`
Input Event DetailType: `orcabus.workflowrunstatechange`
Input Event status: `complete`

Output Event source: `orcabus.instrumentmanager`
Output Event DetailType: `orcabus.fastqlistrowstatechange`
Output Event status: `fastqlistrowsregistered`

* The UpdateDataBaseOnNewFastqListRows Construct
  * Subscribes to the BSSHFastqCopyManagerEventHandler Construct outputs and updates the database:
    * Registers all fastq list rows in the database and tie them to the libraryrunid
    * Appends libraryrunids to the library ids in the samplesheet
    * Pushes an event to say that some fastq list rows have been added to the database, with a list of affected library ids and the instrument run id

### Construct B (Part 3)

Input Event Source: `orcabus.instrumentmanager`
Input Event DetailType: `orcabus.fastqlistrowstatechange`
Input Event status: `fastqlistrowsregistered`

Output Event source: `orcabus.bclconvertinteropqcinputeventglue`
Output Event DetailType: `orcabus.workflowrunstatechange`
Output Event status: `complete`

* The BCLConvertInteropQCInputMaker Construct
  * Subscribes to the BSSHFastqCopyManagerEventHandler Construct outputs and creates the input for the BCLConvertInteropQC
  * Pushes an event payload of the input for the BCLConvertInteropQCReadyEventSubmitter

### Construct B (Part 4)

Input Event Source: `orcabus.bclconvertinteropqcinputeventglue`
Input Event DetailType: `orcabus.workflowrunstatechange`
Input Event status: `complete`

Output Event source: `orcabus.workflowmanager`
Output Event DetailType: `orcabus.workflowrunstatechange`
Output Event status: `ready`

* The BCLConvertInteropQCReadyEventSubmitter Construct
  * Subscribes to the BSSHFastqCopyManagerEventHandler Construct outputs and generates a ready event for the BCLConvertInteropQC
    
## Part C - Glue the FastqListRow Output Event to the ctTSOv2ReadySfn

> This will be all one stack

The most important glue of them all. Super Glue!

## Part C - Glue the FastqListRow Output Event to the ctTSOv2ReadySfn

> This will be all one stack

The most important glue of them all. Super Glue!

### Construct C (Part 1)

Input Event Source: `orcabus.instrumentrunmanager`
Input Event DetailType: `orcabus.librarystatechange`
Input Event status: `fastqlistrowregistered`

Output Event source: `orcabus.cttsov2inputeventglue`
Output Event DetailType: `orcabus.workflowrunstatechange`
Output Event status: `awaitinginput`

* The fastqListRowsToctTSOv2InputMaker Construct
  * Subscribes to the FastqListRowEventHandler Construct outputs and creates the input for the ctTSOv2ReadySfn
  * Pushes an event payload of the input for the ctTSOv2ReadyEventSubmitters
  * From the awaiting input event, we then generate a workflow ready status for each of the cttso run workflows


### Construct C (Part 2)

Output Event source: `orcabus.cttsov2inputeventglue`
Output Event DetailType: `orcabus.workflowrunstatechange`
Output Event status: `awaitinginput`


Output Event source: `orcabus.cttsov2inputeventglue`
Output Event DetailType: `orcabus.workflowrunstatechange`
Output Event status: `ready`

* The ctTSOv2InputMaker, subscribes to the cttsov2 input event glue (itself) and generates a ready event for the ctTSOv2ReadySfn
  * For the cttso v2 workflow we require a samplesheet, a set of fastq list rows (provided in the last step)
  * However, in order to be 'ready' we need to use a few more variables such as  
    * icaLogsUri,
    * analysisOuptutUri
    * cacheUri
    * projectId
    * userReference


### Construct C (Part 3)

Output Event source: `orcabus.cttsov2inputeventglue`
Output Event DetailType: `orcabus.workflowrunstatechange`
Output Event status: `ready`

Output Event source: `orcabus.workflowmanager`
Output Event DetailType: `orcabus.workflowrunstatechange`
Output Event status: `ready`

* The ctTSOv2ReadyEventSubmitter Construct
  * Subscribes to the ctTSOv2InputMaker Construct outputs and generates a ready event for the ctTSOv2ReadySfn



## Kicking things off

We need a BCLConvertManager Success event to get things started! 

An example is as follows:
