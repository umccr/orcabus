package main

import (
	"encoding/json"
	"fmt"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/umccr/orcabus/lib/workload/stateless/stacks/attribute-linker/schema/orcabus_workflowmanager/workflowrunstatechange"
)

func handler(event workflowrunstatechange.Event) (string, error) {
	b, err := json.Marshal(event)
	a := string(b)
	fmt.Println(a)
	return a, err
}

func main() {
	lambda.Start(handler)
}
