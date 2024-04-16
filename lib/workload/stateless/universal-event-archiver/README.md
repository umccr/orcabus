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

Example Input: general Event structure

```json5
{
  "version": "0",
  "id": "UUID",
  "detail-type": "event_name",
  "source": "event source",
  "account": "ARN",
  "time": "timestamp",
  "region": "region",
  "resources": [
    "ARN"
  ],
  "detail": {
    ...
  }
}

```

## Outputs

S3 object of that event archived in dedicated s3 bucket.\
URI: s3://{bucket_name}/events/{year}/{month}/{day}/{event_type}_{totalSeconds.microsecond}.json \
Example Outputs: ```s3://{bucket_name}/events/2024/04/16/WorkflowRequest_1713252338.243297.json```

