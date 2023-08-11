select assert_single((
  select metadata::Library{ 
    *,
    specimenId := .specimen.internalId 
  }
  filter .internalId = <str>$libraryId
))
