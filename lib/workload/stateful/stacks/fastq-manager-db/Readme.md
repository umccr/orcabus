# Fastq Manager DB

This comprises three dynamodb table that stores the metadata of fastq files. 

The tables are:
* fastq list row
* fastq set
* jobs

The fastq list row table is indexed by the id with the following global secondary indexes:
  * rgid_ext (the read group id, plus the instrument run id)
  * instrument_run_id (the instrument run id)
  * library_id (the library orcabus id)
  * fastq_set_id (easier to find the corresponding set object)

The fastq set table is indexed by the id with the following global secondary indexes:
  * library_id (the library orcabus id)

The jobs table is indexed by the id with the following global secondary indexes:
  * fastq_set_id (the fastq set id)
  * status (the status of the job)

