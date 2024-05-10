# BCLConvert Interop QC Pipeline Dynamo Db

The dynamo db service that stores icav2 BCLConvert InteropQc pipeline analyses

Analysis are stored by their portal_run_id, icav2_analysis_id and their database uuid.  

We also capture the timestamp of events in the database to allow for tracking of the analysis state.

