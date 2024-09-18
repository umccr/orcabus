import django

from fastq_manager.models import FastqPair

django.setup()

# --- keep ^^^ at top of the module

from libumccr import libjson
from fastq_manager_proc.services import fastq_pair_srv


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
    # TODO: define what a reasonable event would look like
    {
        "rgid": "1234",
        "rgsm": "sample1",
        "rglb": "L000001",
        "read_1_id": "file.1234.r1",
        "read_2_id": "file.1234.r2"
    }
    """
    print(f"Processing {event}, {context}")

    fastq_pair = FastqPair(
        rgid=event["rgid"],
        rgsm=event["rgsm"],
        rglb=event["rglb"],
        read_1_id=event["read_1_id"],
        read_2_id=event["read_2_id"]
    )
    fastq_pair.save()

    print(f"FastqPair > {fastq_pair}")

    response = {
        "fastq_pair": fastq_pair
    }
    return response
