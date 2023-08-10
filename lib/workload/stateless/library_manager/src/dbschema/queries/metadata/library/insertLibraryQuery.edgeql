select (
  with module metadata
  insert metadata::Library {
    identifier := <str>$identifier,
    phenotype := <optional Phenotype>$phenotype,
    workflow := <optional WorkflowTypes>$workflow,
    quality := <optional Quality>$quality,
    type := <optional LibraryTypes>$type,
    assay := <optional str>$assay,
    coverage := <optional decimal>$coverage
  }
){ * }
