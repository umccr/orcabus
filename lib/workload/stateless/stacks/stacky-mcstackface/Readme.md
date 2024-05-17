# Stacky McStackFace

This CDK stack will imitate the events of the workflow run manager.  

There are three main parts of this stack: 

## Part 1 - Glue the BCLConvertManager to the BSSHFastqCopyManager

This Construct is known as Scotch. A stock-standard glue.  

> This will be all one construct

### Construct 1a

Input Event Source: `orcabus.bclconvertmanager`
Input Event DetailType: `orcabus.workflowrunstatechange`
Input Event status: `succeeded`

Output Event source: `orcabus.workflowrunmanager`
Output Event DetailType: `orcabus.workflowrunstatechange`
Output Event status: `complete`

* The BCLConvertManagerEventHandler Construct
  * This will be triggered by the completion event from the BCLConvertManager stack.
  * Contains a standard workflow run statechange, and includes the samplesheet gz and the instrument run id
  * Pushes a workflow run manager event saying that the BCLConvert Manager has complete.

### Construct 1b

Input Event Source: `orcabus.workflowrunmanager`
Input Event DetailType: `orcabus.workflowrunstatechange`
Input Event status: `complete`

Output Event source: `orcabus.metadatamanager`
Output Event DetailType: `orcabus.librarystatechange`
Output Event status: `libraryrunidregistered`

* The UpdateDataBaseOnNewSampleSheet Construct
  * Subscribes to the BCLConvertManagerEventHandler Stack outputs and updates the database:
    * Registers all library run ids in the samplesheet
    * Appends libraryrunids to the library ids in the samplesheet
    * For a given library id, queries the current athena database to collect metadata for the library
      * assay
      * type
      * workflow etc.

### Construct 1c

Input Event Source: `orcabus.workflowrunmanager`
Input Event DetailType: `orcabus.workflowrunstatechange`
Input Event status: `complete`

Output Event source: `orcabus.bclconvertmanagerinputeventglue`
Output Event DetailType: `orcabus.workflowrunstatechange`
Output Event status: `complete`

* The BsshFastqCopyManagerInputMaker Construct
  * Subscribes to the BCLConvertManagerEventHandler Stack outputs and creates the input for the BSSHFastqCopyManager
  * Pushes an event payload of the input for the BsshFastqCopyManagerReadyEventSubmitter

### Construct 1d

Input Event Source: `orcabus.bsshfastqcopymanagerinputeventglue`
Input Event DetailType: `orcabus.workflowrunstatechange`
Input Event status: `complete`

Output Event source: `orcabus.workflowrunmanager`
Output Event DetailType: `orcabus.workflowrunstatechange`
Output Event status: `ready`

* The BsshFastqCopyManagerReadyEventSubmitter Construct
  * Subscribes to the BCLConvertManagerEventHandler Stack outputs and generates a ready event for the BSSHFastqCopyManager


## Part 2 - Glue the BSSHFastqCopyManager to BCLConvertInteropQC

> This will be all one construct

This construct will be known as Selleys. 

### Construct 2a

Input Event Source: `orcabus.bsshfastqcopymanager`
Input Event DetailType: `orcabus.workflowrunstatechange`
Input Event status: `succeeded`

Output Event source: `orcabus.workflowrunmanager`
Output Event DetailType: `orcabus.workflowrunstatechange`
Output Event status: `complete`

* The BSSHFastqCopyManagerEventHandler Construct
  * This will be triggered by the completion event from the BSSHFastqCopyManager Construct.
  * Contains a standard workflow run statechange, the fastqlistrowgzipped, and instrument run id
  * Pushes a workflow run manager event saying that the BSSHFastqCopyManager has complete.

### Construct 2b

Input Event Source: `orcabus.workflowrunmanager`
Input Event DetailType: `orcabus.workflowrunstatechange`
Input Event status: `complete`

Output Event source: `orcabus.metadatamanager`
Output Event DetailType: `orcabus.librarystatechange`
Output Event status: `fastqlistrowregistered`

* The UpdateDataBaseOnNewFastqListRows Construct
  * Subscribes to the BSSHFastqCopyManagerEventHandler Construct outputs and updates the database:
    * Registers all fastq list rows in the database and tie them to the libraryrunid
    * Appends libraryrunids to the library ids in the samplesheet
    * Pushes an event to say that some fastq list rows have been added to the database, with a list of affected library ids and the instrument run id

### Construct 2c

Input Event Source: `orcabus.workflowrunmanager`
Input Event DetailType: `orcabus.workflowrunstatechange`
Input Event status: `complete`

Output Event source: `orcabus.bclconvertinteropqcinputeventglue`
Output Event DetailType: `orcabus.workflowrunstatechange`
Output Event status: `complete`

* The BCLConvertInteropQCInputMaker Construct
  * Subscribes to the BSSHFastqCopyManagerEventHandler Construct outputs and creates the input for the BCLConvertInteropQC
  * Pushes an event payload of the input for the BCLConvertInteropQCReadyEventSubmitter

### Construct 2d

Input Event Source: `orcabus.bclconvertinteropqcinputeventglue`
Input Event DetailType: `orcabus.workflowrunstatechange`
Input Event status: `complete`

Output Event source: `orcabus.workflowrunmanager`
Output Event DetailType: `orcabus.workflowrunstatechange`
Output Event status: `ready`

* The BCLConvertInteropQCReadyEventSubmitter Construct
  * Subscribes to the BSSHFastqCopyManagerEventHandler Construct outputs and generates a ready event for the BCLConvertInteropQC
    
## Part 3 - Glue the FastqListRow Output Event to the ctTSOv2ReadySfn

> This will be all one stack

The most important glue of them all. Gorilla Glue!

### Construct 3a

Input Event Source: `orcabus.metadatamanager`
Input Event DetailType: `orcabus.librarystatechange`
Input Event status: `fastqlistrowregistered`

Output Event source: `orcabus.workflowrunmanager`
Output Event DetailType: `orcabus.librarystatechange`
Output Event status: `fastqlistrowsregistered`

* The FastqListRowEventHandler Construct
  * This will be triggered by the completion event from the UpdateDataBaseOnNewFastqListRows complete event.
  * Contains a standard workflow run statechange
  * And a list of fastq list rows / library ids that have changed, and the instrument run id

### Construct 3b

Input Event source: `orcabus.workflowrunmanager`
Input Event DetailType: `orcabus.librarystatechange`
Input Event status: `fastqlistrowsregistered`

Output Event source: `orcabus.cttsov2inputeventglude`
Output Event DetailType: `orcabus.workflowrunstatechange`
Output Event status: `complete`

* The ctTSOv2InputMaker Construct
  * Subscribes to the FastqListRowEventHandler Construct outputs and creates the input for the ctTSOv2ReadySfn
  * Pushes an event payload of the input for the ctTSOv2ReadyEventSubmitter

### Construct 3c

Output Event source: `orcabus.cttsov2inputeventglude`
Output Event DetailType: `orcabus.workflowrunstatechange`
Output Event status: `complete`

Output Event source: `orcabus.workflowrunmanager`
Output Event DetailType: `orcabus.workflowrunstatechange`
Output Event status: `ready`

* The ctTSOv2ReadyEventSubmitter Construct
  * Subscribes to the ctTSOv2InputMaker Construct outputs and generates a ready event for the ctTSOv2ReadySfn

