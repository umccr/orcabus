update metadata::Specimen
filter .identifier = <str>$specimenId
set {
  libraries += (
    select metadata::Library filter .identifier = <str>$libraryId
  ) 
}
