# Titebond Glue

> Glue for the common orcabus

Originally I wanted to go for gorilla, but not being in alphabetical order it causes some problems.  

 
## Part D - Glue the FastqListRow Output Event to the wgtsReadySfn

> This will be all one stack

### Construct D (Part 1)

Input Event Source: `orcabus.metadatamanager`
Input Event DetailType: `LibraryStateChange`
Input Event status: `fastqlistrowregistered`

Output Event source: `orcabus.wgtsinputeventglue`
Output Event DetailType: `WorkflowRunStateChange`
Output Event status: `awaitinginput`

* The fastqListRowsToWgtsQcInputMaker Construct
  * Subscribes to the FastqListRowEventHandler Construct outputs and creates the input for the wgtsQcReadySfn
  * Pushes an event payload of the input for the wgtsQcReadyEventSubmitters
  * From the awaiting input event, we then generate a workflow ready status for each of the wgts QC run workflows


### Construct D (Part 2)

Input Event source: `orcabus.wgtsinputeventglue`
Input Event DetailType: `WorkflowRunStateChange`
Input Event status: `awaitinginput`

Output Event source: `orcabus.wgtsinputeventglue`
Output Event DetailType: `WorkflowRunStateChange`
Output Event status: `ready`

* The wgtsQcInputMaker, subscribes to the wgts QC input event glue (itself) and generates a ready event for the wgtsQcReadySfn
  * However, in order to be 'ready' we need to use a few more variables such as  
    * icaLogsUri
    * analysisOutputUri
    * cacheUri
    * projectId
    * userReference

We have another event that will subscribe to the wgts workflow run state change events for
complete wgts workflows. If the workflow is complete, this service will find the rgid of the workflow
from the portal run id.

This qc complete event will be used by the tumor normal service to 'tick-off' rgids as ready for running.  

