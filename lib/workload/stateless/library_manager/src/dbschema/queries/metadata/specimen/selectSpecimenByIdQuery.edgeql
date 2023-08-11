select assert_single((
  select metadata::Specimen{ 
    *,
    subjectId := .subject.orcaBusId,
    libraryIds := .libraries.orcaBusId
  }
  filter
      .internalId = <optional str>$internalId
))
