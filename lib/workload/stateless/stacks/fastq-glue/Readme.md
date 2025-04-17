# Fastq Glue

The fastq glue service is a simple tool that connects the fastq manager to the automation pipeline processes. 


## Post BSSH Fastq Copy 

* Once the bssh fastq copy service has completed and the fastq data is now in our BYOB bucket, 
  the fastq glue service then performs the following:
    * Generates the fastq sets for each sample in the samplesheet
    * Raises an event to say all fastq sets for this instrument run id have been created

## Future work

* With the new sequence run manager, there is scope to generate the fastq sets prior to the data existing in our cache bucket. 
* We could then 'prime' the analysis manager for samples that are to arrive in the next few hours.  This has the following benefits:
  * Any somatic data with a complementary normal fastq in archive could be signalled to be unarchived. 
  * We may be able to examine the analyses that are triggered prior to being actually run to confirm that they are correct.

