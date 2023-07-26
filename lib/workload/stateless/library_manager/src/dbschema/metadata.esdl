
module metadata {

    abstract type MetadataLoggable {
        # This will only copy the id of the `new` object and so changes is not recorded.
        # Might just do a normal copy from the application logic to the logs.
        # Will revisit this - Wil

        # trigger log_update after update for each do (
        #     insert log::Metadata {
        #         action := "UPDATE",
        #         object := __new__,
        #         detail := <json>(select __new__{**}),
        #         updatedTime := datetime_of_statement()
        #     }
        # );

        # trigger log_delete after delete for each do (
        #     insert log::Metadata {
        #         action := 'DELETE',
        #         updatedTime := datetime_of_statement()
        #     }
        # );

        # trigger log_insert after insert for each do (
        #     insert log::Metadata {
        #         action := 'INSERT',
        #         object := __new__,
        #         detail := <json>(select __new__{**}),
        #         updatedTime := datetime_of_statement()
        #     }
        # );
    }

    scalar type Phenotype extending enum<'normal', 'tumor', 'negative-control'>;
    scalar type Quality extending enum<'veryPoor', 'poor', 'good', 'borderline'>;
    scalar type WorkflowTypes extending enum<'clinical','research','qc','control','bcl','manual'>;
    scalar type ExperimentTypes extending enum<
        '10X',
        'ctDNA',
        'ctTSO',
        'exome',
        'Metagenm',
        'MethylSeq',
        'other',
        'TSO-DNA',
        'TSO-RNA',
        'WGS',
        'WTS',
        'BiModal'
    >;

    abstract type MetadataIdentifiable {
        required identifier: str {
            constraint exclusive on (str_lower(__subject__));
        };
        externalIdentifiers: array<tuple<system: str, value: str>>;
    }

    type Library extending MetadataIdentifiable{
        workflow: WorkflowTypes;
        quality: Quality;
        coverage: float32;
        truseqindex: str;
        overrideCycles: str;
        runNumber: str;
    }

    type Sample extending MetadataIdentifiable {
        phenotype: Phenotype;
        source: str;
        assay: str;
        projectOwner: str;
        projectName: str;

        multi libraries: Library;
    }

    type Patient extending MetadataIdentifiable {
        multi samples: Sample;
    }

    type Experiment extending MetadataIdentifiable {
        type: ExperimentTypes;

        multi patients: Patient;
    }

}
