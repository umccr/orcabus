select assert_single((
  select metadata::Specimen{ ** }
  filter .identifier = <str>$specimenId
))
