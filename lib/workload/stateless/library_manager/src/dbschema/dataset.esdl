
module dataset {

    abstract type DatasetBase {

      trigger log_update after update for each do (
        insert log::DatasetBase {
          action := 'update',
          target := __new__,
          updated := datetime_of_statement()
        }
      );

    }

    function extractIdentifierValue(i: tuple<system: str, value: str>)-> str
      using (i.value);

    # a abstract type that represents a location to store identifiers for
    # each part of a dataset

    abstract type DatasetIdentifiable {
        required identifiers: array<tuple<system: str, value: str>>;
    }


    # the main data type that represents a collection of genomic data
    # collected from an organisation/study

    type Dataset extending DatasetIdentifiable, DatasetBase {

        required uri: str {
            readonly := true;
            constraint exclusive on (str_lower(__subject__));
        }

        required description: str;

        multi cases: DatasetCase {
            on source delete delete target;
            on target delete allow;
            constraint exclusive;
        };

    }


    # the case wraps up all items that are part of a single unit/record of study
    # this will often be a 'no-op' wrapper - without its own identifiers
    # but for instance, for a family case this might have the family identifiers
;.
    type DatasetCase extending DatasetIdentifiable {

        # the backlink to the dataset that owns us
        link dataset := .<cases[is Dataset];

        multi patients: DatasetPatient {
            on source delete delete target;
            on target delete allow;
            constraint exclusive;
        }

    }

    scalar type SexAtBirthType extending enum<'male', 'female', 'other'>;

    # the patient represents a single human who may have attached specimens

    type DatasetPatient extending DatasetIdentifiable {

         sexAtBirth: SexAtBirthType;

        # the backlink to the dataset that owns us
        link dataset := .<patients[is DatasetCase].<cases[is Dataset];

        multi specimens: DatasetSpecimen {
            on source delete delete target;
            on target delete allow;
            constraint exclusive;
        }
    }

    # the specimen represents the source biological material inputted to the
    # sequencing performed on an individual

    type DatasetSpecimen extending DatasetIdentifiable {

         sampleType: str;

        # the backlink to the dataset that owns us
        link dataset := .<specimens[is DatasetPatient].<patients[is DatasetCase].<cases[is Dataset];

        # the backlink to the case that owns us
        link case_ := .<specimens[is DatasetPatient].<patients[is DatasetCase];

        # the backlink to the patient that owns us
        link patient := .<specimens[is DatasetPatient];

        # the specimen links to all actual genomic artifacts (files) that have been
        # created in any lab process
        multi artifacts: lab::ArtifactBase;
    }
}
