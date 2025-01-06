import logging
import uuid
from datetime import timedelta, datetime, timezone
from typing import List

from workflow_manager.models import Status, State, WorkflowRun

logger = logging.getLogger()
logger.setLevel(logging.INFO)

RUNNING_MIN_TIME_DELTA_SEC = timedelta(hours=1).total_seconds()
TIMEDELTA_1H = timedelta(hours=1)


class WorkflowRunUtil:
    """
    Utility methods for a WorkflowRun.
    # TODO: this could be integrated into the WorflowRun model class? (figure out performance / implications)
    """

    def __init__(self, workflow_run: WorkflowRun):
        self.workflow_run = workflow_run
        self.states: List[State] = list(self.workflow_run.get_all_states())

    def get_current_state(self):
        if len(self.states) < 1:
            return None
        elif len(self.states) == 1:
            return self.states[0]
        else:
            return WorkflowRunUtil.get_latest_state(self.states)

    def is_complete(self):
        return self.get_current_state().is_terminal()

    def is_draft(self):
        # There may be multiple DRAFT states. We assume they are in order, e.g. no other state inbetween
        return self.get_current_state().is_draft()

    def is_ready(self):
        return self.get_current_state().is_ready()

    def is_running(self):
        return self.get_current_state().is_running()

    def contains_status(self, status: str):
        # NOTE: we assume status is following conventions
        for s in self.states:
            if status == s.status:
                return True
        return False

    def transition_to(self, new_state: State) -> bool:
        """
        Parameter:
            new_state: the new state to transition to
        Process:
            Transition to the new state if possible and update the WorkflowRun.
        Return:
            False: if the transition is not possible
            True: if the state was updated
        # TODO: consider race conditions?
        """
        # enforce status conventions on new state
        new_state.status = Status.get_convention(new_state.status)  # TODO: encapsulate into State ?!

        # If it's a brand new WorkflowRun we expect the first state to be DRAFT
        # TODO: handle exceptions;
        #       BCL Convert may not create a DRAFT state
        if not self.get_current_state():
            if new_state.is_draft():
                self.persist_state(new_state)
                return True
            else:
                logger.warning(f"WorkflowRun does not have state yet, but new state is not DRAFT: {new_state}")
                self.persist_state(new_state)  # FIXME: remove once convention is enforced
                return True

        # Ignore any state that's older than the current one
        if new_state.timestamp < self.get_current_state().timestamp:
            return False

        # Don't allow any changes once in terminal state
        if self.is_complete():
            logger.info(f"WorkflowRun in terminal state, can't transition to: {new_state.status}")
            return False

        # Allowed transitions from DRAFT state
        if self.is_draft():
            if new_state.is_draft():  # allow "updates" of the DRAFT state
                self.persist_state(new_state)
                return True
            elif new_state.is_ready():  # allow transition from DRAFT to READY state
                self.persist_state(new_state)
                return True
            else:
                return False  # Don't allow any other transitions from DRAFT state

        # Allowed transitions from READY state
        if self.is_ready():
            if new_state.is_draft():  # no going back
                return False
            if new_state.is_ready():  # no updates to READY state
                return False
            # Transitions to other states is allowed (may not be controlled states though, so we can't control)

        # Allowed transitions from RUNNING state
        if self.is_running():
            if new_state.is_draft():  # no going back
                return False
            if new_state.is_ready():  # no going back
                return False
            if new_state.is_running():
                # Only allow updates every so often
                time_delta = new_state.timestamp - self.get_current_state().timestamp
                if time_delta.total_seconds() < TIMEDELTA_1H.total_seconds():
                    # Avoid too frequent updates for RUNNING state
                    return False
                else:
                    self.persist_state(new_state)
                    return True

        # Allowed transitions from other state
        if self.contains_status(new_state.status):
            # Don't allow updates/duplications of other states
            return False

        # Assume other state transitions are OK
        self.persist_state(new_state)
        return True

    def persist_state(self, new_state):
        new_state.workflow_run = self.workflow_run
        if new_state.payload:
            new_state.payload.save()  # Need to save Payload before we can save State
        new_state.save()

    @staticmethod
    def get_latest_state(states: List[State]) -> State:
        last: State = states[0]
        for s in states:
            if s.timestamp > last.timestamp:
                last = s
        return last


def create_portal_run_id() -> str:
    date = datetime.now(timezone.utc)
    return f"{date.year:04}{date.month:02}{date.day:02}{str(uuid.uuid4())[:8]}"
