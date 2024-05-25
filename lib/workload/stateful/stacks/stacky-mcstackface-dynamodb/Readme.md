# Stacky McStackFace MetadataManager Dynamo Db

The dynamo db service that stores the hacky metadata manager

We have various id types

## Instrument Run Manager

* id: Instrument Run ID
* id_type: Partition Table Name
* samplesheet_dict: The samplesheet dictionary
* fastq_list_row_dict: The fastq list rows

## Workflow Manager

* Records Translated Events

* id: refId
* id_type: The name of the translation event
* event_detail_input: The input event detail
* event_detail_output: The event detail of the translated event

## Glue Manager

* Records Input Maker Creation Jobs by Glue Constructs 

* id: refId
* id_type: The name of the input maker glue construct
* event_data_input: The input event data
* event_data_output: The output event data
* portal_run_id: The portal run id generated for the ready event
* workflow_run_name: The workflow run name generated for the ready event