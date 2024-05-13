from django.db import transaction

from workflow_manager.models.workflow import Workflow


@transaction.atomic
def persist_workflow_srv():
    wf = Workflow()
    wf.text = "Test Workflow"
    wf.save()


@transaction.atomic
def get_workflow_from_db():
    return Workflow.objects.first()
