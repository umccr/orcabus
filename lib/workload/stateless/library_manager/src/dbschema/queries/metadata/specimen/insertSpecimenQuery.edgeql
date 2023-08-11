select (
  with module metadata
  insert Specimen {
    orcaBusId := <str>$orcaBusId,
    internalId := <str>$internalId,
    externalId := <optional str>$externalId,
    source := <optional str>$source,

    subject := (
      select assert_single((
        select Subject filter .orcaBusId = <optional str>$subjectOrcaBusId
      ))
    )
  }
){ 
  *,
  subjectId := .subject.internalId
}
