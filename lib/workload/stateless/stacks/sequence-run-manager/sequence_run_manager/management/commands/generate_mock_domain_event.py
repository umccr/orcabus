import json

from django.core.management import BaseCommand, CommandParser
from django.db.models import QuerySet

from sequence_run_manager.models import Sequence
from sequence_run_manager.tests.factories import TestConstant, SequenceFactory
from sequence_run_manager_proc.domain.sequence import SequenceDomain
from sequence_run_manager_proc.domain.sequencerunstatechange import Marshaller


class Command(BaseCommand):
    help = "Generate mock Sequence domain event for local development and testing"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            "--domain",
            help="Deserialized form of Sequence entity in SequenceRunStateChange",
            action="store_true",
        )
        parser.add_argument(
            "--envelope",
            help="SequenceRunStateChange wrap in AWSEvent envelope",
            action="store_true",
        )
        parser.add_argument(
            "--boto", help="AWSEvent to Boto PutEvent API envelope", action="store_true"
        )

    def handle(self, *args, **options):
        opt_domain = options["domain"]
        opt_with_envelope = options["envelope"]
        opt_with_boto_envelope = options["boto"]

        qs: QuerySet = Sequence.objects.filter(
            sequence_run_id=TestConstant.sequence_run_id.value
        )
        if not qs.exists():
            mock_sequence: Sequence = SequenceFactory()
        else:
            mock_sequence: Sequence = qs.get()

        mock_sequence_domain = SequenceDomain(
            sequence=mock_sequence, status_has_changed=True, state_has_changed=True
        )

        if opt_domain:
            print(json.dumps(Marshaller.marshall(mock_sequence_domain.to_event())))
            exit(0)

        if opt_with_envelope:
            print(
                json.dumps(
                    Marshaller.marshall(mock_sequence_domain.to_event_with_envelope())
                )
            )
            exit(0)

        if opt_with_boto_envelope:
            print(
                json.dumps(
                    Marshaller.marshall(
                        mock_sequence_domain.to_put_events_request_entry(
                            event_bus_name="MockBus"
                        )
                    )
                )
            )
            exit(0)

        print(json.dumps(Marshaller.marshall(mock_sequence_domain.to_event())))
