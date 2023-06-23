import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from libumccr import libjson
from libumccr.aws import libssm

from sequence_run_manager.models import Sequence
from sequence_run_manager.models.sequence import SequenceStatus
from sequence_run_manager_proc.domain.sequencerunstatechange import (
    SequenceRunStateChange,
    AWSEvent,
    Marshaller,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ICA_WORKFLOW_PREFIX = "/iap/workflow"  # FIXME update this


@dataclass
class SequenceDomain:
    _namespace = "orcabus.srm"
    _version = "1.0.0"
    sequence: Sequence
    state_has_changed: bool = False

    @property
    def namespace(self) -> str:
        """Domain event namespace"""
        return self._namespace

    @property
    def event_version(self) -> str:
        """Domain event version"""
        return self._version

    @property
    def event_type(self) -> str:
        """Domain event type in string representation"""
        return SequenceRunStateChange.__name__

    def to_event(self) -> SequenceRunStateChange:
        """Convert from Entity model to Domain event object"""
        if self.sequence is None:
            raise SequenceRuleError("Sequence entity is null or not loaded yet")

        if isinstance(self.sequence.status, SequenceStatus):
            _status_str = str(self.sequence.status.value)
        elif isinstance(self.sequence.status, str):
            _status_str = self.sequence.status
        else:
            raise SequenceRuleError("Sequence status is null or not loaded yet")

        return SequenceRunStateChange(
            id=self.sequence.id,
            instrument_run_id=self.sequence.instrument_run_id,
            run_volume_name=self.sequence.run_volume_name,
            run_folder_path=self.sequence.run_folder_path,
            run_data_uri=self.sequence.run_data_uri,
            status=_status_str,
            start_time=self.sequence.start_time,
            end_time=self.sequence.end_time,
            reagent_barcode=self.sequence.reagent_barcode,
            flowcell_barcode=self.sequence.flowcell_barcode,
            sample_sheet_name=self.sequence.sample_sheet_name,
            sequence_run_id=self.sequence.sequence_run_id,
            sequence_run_name=self.sequence.sequence_run_name,
        )

    def to_event_with_envelope(self) -> AWSEvent:
        """Convert from Entity model to Domain event object with envelope"""
        return AWSEvent(
            id=str(uuid.uuid4()),
            time=datetime.utcnow().replace(tzinfo=timezone.utc),
            version=self.event_version,
            source=self.namespace,
            detail_type=self.event_type,
            detail=self.to_event(),
        )

    def to_put_events_request_entry(
        self, event_bus_name: str, trace_header: str = ""
    ) -> dict:
        """Convert Domain event with envelope to Entry dict struct of PutEvent API"""
        domain_event_with_envelope = self.to_event_with_envelope()
        entry = {
            "Detail": json.dumps(
                Marshaller.marshall(domain_event_with_envelope.detail)
            ),
            "DetailType": domain_event_with_envelope.detail_type,
            "Resources": [],
            "Source": domain_event_with_envelope.source,
            "Time": domain_event_with_envelope.time,
            "EventBusName": event_bus_name,
        }
        if domain_event_with_envelope.resources is not None:
            entry.update(Resources=domain_event_with_envelope.resources)
        if trace_header:
            entry.update(TraceHeader=trace_header)
        return entry


class SequenceRuleError(ValueError):
    pass


class SequenceRule:
    def __init__(self, sequence: Sequence):
        self._sequence = sequence

    def must_not_emergency_stop(self):
        """
        emergency_stop_list - is simple registry list that
            - is in JSON format
            - store in SSM param store
            - contains list of instrument_run_id e.g. ["200612_A01052_0017_BH5LYWDSXY"]

        Business rule:
        If this_sequence is found in the emergency stop list then it will stop any further processing.
        Otherwise, emergency stop list should be empty list [].

        Here is an example to set emergency_stop_list for Run 200612_A01052_0017_BH5LYWDSXY.
        To reset, simply payload value to the empty list [].

            aws ssm put-parameter \
              --name "/iap/workflow/emergency_stop_list" \
              --type "String" \
              --value "[\"200612_A01052_0017_BH5LYWDSXY\"]" \
              --overwrite \
              --profile dev
        """
        try:
            emergency_stop_list_json = libssm.get_ssm_param(
                f"{ICA_WORKFLOW_PREFIX}/emergency_stop_list"
            )
            emergency_stop_list = libjson.loads(emergency_stop_list_json)
        except Exception as e:
            # If any exception found, log warning and proceed
            logger.warning(
                f"Cannot read emergency_stop_list from SSM param. Exception: {e}"
            )
            emergency_stop_list = []

        if self._sequence.instrument_run_id in emergency_stop_list:
            raise SequenceRuleError(
                f"Sequence {self._sequence.instrument_run_id} is marked for emergency stop."
            )

        return self
