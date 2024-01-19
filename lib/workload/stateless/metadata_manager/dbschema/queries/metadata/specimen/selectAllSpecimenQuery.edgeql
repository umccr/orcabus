with

  # Pagination parameter
  offset_ := <optional int16>$offset ?? 0,
  limit_ := <optional int16>$limit ?? 10,

  libraries := (
    select metadata::Specimen {
      *
    }
    filter ( 
      .orcaBusId ?= <optional str>$orcaBusId ?? .orcaBusId
        AND
      .internalId ?= <optional str>$internalId ?? .internalId
        AND
      .externalId ?= <optional str>$externalId ?? .externalId
        AND
      .source ?= <optional str>$source ?? .source
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

