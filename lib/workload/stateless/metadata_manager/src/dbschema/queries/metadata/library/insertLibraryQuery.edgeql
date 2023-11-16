select (
  with module metadata
  insert metadata::Library {
    orcaBusId := <str>$orcaBusId,
    internalId := <str>$internalId,
    phenotype := <optional Phenotype>$phenotype,
    workflow := <optional WorkflowTypes>$workflow,
    quality := <optional Quality>$quality,
    type := <optional LibraryTypes>$type,
    assay := <optional str>$assay,
    coverage := <optional decimal>$coverage,

    specimen := (
      select assert_single((
        select Specimen filter .orcaBusId = <optional str>$specimenOrcaBusId
      ))
    )
  }
){ 
  *,
  specimenId := .specimen.internalId
}
