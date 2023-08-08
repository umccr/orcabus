CREATE MIGRATION m1zoeax2rbkp3v7to2iasbi7yluj3gxfythru5wkz4xomyrl55zicq
    ONTO m1qzudozq2bkpiohnvi5uwiilcxb4ghit3x6yjdogzqsietfje6b7q
{
  ALTER TYPE metadata::Library {
      DROP LINK patients_;
  };
  ALTER TYPE metadata::Sample {
      DROP LINK patients_;
  };
  ALTER TYPE metadata::Patient RENAME TO metadata::Subject;
  ALTER TYPE metadata::Library {
      CREATE MULTI LINK subjects_ := (.<libraries[IS metadata::Sample].<samples[IS metadata::Subject]);
  };
  ALTER TYPE metadata::Sample {
      CREATE MULTI LINK subjects_ := (.<samples[IS metadata::Subject]);
  };
};
