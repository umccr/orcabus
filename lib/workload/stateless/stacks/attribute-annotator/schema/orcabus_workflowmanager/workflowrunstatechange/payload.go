package workflowrunstatechange

type Payload struct {
	Data    interface{} `json:"data,omitempty"`
	RefId   string      `json:"refId,omitempty"`
	Version string      `json:"version,omitempty"`
}

func (p *Payload) SetData(data interface{}) {
	p.Data = data
}

func (p *Payload) SetRefId(refId string) {
	p.RefId = refId
}

func (p *Payload) SetVersion(version string) {
	p.Version = version
}
