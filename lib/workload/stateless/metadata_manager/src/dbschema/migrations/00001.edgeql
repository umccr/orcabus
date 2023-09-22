CREATE MIGRATION m1yeshjmmmg2k6sw3jahas6todmhmhxzzor3ktnkondv6sp57bshka
    ONTO initial
{
  CREATE EXTENSION graphql VERSION '1.0';
  CREATE MODULE audit IF NOT EXISTS;
  CREATE MODULE metadata IF NOT EXISTS;
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
  CREATE ABSTRACT TYPE metadata::MetadataIdentifiable {
      CREATE PROPERTY externalId: std::str;
      CREATE REQUIRED PROPERTY internalId: std::str {
          CREATE CONSTRAINT std::exclusive ON (std::str_lower(__subject__));
      };
      CREATE REQUIRED PROPERTY orcaBusId: std::str {
          CREATE CONSTRAINT std::exclusive ON (std::str_lower(__subject__));
      };
  };
  CREATE SCALAR TYPE metadata::WorkflowTypes EXTENDING enum<clinical, research, qc, control, bcl, manual>;
  CREATE TYPE metadata::Library EXTENDING metadata::MetadataIdentifiable {
      CREATE PROPERTY assay: std::str;
      CREATE PROPERTY coverage: std::decimal;
      CREATE PROPERTY phenotype: std::str;
      CREATE PROPERTY quality: std::str;
      CREATE PROPERTY type: std::str;
      CREATE PROPERTY workflow: metadata::WorkflowTypes;
  };
  CREATE TYPE metadata::Specimen EXTENDING metadata::MetadataIdentifiable {
      CREATE PROPERTY source: std::str;
  };
  ALTER TYPE metadata::Library {
      CREATE SINGLE LINK specimen: metadata::Specimen {
          ON TARGET DELETE ALLOW;
      };
  };
  ALTER TYPE metadata::Specimen {
      CREATE MULTI LINK libraries := (.<specimen[IS metadata::Library]);
  };
  CREATE TYPE metadata::Subject EXTENDING metadata::MetadataIdentifiable;
  ALTER TYPE metadata::Specimen {
      CREATE SINGLE LINK subject: metadata::Subject {
          ON TARGET DELETE ALLOW;
      };
  };
  ALTER TYPE metadata::Subject {
      CREATE MULTI LINK specimens := (.<subject[IS metadata::Specimen]);
  };
};
