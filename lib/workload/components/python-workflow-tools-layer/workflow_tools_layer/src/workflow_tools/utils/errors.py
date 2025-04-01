from typing import Optional


class WorkflowRunNotFoundError(Exception):
    def __init__(
            self,
            workflow_run_id: Optional[str] = None,
            portal_run_id: Optional[str] = None,
    ):
        self.workflow_run_id = workflow_run_id
        self.portal_run_id = portal_run_id
        if workflow_run_id is not None:
            self.message = f"Could not find workflow with orcabus run id '{workflow_run_id}'"
        elif portal_run_id is not None:
            self.message = f"Could not find workflow run portal run id '{portal_run_id}'"
        else:
            self.message = "Could not find workflow"
        super().__init__(self.message)


class WorkflowRunStateNotFoundError(Exception):
    def __init__(
            self,
            workflow_run_id: Optional[str] = None,
            portal_run_id: Optional[str] = None,
            status: Optional[str] = None,
    ):
        self.workflow_run_id = workflow_run_id
        self.portal_run_id = portal_run_id
        self.status = status
        if workflow_run_id is not None:
            self.message = f"Could not find workflow with orcabus run id '{workflow_run_id}', status '{status}'"
        elif portal_run_id is not None:
            self.message = f"Could not find workflow run portal run id '{portal_run_id}', status '{status}'"
        else:
            self.message = "Could not find workflow"
        super().__init__(self.message)
