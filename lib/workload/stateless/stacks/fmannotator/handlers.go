// Package fmannotator Lambda handler implementations.
package fmannotator

import (
	"bytes"
	"context"
	"fmt"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/sqs"
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

// PortalRunIdQueue Annotate the portalRunId by receiving messages from an SQS queue.
func PortalRunIdQueue(annotatorConfig *Config, token string) (err error) {
	ctx := context.Background()
	sdkConfig, err := config.LoadDefaultConfig(ctx)
	if err != nil {
		return err
	}
	sqsClient := Sqs{
		sqs.NewFromConfig(sdkConfig),
	}

	messages, err := sqsClient.GetMessages(ctx, annotatorConfig.QueueName, annotatorConfig.QueueMaxMessages, annotatorConfig.QueueWaitTimeSecs)
	if err != nil {
		return err
	}

	for _, message := range messages {
		err := PortalRunId(message, annotatorConfig, token)
		if err != nil {
			return err
		}
	}

	return nil
}
