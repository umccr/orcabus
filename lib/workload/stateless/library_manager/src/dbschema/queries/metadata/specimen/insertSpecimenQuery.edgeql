select (
  insert metadata::Specimen {
    identifier := <str>$specimenId,
    externalIdentifiers := <optional json>$externalIdentifiers,
    source := <optional str>$source
  }
){ * }
