package workflowrunstatechange

import (
	"time"
)

type WorkflowRunStateChange struct {
	LinkedLibraries []LibraryRecord `json:"linkedLibraries,omitempty"`
	Payload         Payload         `json:"payload,omitempty"`
	PortalRunId     string          `json:"portalRunId,omitempty"`
	Status          string          `json:"status,omitempty"`
	Timestamp       time.Time       `json:"timestamp,omitempty"`
	WorkflowName    string          `json:"workflowName,omitempty"`
	WorkflowRunName string          `json:"workflowRunName,omitempty"`
	WorkflowVersion string          `json:"workflowVersion,omitempty"`
}

func (w *WorkflowRunStateChange) SetLinkedLibraries(linkedLibraries []LibraryRecord) {
	w.LinkedLibraries = linkedLibraries
}

func (w *WorkflowRunStateChange) SetPayload(payload Payload) {
	w.Payload = payload
}

func (w *WorkflowRunStateChange) SetPortalRunId(portalRunId string) {
	w.PortalRunId = portalRunId
}

func (w *WorkflowRunStateChange) SetStatus(status string) {
	w.Status = status
}

func (w *WorkflowRunStateChange) SetTimestamp(timestamp time.Time) {
	w.Timestamp = timestamp
}

func (w *WorkflowRunStateChange) SetWorkflowName(workflowName string) {
	w.WorkflowName = workflowName
}

func (w *WorkflowRunStateChange) SetWorkflowRunName(workflowRunName string) {
	w.WorkflowRunName = workflowRunName
}

func (w *WorkflowRunStateChange) SetWorkflowVersion(workflowVersion string) {
	w.WorkflowVersion = workflowVersion
}
