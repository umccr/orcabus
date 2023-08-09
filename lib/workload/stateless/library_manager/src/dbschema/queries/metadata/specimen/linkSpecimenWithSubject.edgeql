update metadata::Subject
filter .identifier = <str>$subjectId
set {
  specimens += (
    select metadata::Specimen filter .identifier = <str>$specimenId
  ) 
}
