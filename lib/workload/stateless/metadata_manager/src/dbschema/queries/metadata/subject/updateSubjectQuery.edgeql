select assert_single((
  update metadata::Subject
  filter 
    .orcaBusId = <optional str>$orcaBusId
  set {
    internalId := <optional str>$internalId,
    externalId := <optional str>$externalId
  }
)){ 
  *,
  specimenIds := .specimens.orcaBusId
}
