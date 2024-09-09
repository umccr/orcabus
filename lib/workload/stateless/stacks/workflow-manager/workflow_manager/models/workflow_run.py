from django.db import models

from workflow_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager
from workflow_manager.models.library import Library
from workflow_manager.models.workflow import Workflow


class WorkflowRunManager(OrcaBusBaseManager):
    pass


class WorkflowRun(OrcaBusBaseModel):
    id = models.BigAutoField(primary_key=True)

    # --- mandatory fields

    portal_run_id = models.CharField(max_length=255, unique=True)

    # --- optional fields

    # ID of the external service
    execution_id = models.CharField(max_length=255, null=True, blank=True)
    workflow_run_name = models.CharField(max_length=255, null=True, blank=True)
    comment = models.CharField(max_length=255, null=True, blank=True)

    # --- FK link to value objects

    # Link to workflow table
    workflow = models.ForeignKey(Workflow, null=True, blank=True, on_delete=models.SET_NULL)

    # Link to library table
    # libraries = models.ManyToManyField(Library, through="LibraryAssociation")

    objects = WorkflowRunManager()

    def __str__(self):
        return f"ID: {self.id}, portal_run_id: {self.portal_run_id}, workflow_run_name: {self.workflow_run_name}, " \
               f"workflow: {self.workflow.workflow_name} "

    def to_dict(self):
        return {
            "id": self.id,
            "portal_run_id": self.portal_run_id,
            "execution_id": self.execution_id,
            "workflow_run_name": self.workflow_run_name,
            "comment": self.comment,
            "workflow": self.workflow.to_dict() if (self.workflow is not None) else None
        }

    def get_all_states(self):
        # retrieve all states (DB records rather than a queryset)
        return list(self.state_set.all())  # TODO: ensure order by timestamp ?

    def get_latest_state(self):
        # retrieve all related states and get the latest one
        return self.states.order_by('-timestamp').first()
    
    def get_libraries(self):
        # retrieve all related libraries objects
        return Library.objects.filter(workflow_run_association__workflow_run=self).distinct()

class LibraryAssociationManager(OrcaBusBaseManager):
    pass


class LibraryAssociation(OrcaBusBaseModel):
    workflow_run = models.ForeignKey(WorkflowRun, related_name="library_association", on_delete=models.CASCADE)
    library = models.ForeignKey(Library, related_name="workflow_run_association", on_delete=models.CASCADE)
    association_date = models.DateTimeField()
    status = models.CharField(max_length=255)

    objects = LibraryAssociationManager()
