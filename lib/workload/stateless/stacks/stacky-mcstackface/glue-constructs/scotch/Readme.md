# Scotch Glue

> A stock-standard glue.

## Four parts to this construct:

### Part 1

* Input Event Source: `orcabus.bclconvertmanager`
* Input Event DetailType: `orcabus.workflowrunstatechange`
* Input Event status: `complete`


* Output Event source: `orcabus.workflowmanager`
* Output Event DetailType: `orcabus.workflowrunstatechange`
* Output Event status: `complete`


* The BCLConvertManagerEventHandler Construct
  * This will be triggered by the completion event from the BCLConvertManager stack.
  * Contains a standard workflow run statechange, and includes the samplesheet gz and the instrument run id
  * Pushes a workflow run manager event saying that the BCLConvert Manager has complete.


![](images/part_1/bclconvertmanager_external_event_handler_sfn.png)


### Part 2

* Input Event Source: `orcabus.workflowmanager`
* Input Event DetailType: `orcabus.workflowrunstatechange`
* Input Event status: `complete`


* Output Event source: `orcabus.instrumentmanager`
* Output Event DetailType: `orcabus.samplesheetstatechange`
* Output Event status: `samplesheetregistered`


* The UpdateDataBaseOnNewSampleSheet Construct
  * Subscribes to the BCLConvertManagerEventHandler Stack outputs and updates the database:
    * Registers all library run ids in the samplesheet
    * Appends libraryrunids to the library ids in the samplesheet
    * For a given library id, queries the current athena database to collect metadata for the library
      * assay
      * type
      * workflow etc.

![](images/part_2/update_database_on_new_samplesheet_simple_sfn.png)

OR

![](images/part_2/update_database_on_new_samplesheet_full_sfn.png)


### Part 3

* Input Event Source: `orcabus.workflowmanager`
* Input Event DetailType: `orcabus.workflowrunstatechange`
* Input Event status: `complete`


* Output Event source: `orcabus.bsshfastqcopyinputeventglue`
* Output Event DetailType: `orcabus.workflowrunstatechange`
* Output Event status: `complete`


* The BsshFastqCopyManagerInputMaker Construct
  * Subscribes to the BCLConvertManagerEventHandler Stack outputs and creates the input for the BSSHFastqCopyManager
  * Pushes an event payload of the input for the BsshFastqCopyManagerReadyEventSubmitter

  
![](images/part_3/bssh_fastq_copy_maker_data_input_maker_sfn.png)

With the parent function displayed here:

![](../../../../../components/event-workflowrunstatechange-internal-to-inputmaker-sfn/images/workflowrunstatechange_input_maker_step_function_sfn.png)

### Part 4

* Input Event Source: `orcabus.bsshfastqcopymanagerinputeventglue`
* Input Event DetailType: `orcabus.workflowrunstatechange`
* Input Event status: `complete`


* Output Event source: `orcabus.workflowmanager`
* Output Event DetailType: `orcabus.workflowrunstatechange`
* Output Event status: `ready`


* The BsshFastqCopyManagerReadyEventSubmitter Construct
  * Subscribes to the BCLConvertManagerEventHandler Stack outputs and generates a ready event for the BSSHFastqCopyManager

![](images/part_4/bssh_fastq_copy_input_maker_to_internal_ready_sfn.png)