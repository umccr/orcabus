select assert_single((
  select metadata::Subject{
    *,
    specimenIds := .specimens.orcaBusId
  }
  filter (
      .internalId = <optional str>$internalId
  )
))
