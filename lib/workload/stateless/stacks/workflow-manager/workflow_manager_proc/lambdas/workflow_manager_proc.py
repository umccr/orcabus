import django

django.setup()

# --- keep ^^^ at top of the module

from libumccr import libjson

from workflow_manager_proc.services import workflow_srv


def sqs_handler(event, context):
    """event payload dict
    {
        'Records': [
            {
                'messageId': "11d6ee51-4cc7-4302-9e22-7cd8afdaadf5",
                'body': "{\"JSON\": \"Formatted Message\"}",
                'messageAttributes': {},
                'md5OfBody': "",
                'eventSource': "aws:sqs",
                'eventSourceARN': "arn:aws:sqs:us-east-2:123456789012:fifo.fifo",
            },
            ...
        ]
    }

    Details event payload dict refer to https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html
    Backing queue is FIFO queue and, guaranteed delivery-once, no duplication.

    :param event:
    :param context:
    :return:
    """
    messages = event['Records']

    results = []
    for message in messages:
        job = libjson.loads(message['body'])
        results.append(handler(job, context))

    return {
        'results': results
    }


def handler(event, context):
    """event payload
    {
        THIS SHOULD TYPICALLY BE BOUND TO RESPECTIVE config/event_schemas
    }
    """
    print(f"Processing {event}, {context}")

    wf = workflow_srv.get_workflow_from_db()
    print(f"Workflow: {wf}")

    response = {
        "Workflow": "Test workflow"
    }
    return response
