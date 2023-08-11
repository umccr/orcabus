select (
  insert metadata::Subject {
    orcaBusId := <str>$orcaBusId,
    internalId := <str>$internalId,
    externalId := <optional str>$externalId
  }
){ * }
