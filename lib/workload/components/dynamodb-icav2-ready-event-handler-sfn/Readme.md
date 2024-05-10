# Dynamodb Handle Ready Event From Workflow Run Manager for ICAv2 Workflow Run

## Summary

This step function construct listens to ready events from the workflow run manager through the main Orcabus event pipe.  

The step function is then triggered if the workflow type matches that specified in the step function.

If the portal run id is already in the database, then the step function just return the existing status

If the portal run id is not in the database, then the step function will launch the workflow on the ICAv2 platform.  
Then store the analysis configurations in the database and return an event back to the orcabus to say that the analysis has started running.  

## Input

## Construct Inputs

* tableName - The name of the table to store the analysis configurations
* stateMachineName - This state machine's name
* workflowPlatformType - either cwl or nextflow.  
* pipelineIdSsmPath - The ssm parameter path to the pipeline id, the pipeline id can also be provided in the event, if the user wants to use a custom id.  
* icav2AccessTokenSecretObj - The secretsmanager object for the icav2 access token
* detailType - The detail type of the event to listen to (workflowRunStateChange)
* eventBusName - The event bus name (OrcaBusMain)
* triggerLaunchSource - The workflow run manager source to listen to (orcabus.wfm) 
* internalEventSource - The internal event source to push events to (orcabus.cttsov2)
* generateInputsJsonSfn - The step function to generate the inputs json for the workflow run (this is a subfunction of this step function)
* workflowType - The workflow Type, either cttsov2 or bclconvert_interop_qc
* workflowVersion - The workflow version (not currently used)
* serviceVersion - The service version (not currently used)

## Requirements of the generateInputsJsonSfn

/TODO
