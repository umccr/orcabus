
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
        externalIdentifiers: json;
    }

    type Library extending MetadataIdentifiable {
        phenotype: Phenotype;
        workflow: WorkflowTypes;
        quality: Quality;
        type: LibraryTypes;
        assay: str;
        coverage: float32;

        # The backlink to specimens
        multi link specimens_ := .<libraries[is Specimen];
        # The backlink to patients
        multi link subjects_ := .<libraries[is Specimen].<specimens[is Subject];
    }

    type Specimen extending MetadataIdentifiable {
        source: str;
        multi libraries: Library {
            on target delete allow
        };

        # The backlink to patients
        multi link subjects_ := .<specimens[is Subject];

    }

    type Subject extending MetadataIdentifiable {
        multi specimens: Specimen {
            on target delete allow
        };
    }

}
