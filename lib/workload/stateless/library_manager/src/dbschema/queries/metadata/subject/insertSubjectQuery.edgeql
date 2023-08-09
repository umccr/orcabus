select (
  insert metadata::Subject {
    identifier := <str>$subjectId,
    externalIdentifiers := <optional json>$externalIdentifiers
  }
){ * }
