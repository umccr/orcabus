select (
  with module metadata
  insert metadata::Library {
    orcaBusId := <str>$orcaBusId,
    internalId := <str>$internalId,
    phenotype := <optional str>$phenotype,
    workflow := <optional WorkflowTypes>$workflow,
    quality := <optional str>$quality,
    type := <optional str>$type,
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
