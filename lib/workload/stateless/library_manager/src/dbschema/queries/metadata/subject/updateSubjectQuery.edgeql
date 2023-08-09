select assert_single((
  update metadata::Subject
  filter .identifier = <str>$subjectId
  set {
    externalIdentifiers := <optional json>$externalIdentifiers
  }
)){ * }
