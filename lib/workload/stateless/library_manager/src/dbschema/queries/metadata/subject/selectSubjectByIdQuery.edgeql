select assert_single((
  select metadata::Subject{ * }
  filter .identifier = <str>$subjectId
))
