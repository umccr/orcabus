# NF Batch ready event handler

Use this component to wrap a pipeline manager 
and handle the NF Batch ready event to submission to the nextflow pipeline.  

Expects a lambda from the custom nf event that produces the inputs for the batch submission job.  

Writes to the database the job id.  

