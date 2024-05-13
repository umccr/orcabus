from enum import Enum

import factory
from django.utils.timezone import make_aware

from workflow_manager.models.workflow import Workflow


class TestConstant(Enum):
    workflow_name = "TestWorkflowNumber1"


class WorkflowFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Workflow

    text = TestConstant.workflow_name.value
