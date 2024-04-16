# Universal Event Archiver

<!-- TOC -->
* [Universal Event Archiver](#universal-event-archiver)
  * [Inputs](#inputs)
  * [Outputs](#outputs)

<!-- TOC -->


## Inputs

The lambda function takes all events that go over the OrcaBus event bus, and write it as JSON to the dedicated S3 bucket Formatting the S3 key with year/month/day partitioning.\

Parameters: 
* s3bucket
* eventBus

Example Input: schema from config/event_schemas/WorkflowRequest.json

```json5
{
  "openapi": "3.0.0",
  "info": {
    "version": "1.0.0",
    "title": "WorkflowRequest"
  },
  "paths": {},
  "components": {
    "schemas": {
      "Event": {
        ...
      }
    }
  }
}

```

## Outputs

S3 object of that event archived in dedicated s3 bucket.\
URI: s3://{bucket_name}/events/{year}/{month}/{day}/{event_type}_{hour_minutes_seconds}.json \
Example Outputs: ```s3://{bucket_name}/events/2024/04/16/WorkflowRequest_00_02_32.json```

