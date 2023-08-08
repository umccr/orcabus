
module metadata {
    
    scalar type Phenotype extending enum<'normal', 'tumor', 'negative-control'>;
    scalar type Quality extending enum<'very-poor', 'poor', 'good', 'borderline'>;
    scalar type WorkflowTypes extending enum<'clinical', 'research', 'qc', 'control', 'bcl', 'manual'>;
    scalar type LibraryTypes extending enum<
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

    type Library extending MetadataIdentifiable {
        phenotype: Phenotype;
        workflow: WorkflowTypes;
        quality: Quality;
        type: LibraryTypes;
        assay: str;
        coverage: float32;

        # The backlink to samples
        multi link samples_ := .<libraries[is Sample];
        # The backlink to patients
        multi link subjects_ := .<libraries[is Sample].<samples[is Subject];
    }

    type Sample extending MetadataIdentifiable {
        source: str;
        multi libraries: Library {
            on target delete allow
        };

        # The backlink to patients
        multi link subjects_ := .<samples[is Subject];

    }

    type Subject extending MetadataIdentifiable {
        multi samples: Sample {
            on target delete allow
        };
    }

}
