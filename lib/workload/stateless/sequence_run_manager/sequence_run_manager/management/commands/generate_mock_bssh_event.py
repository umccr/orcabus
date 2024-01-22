import json

from django.core.management import BaseCommand

from sequence_run_manager_proc.tests.test_bssh_event import sqs_bssh_event_message


class Command(BaseCommand):
    help = (
        "Generate mock BSSH SQS event in JSON format for local development and testing"
    )

    def handle(self, *args, **options):
        print(json.dumps(sqs_bssh_event_message()))
