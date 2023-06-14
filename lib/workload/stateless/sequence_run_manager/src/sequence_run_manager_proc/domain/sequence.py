import logging
from dataclasses import dataclass

from libumccr import libjson
from libumccr.aws import libssm

from sequence_run_manager.models import Sequence

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ICA_WORKFLOW_PREFIX = "/iap/workflow"  # FIXME update this


@dataclass
class SequenceDomain:
    sequence: Sequence
    state_has_changed: bool = False


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
