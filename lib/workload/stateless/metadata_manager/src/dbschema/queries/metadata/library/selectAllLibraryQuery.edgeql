
with

  # Pagination parameter
  offset_ := <optional int16>$offset ?? 0,
  limit_ := <optional int16>$limit ?? 10,

  libraries := (
    select metadata::Library {
      *
    }
    filter ( 
      .orcaBusId ?= <optional str>$orcaBusId ?? .orcaBusId
        AND
      .internalId ?= <optional str>$internalId ?? .internalId
        AND
      .externalId ?= <optional str>$externalId ?? .externalId
        AND
      .phenotype ?= <optional str>$phenotype ?? .phenotype
        AND
      .assay ?= <optional str>$assay ?? .assay
        AND
      .coverage ?= <optional str>$coverage ?? .coverage
        AND
      .quality ?= <optional str>$quality ?? .quality
        AND
      .type ?= <optional str>$type ?? .type
        AND
      .workflow = <optional metadata::WorkflowTypes>$workflow ?? .workflow
    )
  )
select {

  results := (
    select libraries {
      *
    }
    offset offset_
    limit limit_
  ),
  pagination := {
    total := count(libraries),
    `offset` := offset_,
    `limit` := limit_
  }

}

