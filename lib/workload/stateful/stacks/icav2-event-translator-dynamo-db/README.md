# ICA v2 Event Translator

## This table will record event translator process
Send the orignal input and orcabus event after translation to the dynao db for recording of the process. 

Dynamodb format:
| analysis_id    | event_status | id_type | portal_run_id | original_external_event | translated_internal_ica_event | timestamp |
| -------- | ------- | ------- | ------- | ------- | ------- |------- | 
| dxxxxx-6xxxx-fxxx-1xxx-5xxxxx | PREPARING_INPUTS | analysis_id | 20xxxxxxxxxx | {"correlationId": "",...} | {'portal_run_id': "",...} | 2024-01-01T00:11:35Z |
|dxxxxx-6xxxx-fxxx-1xxx-5xxxxx | SUCCEEDED  | analysis_id | 20xxxxxxxxxx | {"correlationId": "",...} | {'portal_run_id': "",...} | 2024-01-01T00:11:35Z |

