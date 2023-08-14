select assert_single((
  with module metadata
  update Library
  filter 
    .orcaBusId = <optional str>$orcaBusId
  set {
    internalId := <optional str>$internalId ?? .internalId,

    phenotype := <optional Phenotype>$phenotype ?? .phenotype,
    workflow := <optional WorkflowTypes>$workflow ?? .workflow,
    quality := <optional Quality>$quality ?? .quality,
    type := <optional LibraryTypes>$type ?? .type,
    assay := <optional str>$assay ?? .assay,
    coverage := <optional decimal>$coverage ?? .coverage,

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
