package workflowrunstatechange

import (
	"time"
)

// EventBridge custom event schema for orcabus.workflowmanager@WorkflowRunStateChange
type Event struct {
	Account    string                 `json:"account,omitempty"`
	Detail     WorkflowRunStateChange `json:"detail,omitempty"`
	DetailType string                 `json:"detail-type,omitempty"`
	Id         string                 `json:"id,omitempty"`
	Region     string                 `json:"region,omitempty"`
	Resources  []string               `json:"resources,omitempty"`
	Source     string                 `json:"source,omitempty"`
	Time       time.Time              `json:"time,omitempty"`
	Version    string                 `json:"version,omitempty"`
}

func (e *Event) SetAccount(account string) {
	e.Account = account
}

func (e *Event) SetDetail(detail WorkflowRunStateChange) {
	e.Detail = detail
}

func (e *Event) SetDetailType(detailType string) {
	e.DetailType = detailType
}

func (e *Event) SetId(id string) {
	e.Id = id
}

func (e *Event) SetRegion(region string) {
	e.Region = region
}

func (e *Event) SetResources(resources []string) {
	e.Resources = resources
}

func (e *Event) SetSource(source string) {
	e.Source = source
}

func (e *Event) SetTime(time time.Time) {
	e.Time = time
}

func (e *Event) SetVersion(version string) {
	e.Version = version
}
