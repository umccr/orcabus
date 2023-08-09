select assert_single((
  select metadata::Library{ ** }
  filter .identifier = <str>$libraryId
))
