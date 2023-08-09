select assert_single((
  update metadata::Specimen
  filter .identifier = <str>$specimenId
  set {
    externalIdentifiers := <optional json>$externalIdentifiers,
    source := <optional str>$source
  }
)){ * }
