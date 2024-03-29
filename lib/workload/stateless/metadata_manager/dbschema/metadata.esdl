using extension graphql;
module metadata {
    
    scalar type WorkflowTypes extending enum<'clinical', 'research', 'qc', 'control', 'bcl', 'manual'>;

    # Apparently GraphQL has some trouble on setting enums that containin hyphens 
    # and str startswith number
    # Regex pattern accepted: /^[_a-zA-Z][_a-zA-Z0-9]*$/
    # 
    # scalar type Phenotype extending enum<'normal', 'tumor', 'negative-control'>;
    # scalar type Quality extending enum<'very-poor', 'poor', 'good', 'borderline'>;
    # scalar type LibraryTypes extending enum<
    #     '10X',
    #     'ctDNA',
    #     'ctTSO',
    #     'exome',
    #     'Metagenm',
    #     'MethylSeq',
    #     'other',
    #     'TSO-DNA',
    #     'TSO-RNA',
    #     'WGS',
    #     'WTS',
    #     'BiModal'
    # >;

    abstract type MetadataIdentifiable {
        required orcaBusId: str {
            constraint exclusive on (str_lower(__subject__));
        };
        required internalId: str {
            constraint exclusive on (str_lower(__subject__));
        };
        externalId: str;
    }

    type Library extending MetadataIdentifiable {
        phenotype: str;
        workflow: WorkflowTypes;
        quality: str;
        type: str;
        assay: str;
        coverage: str;

        single link specimen: Specimen {
            on target delete allow
        };

    }

    type Specimen extending MetadataIdentifiable {
        source: str;

        # Defining this to link to a single subject where it is possible to be multiple
        # If from GSheet, how to tell if this specimen change subject OR addition to current one
        single subject: Subject {
            on target delete allow
        };

        # The backlink to all libraries that are connected
        multi link libraries := .<specimen[is Library];
    }

    type Subject extending MetadataIdentifiable {
        # The backlink to the specimens that are connected
        multi link specimens := .<subject[is Specimen];
    }

}
