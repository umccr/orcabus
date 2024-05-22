# Selleys Glue

> Glue for the common orcabus

## Four parts to this construct:

### Part 1

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

![](images/part_1/bssh_fastq_copy_manager_event_handler_sfn.png)

### Part 2

Input Event Source: `orcabus.workflowrunmanager`
Input Event DetailType: `orcabus.workflowrunstatechange`
Input Event status: `complete`

Output Event source: `orcabus.metadatamanager`
Output Event DetailType: `orcabus.librarystatechange`
Output Event status: `fastqlistrowsregistered`

* The UpdateDataBaseOnNewFastqListRows Construct
  * Subscribes to the BSSHFastqCopyManagerEventHandler Construct outputs and updates the database:
    * Registers all fastq list rows in the database and tie them to the libraryrunid
    * Appends libraryrunids to the library ids in the samplesheet
    * Pushes an event to say that some fastq list rows have been added to the database, with a list of affected library ids and the instrument run id

![](images/part_2/update_database_on_new_fastqlist_rows_simple_sfn.png)

OR

![](images/part_2/update_database_on_new_fastqlistrows_full_sfn.png)

### Part 3

Input Event Source: `orcabus.workflowrunmanager`
Input Event DetailType: `orcabus.workflowrunstatechange`
Input Event status: `complete`

Output Event source: `orcabus.bclconvertinteropqcinputeventglue`
Output Event DetailType: `orcabus.workflowrunstatechange`
Output Event status: `complete`

* The BCLConvertInteropQCInputMaker Construct
  * Subscribes to the BSSHFastqCopyManagerEventHandler Construct outputs and creates the input for the BCLConvertInteropQC
  * Pushes an event payload of the input for the BCLConvertInteropQCReadyEventSubmitter

![](images/part_3/generate_interopqc_event_maker_sfn.png)

With the parent function displayed here:

![](../../../../../components/event-workflowrunstatechange-internal-to-inputmaker-sfn/images/workflowrunstatechange_input_maker_step_function_sfn.png)

### Part 4

Input Event Source: `orcabus.bclconvertinteropqcinputeventglue`
Input Event DetailType: `orcabus.workflowrunstatechange`
Input Event status: `complete`

Output Event source: `orcabus.workflowrunmanager`
Output Event DetailType: `orcabus.workflowrunstatechange`
Output Event status: `ready`

* The BCLConvertInteropQCReadyEventSubmitter Construct
  * Subscribes to the BSSHFastqCopyManagerEventHandler Construct outputs and generates a ready event for the BCLConvertInteropQC

![](images/part_4/generate_bclconvert_interopqc_ready_event_simple_sfn.png)
