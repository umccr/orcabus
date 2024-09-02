package main

import (
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/umccr/orcabus/lib/workload/stateless/stacks/fmannotator"
)

func main() {
	lambda.Start(fmannotator.Handler)
}
