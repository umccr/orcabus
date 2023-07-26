CREATE MIGRATION m1xcbrad4sfh56yjhuxuezbhk26dwktnll5nlrlggp24rjv6jajoxq
    ONTO initial
{
  CREATE MODULE log IF NOT EXISTS;
  CREATE MODULE metadata IF NOT EXISTS;
  CREATE ABSTRACT TYPE metadata::MetadataIdentifiable {
      CREATE PROPERTY externalIdentifiers: array<tuple<system: std::str, value: std::str>>;
      CREATE REQUIRED PROPERTY identifier: std::str {
          CREATE CONSTRAINT std::exclusive ON (std::str_lower(__subject__));
      };
  };
  CREATE SCALAR TYPE metadata::Quality EXTENDING enum<veryPoor, poor, good, borderline>;
  CREATE SCALAR TYPE metadata::WorkflowTypes EXTENDING enum<clinical, research, qc, control, bcl, manual>;
  CREATE TYPE metadata::Library EXTENDING metadata::MetadataIdentifiable {
      CREATE PROPERTY coverage: std::float32;
      CREATE PROPERTY overrideCycles: std::str;
      CREATE PROPERTY quality: metadata::Quality;
      CREATE PROPERTY runNumber: std::str;
      CREATE PROPERTY truseqindex: std::str;
      CREATE PROPERTY workflow: metadata::WorkflowTypes;
  };
  CREATE SCALAR TYPE metadata::Phenotype EXTENDING enum<normal, tumor, `negative-control`>;
  CREATE TYPE metadata::Sample EXTENDING metadata::MetadataIdentifiable {
      CREATE MULTI LINK libraries: metadata::Library;
      CREATE PROPERTY assay: std::str;
      CREATE PROPERTY phenotype: metadata::Phenotype;
      CREATE PROPERTY projectName: std::str;
      CREATE PROPERTY projectOwner: std::str;
      CREATE PROPERTY source: std::str;
  };
  CREATE TYPE metadata::Patient EXTENDING metadata::MetadataIdentifiable {
      CREATE MULTI LINK samples: metadata::Sample;
  };
  CREATE SCALAR TYPE metadata::ExperimentTypes EXTENDING enum<`10X`, ctDNA, ctTSO, exome, Metagenm, MethylSeq, other, `TSO-DNA`, `TSO-RNA`, WGS, WTS, BiModal>;
  CREATE TYPE metadata::Experiment EXTENDING metadata::MetadataIdentifiable {
      CREATE MULTI LINK patients: metadata::Patient;
      CREATE PROPERTY type: metadata::ExperimentTypes;
  };
  CREATE ABSTRACT TYPE metadata::MetadataLoggable;
  CREATE SCALAR TYPE log::Action EXTENDING enum<`INSERT`, `UPDATE`, `DELETE`>;
  CREATE TYPE log::Metadata {
      CREATE LINK object: metadata::MetadataLoggable {
          ON TARGET DELETE ALLOW;
      };
      CREATE REQUIRED PROPERTY action: log::Action;
      CREATE PROPERTY detail: std::json;
      CREATE REQUIRED PROPERTY updatedTime: std::datetime;
  };
};
