package fmannotator

import (
	"bytes"
	"errors"
	"fmt"
	"github.com/umccr/orcabus/lib/workload/stateless/stacks/fmannotator/schema/orcabus_workflowmanager/workflowrunstatechange"
	"log/slog"
	"net/url"
	"strings"
)

// Handler Handle an incoming WorkflowRunStateChange event using the config and FM endpoint token.
func Handler(event workflowrunstatechange.Event, config *Config, token string) (err error) {
	eventStatus := strings.ToUpper(event.Detail.Status)
	if eventStatus != "SUCCEEDED" && eventStatus != "FAILED" && eventStatus != "ABORTED" {
		return nil
	}

	patch, err := MarshallPortalRunId(&event)
	if err != nil {
		return err
	}

	resp, err := NewApiClient(config, bytes.NewBuffer(patch))
	if err != nil {
		return err
	}

	resp = resp.WithMethod("PATCH").WithS3Endpoint().WithQuery(url.Values{
		"key": {fmt.Sprintf("*%v*", event.Detail.PortalRunId)},
	}).WithHeader("Content-Type", "application/json").WithHeader("Authorization", fmt.Sprintf("Bearer %v", token))
	body, status, err := resp.Do()
	if err != nil {
		return err
	}
	if status != 200 {
		return errors.New(fmt.Sprintf("error annotating attributes with status %v: %v", status, string(body)))
	}

	slog.Debug(fmt.Sprintf("received response %v with body: %v", status, body))

	return nil
}
