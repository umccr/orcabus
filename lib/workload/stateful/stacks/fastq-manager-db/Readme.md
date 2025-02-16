# Fastq Manager DB

This a single dynamodb table that stores the metadata of fastq files. 

The table is indexed by the id with the following global secondary indexes:
  * rgid_ext (the read group id, plus the instrument run id)
  * instrument_run_id (the instrument run id)
  * library_id (the library orcabus id)


