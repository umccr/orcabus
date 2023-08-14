select assert_single((
  with module metadata
  update Specimen
  filter 
    .orcaBusId = <optional str>$orcaBusId
  set {
    internalId := <optional str>$internalId ?? .internalId,
    externalId := <optional str>$externalId ?? .externalId,
    source := <optional str>$source ?? .source,

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
