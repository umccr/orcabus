# Oncoanalyser Pipeline Manager

## Description

1. Parse in the WorkflowRunStateChange event and submit a lambda to the nextflow stack to trigger a new run. 

2. Subscribe to the batch events from the default event bus
   * Marry up the event to the workflow run / portal run id
   * Generate a workflow run statechange event to submit to the Orcabus event bus


