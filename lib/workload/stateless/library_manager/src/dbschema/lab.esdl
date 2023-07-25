module lab {

    abstract type ArtifactBase  {
    }

    # type ArtifactBcl extending ArtifactBase {
    #     required bclFile: storage::File{
    #         on source delete delete target;
    #     };
    # }

    # type ArtifactFastqPair extending ArtifactBase {
    #     required forwardFile: storage::File{
    #         on source delete delete target;
    #     };
    #     required reverseFile: storage::File{
    #         on source delete delete target;
    #     };
    # }

    # type ArtifactVcf extending ArtifactBase {
    #     # To list sampleIds related for the given VCF
    #     # String of array if contain multiple sampleIds for trios.
    #     sampleIds: array<str>;

    #     required vcfFile: storage::File{
    #         on source delete delete target;
    #     };
    #     required tbiFile: storage::File{
    #         on source delete delete target;
    #     };
    # }

    # type ArtifactBam extending ArtifactBase {
    #     required bamFile: storage::File{
    #         on source delete delete target;
    #     };
    #     required baiFile: storage::File{
    #         on source delete delete target;
    #     };
    # }

    # type ArtifactCram extending ArtifactBase {
    #     required cramFile: storage::File{
    #         on source delete delete target;
    #     };
    #     required craiFile: storage::File{
    #         on source delete delete target;
    #     };
    # }

    # a collection of artifacts uploaded/submitted in a batch that has no information about run/analyses
    type SubmissionBatch {

        # some string of this batch that is unique/meaningful to the provider of the data
        externalIdentifier: str;

        multi artifactsIncluded: ArtifactBase {
            constraint exclusive;
            on source delete delete target;
            on target delete allow;
       };
    }


    # a genomic sequencing run that outputs artifacts
    type Run {
        platform: str;
        runDate: datetime;

        multi artifactsProduced: ArtifactBase {
            constraint exclusive;
            on source delete delete target;
            on target delete allow;
       };
    }

    type Analyses {
        pipeline: str;
        analysesDate: datetime;

        multi input: ArtifactBase;

        multi output: ArtifactBase {
              constraint exclusive;
              on source delete delete target;
              on target delete allow;
        };
    }


}
