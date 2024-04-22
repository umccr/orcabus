# Custom Event Archiver

EventBridge does support a bus archive, but we don't have control over it and can't inspect it.\
In order to get a history record of any and all events that go over the OrcaBus event bus, custom event archivers are needed to write specific or all events as JSON objects to a dedicated S3 bucket using its timestamp (structure by year/month/day prefixes).

<!-- TOC -->
* [Universal Event Archiver](#universal-event-archiver)
  * [Inputs](#inputs)
  * [Outputs](#outputs)
* [Sanitize for object key](#sanitize-for-object-key)

<!-- TOC -->


## universal-event-archiver

### inputs

The lambda function takes all events that go over the OrcaBus event bus, and write it as JSON to the dedicated S3 bucket Formatting the S3 key with year/month/day partitioning.

Parameters: 
* eventBus
* s3bucket
* vpc

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

### Outputs

S3 object of that event archived in dedicated s3 bucket.\
URI: s3://{bucket_name}/events/year={year}/month={month}/day={day}/{event_type}_{totalSeconds.microsecond}.json \
Example Outputs: ```s3://{bucket_name}/events/year=2024/month=04/day=16/WorkflowRequest_1713252338.243297.json```


## Sanitize for object key

Event details will be retrieved as part of object key. In case of any issues happened when object key used in filenames or URL, function ```sanitize_string``` will be applied.

* Any sequence of characters that are not alphanumeric or underscores including special characters and spaces will be replaced with an underscore "_".
* Any leading and trailing underscore and whitespace will be removed.

Test case: ```sanitize_string("  test %01## 23%!~@#$%^&*(). case.  ")``` will produce ```test_01_23_case```