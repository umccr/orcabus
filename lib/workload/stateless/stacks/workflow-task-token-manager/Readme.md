# Workflow Task Token Manager

This is a simple set of step functions:

## Service 1: TaskTokenManager

1. Listens to any 'WorkflowRunStateChangeSync' event from the OrcaBus
2. Splits the task token out from the event details and stores it in a DynamoDB table indexed by the portal run id
3. Publishes a WorkflowRunStateChange event, with the task token removed

## Service 2: Send Task Token Success Events

1. Listens to any 'WorkflowRunStateChange' event with a terminal `Status` from the OrcaBus
2. Looks up the portal run id in the DynamoDB table to get the task token (if it exists)
3. Sends either a `TaskTokenSuccess` or `TaskTokenFailure` event

