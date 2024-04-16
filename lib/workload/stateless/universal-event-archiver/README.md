# Universal Event Archiver

<!-- TOC -->
* [Universal Event Archiver](#universal-event-archiver)
  * [Inputs](#inputs)
  * [Outputs](#outputs)
    * [Sanitize for object key](#sanitize-for-object-key)

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


## Sanitize for object key

In case of any issues happened when used in filenames or URL, function ```sanitize_string``` will be applied:
* Removes any leading and trailing whitespace from the input string to clean it up before processing.
* [^\w]+: Matches any sequence of characters that are not alphanumeric or underscores. This includes special characters and spaces. "_" replaces the matched sequences with an underscore.
* strip('_') strip any leading and trailing underscore.

Test case: ```sanitize_string("  test %01## 23%!~@#$%^&*(). case.  ")``` will produce ```test_01_23_case```
