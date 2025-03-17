import json
from datetime import datetime

from sequence_run_manager.tests.factories import SequenceFactory
from sequence_run_manager_proc.domain.sequence import SequenceDomain
from sequence_run_manager_proc.domain.sequencerunstatechange import (
    Marshaller,
    SequenceRunStateChange,
    AWSEvent,
)
from sequence_run_manager_proc.tests.case import SequenceRunProcUnitTestCase, logger


class SequenceDomainUnitTests(SequenceRunProcUnitTestCase):
    def setUp(self) -> None:
        super(SequenceDomainUnitTests, self).setUp()
    
    def tearDown(self) -> None:
        super(SequenceDomainUnitTests, self).tearDown()

    def test_marshall(self):
        """
        python manage.py test sequence_run_manager_proc.tests.test_sequence_domain.SequenceDomainUnitTests.test_marshall
        """
        mock_sequence = SequenceFactory()
        mock_sequence_domain = SequenceDomain(
            sequence=mock_sequence, state_has_changed=True, status_has_changed=True
        )

        marshalled_object = Marshaller.marshall(mock_sequence_domain.to_event())

        logger.info(marshalled_object)
        logger.info(json.dumps(marshalled_object))
        self.assertIsNotNone(marshalled_object)
        self.assertIsInstance(marshalled_object, dict)
        self.assertIn("id", marshalled_object.keys())
        self.assertIn("instrumentRunId", marshalled_object.keys())

    def test_unmarshall(self):
        """
        python manage.py test sequence_run_manager_proc.tests.test_sequence_domain.SequenceDomainUnitTests.test_unmarshall
        """
        mock_sequence = SequenceFactory()
        mock_sequence_domain = SequenceDomain(
            sequence=mock_sequence, state_has_changed=True, status_has_changed=True
        )

        marshalled_object = Marshaller.marshall(mock_sequence_domain.to_event())

        unmarshalled_object = Marshaller.unmarshall(
            data=marshalled_object, typeName=mock_sequence_domain.event_type
        )

        logger.info(unmarshalled_object)
        self.assertIsNotNone(unmarshalled_object)
        self.assertIsInstance(unmarshalled_object, object)
        self.assertIsInstance(unmarshalled_object, SequenceRunStateChange)
        self.assertIsInstance(unmarshalled_object.startTime, datetime)

    def test_aws_event_serde(self):
        """
        python manage.py test sequence_run_manager_proc.tests.test_sequence_domain.SequenceDomainUnitTests.test_aws_event_serde
        """
        mock_sequence = SequenceFactory()
        mock_sequence_domain = SequenceDomain(
            sequence=mock_sequence, state_has_changed=True, status_has_changed=True
        )

        aws_event = mock_sequence_domain.to_event_with_envelope()

        logger.info(aws_event)
        logger.info(json.dumps(Marshaller.marshall(aws_event)))
        self.assertIsNotNone(aws_event)
        self.assertIsInstance(aws_event, AWSEvent)

    def test_put_events_request_entry(self):
        """
        python manage.py test sequence_run_manager_proc.tests.test_sequence_domain.SequenceDomainUnitTests.test_put_events_request_entry
        """
        mock_sequence = SequenceFactory()
        mock_sequence_domain = SequenceDomain(
            sequence=mock_sequence, state_has_changed=True, status_has_changed=True
        )

        mock_entry = mock_sequence_domain.to_put_events_request_entry(
            event_bus_name="MockBus",
        )
        logger.info(mock_entry)

        self.assertIsNotNone(mock_entry)
        self.assertIsInstance(mock_entry, dict)
        self.assertIn("Detail", mock_entry.keys())
        self.assertIsInstance(mock_entry["Detail"], str)
        self.assertIsInstance(mock_entry["DetailType"], str)

        mock_entry_detail = json.loads(mock_entry["Detail"])
        logger.info(mock_entry_detail)
        self.assertIsInstance(mock_entry_detail, dict)

        unmarshalled_detail = Marshaller.unmarshall(
            data=mock_entry_detail, typeName=SequenceRunStateChange
        )
        logger.info(unmarshalled_detail)
        self.assertIsInstance(unmarshalled_detail, SequenceRunStateChange)
