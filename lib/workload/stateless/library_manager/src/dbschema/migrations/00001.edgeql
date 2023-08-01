CREATE MIGRATION m17xfniduooadnu5z2ws7karmivnhmlexiat4ezkld7ialnjvsvh2a
    ONTO initial
{
  CREATE MODULE audit IF NOT EXISTS;
  CREATE MODULE metadata IF NOT EXISTS;
  CREATE ABSTRACT TYPE metadata::MetadataIdentifiable {
      CREATE PROPERTY externalIdentifiers: array<tuple<system: std::str, value: std::str>>;
      CREATE REQUIRED PROPERTY identifier: std::str {
          CREATE CONSTRAINT std::exclusive ON (std::str_lower(__subject__));
      };
  };
  CREATE SCALAR TYPE metadata::LibraryTypes EXTENDING enum<`10X`, ctDNA, ctTSO, exome, Metagenm, MethylSeq, other, `TSO-DNA`, `TSO-RNA`, WGS, WTS, BiModal>;
  CREATE SCALAR TYPE metadata::Phenotype EXTENDING enum<normal, tumor, `negative-control`>;
  CREATE SCALAR TYPE metadata::Quality EXTENDING enum<`very-poor`, poor, good, borderline>;
  CREATE SCALAR TYPE metadata::WorkflowTypes EXTENDING enum<clinical, research, qc, control, bcl, manual>;
  CREATE TYPE metadata::Library EXTENDING metadata::MetadataIdentifiable {
      CREATE PROPERTY assay: std::str;
      CREATE PROPERTY coverage: std::float32;
      CREATE PROPERTY phenotype: metadata::Phenotype;
      CREATE PROPERTY quality: metadata::Quality;
      CREATE PROPERTY type: metadata::LibraryTypes;
      CREATE PROPERTY workflow: metadata::WorkflowTypes;
  };
  CREATE TYPE metadata::Sample EXTENDING metadata::MetadataIdentifiable {
      CREATE MULTI LINK libraries: metadata::Library;
      CREATE PROPERTY source: std::str;
  };
  CREATE TYPE metadata::Patient EXTENDING metadata::MetadataIdentifiable {
      CREATE MULTI LINK samples: metadata::Sample;
  };
  CREATE SCALAR TYPE audit::ActionOutcome EXTENDING enum<fatal, error, warning, information, success>;
  CREATE SCALAR TYPE audit::ActionType EXTENDING enum<C, R, U, D, E>;
  CREATE ABSTRACT TYPE audit::AuditEvent {
      CREATE REQUIRED PROPERTY actionCategory: audit::ActionType;
      CREATE REQUIRED PROPERTY actionDescription: std::str;
      CREATE REQUIRED PROPERTY actionOutcome: audit::ActionOutcome;
      CREATE PROPERTY details: std::json;
      CREATE REQUIRED PROPERTY inProgress: std::bool;
      CREATE REQUIRED PROPERTY occurredDateTime: std::datetime {
          SET default := (std::datetime_current());
      };
      CREATE REQUIRED PROPERTY occurredDuration: std::duration;
      CREATE REQUIRED PROPERTY recordedDateTime: std::datetime {
          SET default := (std::datetime_current());
          SET readonly := true;
      };
      CREATE REQUIRED PROPERTY updatedDateTime: std::datetime {
          CREATE REWRITE
              INSERT 
              USING (std::datetime_of_statement());
          CREATE REWRITE
              UPDATE 
              USING (std::datetime_of_statement());
      };
      ALTER PROPERTY occurredDuration {
          CREATE REWRITE
              INSERT 
              USING (SELECT
                  (__subject__.occurredDateTime - __subject__.recordedDateTime)
              );
          CREATE REWRITE
              UPDATE 
              USING (SELECT
                  (__subject__.occurredDateTime - __subject__.recordedDateTime)
              );
      };
  };
  CREATE TYPE audit::SystemAuditEvent EXTENDING audit::AuditEvent;
};
