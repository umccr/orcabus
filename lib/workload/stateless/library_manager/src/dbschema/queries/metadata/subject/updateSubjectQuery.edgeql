select assert_single((
  update metadata::Subject
  filter 
    .orcaBusId = <optional str>$orcaBusId
  set {
    internalId := <optional str>$internalId ?? .internalId,
    externalId := <optional str>$externalId ?? .externalId
  }
)){ 
  *,
  specimenIds := .specimens.orcaBusId
}
