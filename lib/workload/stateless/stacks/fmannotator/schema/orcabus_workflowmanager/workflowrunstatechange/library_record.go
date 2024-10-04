package workflowrunstatechange

type LibraryRecord struct {
	LibraryId string `json:"libraryId,omitempty"`
	OrcabusId string `json:"orcabusId,omitempty"`
}

func (l *LibraryRecord) SetLibraryId(libraryId string) {
	l.LibraryId = libraryId
}

func (l *LibraryRecord) SetOrcabusId(orcabusId string) {
	l.OrcabusId = orcabusId
}
