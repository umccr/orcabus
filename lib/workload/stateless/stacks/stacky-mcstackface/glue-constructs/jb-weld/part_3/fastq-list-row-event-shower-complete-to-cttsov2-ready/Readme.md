# Fastq List Row Event Shower Complete to cttsov2 submission

## Description

We assume we have collected all the fastq list row events for a given instrument run that
map to library ids.  

We will use the fastq list row events to generate a cttsov2 submission for every
library id in the instrument run id that is a v2 assay.  

To complete this we will need to 

1. Get the library ids for the instrument run id
2. Find the corresponding fastq list rows for the library ids
3. Find the corresponding bclconvert data sections and tso500l data sections
4. Generate the cttsov2 samplesheet in dictionary format (for each sample)
5. Push a 'awaiting input' event for each library id, containing:
   * A list of fastq list rows,
   * A samplesheet
   * A library id (or the sample id in this case)
6. The cttsov2 service will then generate the cttsov2 workflow for each library id
