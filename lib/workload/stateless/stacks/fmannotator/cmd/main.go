package main

import (
	"fmt"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/aws/aws-secretsmanager-caching-go/secretcache"
	"github.com/umccr/orcabus/lib/workload/stateless/stacks/fmannotator"
	"github.com/umccr/orcabus/lib/workload/stateless/stacks/fmannotator/schema/orcabus_workflowmanager/workflowrunstatechange"
	"log/slog"
)

var (
	secretCache, _ = secretcache.New()
)

func Handler(event workflowrunstatechange.Event) error {
	config, err := fmannotator.LoadConfig()
	if err != nil {
		return err
	}

	token, err := secretCache.GetSecretString(config.FileManagerSecret)
	if err != nil {
		return err
	}

	slog.Info(fmt.Sprintf("token is: %v", token))

	return fmannotator.Handler(event, &config, token)
}

func main() {
	lambda.Start(Handler)
}
