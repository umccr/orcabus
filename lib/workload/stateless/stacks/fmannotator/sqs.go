package fmannotator

import (
	"context"
	"encoding/json"
	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/service/sqs"
	"github.com/umccr/orcabus/lib/workload/stateless/stacks/fmannotator/schema/orcabus_workflowmanager/workflowrunstatechange"
)

// Sqs encapsulates the AWS SQS actions.
type Sqs struct {
	SqsClient *sqs.Client
}

// GetMessages uses the ReceiveMessage to get messages from an SQS queue.
func (actor Sqs) GetMessages(ctx context.Context, queueUrl string, maxMessages int32, waitTime int32) ([]workflowrunstatechange.Event, error) {
	var messages []workflowrunstatechange.Event
	result, err := actor.SqsClient.ReceiveMessage(ctx, &sqs.ReceiveMessageInput{
		QueueUrl:            aws.String(queueUrl),
		MaxNumberOfMessages: maxMessages,
		WaitTimeSeconds:     waitTime,
	})
	if err != nil {
		return nil, err
	}

	for _, message := range result.Messages {
		var event workflowrunstatechange.Event
		err := json.Unmarshal([]byte(*message.Body), &event)
		if err != nil {
			return nil, err
		}

		messages = append(messages, event)
	}

	return messages, nil
}
