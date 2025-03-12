# Fastq Glue

The fastq glue service is a simple tool that connects the fastq manager to the automation pipeline processes. 

## Starting BCLConvert

The first interaction the fastq glue service has with the automation is when the sequence run manager registers a samplesheet.  

The fastq glue service then collects the samplesheet and generates fastq sets and fastq list rows for each sample in the samplesheet.

The fastq glue service then also creates a final event with 'FastqsCreated' with an instrument run id in the detail.

Workflow glue services can then query the fastq manager for any fastq sets of interest an 'initiate' the fastq process 

## Post BSSH Fastq Copy

Once the bssh fastq copy service has completed and the fastq data is now in our BYOB bucket, the fastq glue service then performs the following.

1. Adds read sets to the fastq list rows by querying the fastq_list.csv in the instrument run id output directory.
2. Triggers qc processes endpoint for each fastq list row in the instrument run. 
3. Triggers the file compression information endpoint for each fastq list row.
4. Triggers the ntsm information endpoint for each fastq list row


