select assert_single((
  select metadata::Specimen{ 
    *,
    subjectId := .subject_.identifier
  }
  filter .identifier = <str>$specimenId
))
