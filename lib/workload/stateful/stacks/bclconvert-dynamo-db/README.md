# BclConvert Manager DynamoDB Tables

## BclConvert Manager Translator Table

This table will record event translator process in BclConvert Manager.

The orignal input and orcabus event after translation will be saved in the dynamo db for recording of the process.

Dynamodb format:
| id | id_type | analysis_id | analysis_status | portal_run_id | db_uuid | original_external_event | translated_internal_ica_event | timestamp |
| -------------- | ---- | ------- | ------- | ---- | ------- | ------- | ------- |------- |
| dxxxxx-6xxxx-fxxx-1xxx-5xxxxx | portal_run_id | dxxxxx-6xxxx-fxxx-1xxx-5xxxxx | | | dxxxxx-6xxxx-fxxx-1xxx-5xxxxx | | | |
| dxxxxx-6xxxx-fxxx-1xxx-5xxxxx | analysis_id |  |   |dxxxxx-6xxxx-fxxx-1xxx-5xxxxx | dxxxxx-6xxxx-fxxx-1xxx-5xxxxx | | | |
| dxxxxx-6xxxx-fxxx-1xxx-5xxxxx | db_uuid | dxxxxx-6xxxx-fxxx-1xxx-5xxxxx | INITIALIZING | 20xxxxxxxxxx | | {"correlationId": "",...} | {'portal_run_id': "",...} | 2024-01-01T00:11:35Z |
|dxxxxx-6xxxx-fxxx-1xxx-5xxxxx | db_uuid | dxxxxx-6xxxx-fxxx-1xxx-5xxxxx | QUEUED | 20xxxxxxxxxx | |  {"correlationId": "",...} | {'portal_run_id': "",...} | 2024-01-01T00:11:35Z |
|dxxxxx-6xxxx-fxxx-1xxx-5xxxxx | db_uuid | dxxxxx-6xxxx-fxxx-1xxx-5xxxxx | IN_PROGRESS | 20xxxxxxxxxx | |  {"correlationId": "",...} | {'portal_run_id': "",...} | 2024-01-01T00:11:35Z |
|dxxxxx-6xxxx-fxxx-1xxx-5xxxxx | db_uuid | dxxxxx-6xxxx-fxxx-1xxx-5xxxxx | SUCCEEDED | 20xxxxxxxxxx | |  {"correlationId": "",...} | {'portal_run_id': "",...} | 2024-01-01T00:11:35Z |
