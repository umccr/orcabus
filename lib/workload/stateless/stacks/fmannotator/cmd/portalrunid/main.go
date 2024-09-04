package main

import (
	"encoding/json"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/aws/aws-secretsmanager-caching-go/secretcache"
	"github.com/umccr/orcabus/lib/workload/stateless/stacks/fmannotator"
	"github.com/umccr/orcabus/lib/workload/stateless/stacks/fmannotator/schema/orcabus_workflowmanager/workflowrunstatechange"
	"log/slog"
)

const (
	TokenIdField = "id_token"
)

var (
	secretCache, _ = secretcache.New()
)

// Handler for the portalRunId annotator function.
func Handler(event workflowrunstatechange.Event) error {
	level, err := fmannotator.GetLogLevel()
	if err != nil {
		return err
	}
	slog.SetLogLoggerLevel(level)

	config, err := fmannotator.LoadConfig()
	if err != nil {
		return err
	}

	secret, err := secretCache.GetSecretString(config.FileManagerSecretName)
	if err != nil {
		return err
	}

	secretKeys := make(map[string]string)
	err = json.Unmarshal([]byte(secret), &secretKeys)
	if err != nil {
		return err
	}

	return fmannotator.PortalRunId(event, &config, secretKeys[TokenIdField])
}

func main() {
	lambda.Start(Handler)
}
