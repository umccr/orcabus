CREATE MIGRATION m1qzudozq2bkpiohnvi5uwiilcxb4ghit3x6yjdogzqsietfje6b7q
    ONTO m17xfniduooadnu5z2ws7karmivnhmlexiat4ezkld7ialnjvsvh2a
{
  ALTER TYPE metadata::Patient {
      ALTER LINK samples {
          ON TARGET DELETE ALLOW;
      };
  };
  ALTER TYPE metadata::Sample {
      ALTER LINK libraries {
          ON TARGET DELETE ALLOW;
      };
      CREATE MULTI LINK patients_ := (.<samples[IS metadata::Patient]);
  };
  ALTER TYPE metadata::Library {
      CREATE MULTI LINK patients_ := (.<libraries[IS metadata::Sample].<samples[IS metadata::Patient]);
      CREATE MULTI LINK samples_ := (.<libraries[IS metadata::Sample]);
  };
};
