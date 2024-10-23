// Package fmannotator Lambda handler implementations.
package fmannotator

import (
	"bytes"
	"fmt"
	"github.com/umccr/orcabus/lib/workload/stateless/stacks/fmannotator/schema/orcabus_workflowmanager/workflowrunstatechange"
	"log/slog"
	"net/url"
	"strings"
)

// PortalRunId Annotate the portalRunId from an incoming WorkflowRunStateChange event using the config and FM endpoint token.
func PortalRunId(event workflowrunstatechange.Event, config *Config, token string) (err error) {
	eventStatus := strings.ToUpper(event.Detail.Status)
	if eventStatus != "SUCCEEDED" && eventStatus != "FAILED" && eventStatus != "ABORTED" {
		return nil
	}

	patch, err := MarshallPortalRunId(&event)
	if err != nil {
		return err
	}

	req, err := NewApiClient(config, bytes.NewBuffer(patch))
	if err != nil {
		return err
	}

	req = req.WithMethod("PATCH").WithS3Endpoint().WithQuery(url.Values{
		"currentState": {"false"},
		"key":          {fmt.Sprintf("*/%v/*", event.Detail.PortalRunId)},
	}).WithHeader("Content-Type", "application/json").WithHeader("Authorization", fmt.Sprintf("Bearer %s", token))

	body, status, err := req.Do()
	if err != nil {
		return err
	}
	if status != 200 {
		return fmt.Errorf("error annotating attributes with status %v: %v", status, string(body))
	}

	slog.Debug(fmt.Sprintf("received response %v with body: %v", status, body))

	return nil
}
