package main

import (
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/aws/aws-secretsmanager-caching-go/secretcache"
	"github.com/umccr/orcabus/lib/workload/stateless/stacks/fmannotator"
)

var (
	secretCache, _ = secretcache.New()
)

// Handler for the portalrunidqueue function.
func Handler() error {
	config, token, err := fmannotator.LoadCachedConfig(secretCache)
	if err != nil {
		return err
	}

	return fmannotator.PortalRunIdQueue(config, token)
}

func main() {
	lambda.Start(Handler)
}
