select assert_single((
  with module metadata
  update Library
  filter 
    .orcaBusId = <optional str>$orcaBusId
  set {
    internalId := <optional str>$internalId,

    phenotype := <optional str>$phenotype,
    workflow := <optional WorkflowTypes>$workflow,
    quality := <optional str>$quality,
    type := <optional str>$type,
    assay := <optional str>$assay,
    coverage := <optional str>$coverage,

    specimen := (
      select assert_single((
        select Specimen filter .orcaBusId = <optional str>$specimenOrcaBusId
      ))
    )
  }
)){ 
  *,
  specimenId := .specimen.internalId
}
