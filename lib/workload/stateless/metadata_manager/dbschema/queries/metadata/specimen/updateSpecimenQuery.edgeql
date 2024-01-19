select assert_single((
  with module metadata
  update Specimen
  filter 
    .orcaBusId = <optional str>$orcaBusId
  set {
    internalId := <optional str>$internalId,
    externalId := <optional str>$externalId,
    source := <optional str>$source,

    subject := (
      select assert_single((
        select Subject filter .orcaBusId = <optional str>$subjectOrcaBusId 
      ))
    )
  }
)){ 
  *,
  subjectId := .subject.internalId
}
