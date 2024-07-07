# Fastq List Rows to WGTS QC Input Maker

Subscribe to the fastq list rows event, kick off a DraftStateChange for each event with 
the awaiting input status.  

Another step function will then convert these awaiting input statuses' to 'ready'