from django.urls import path, include

from workflow_manager.routers import OptionalSlashDefaultRouter
from workflow_manager.viewsets.workflow import WorkflowViewSet
from workflow_manager.viewsets.workflow_run import WorkflowRunViewSet
from workflow_manager.viewsets.payload import PayloadViewSet
from workflow_manager.settings.base import API_VERSION

api_namespace = "api"
api_version = API_VERSION
api_base = f"{api_namespace}/{api_version}/"

router = OptionalSlashDefaultRouter()
router.register(r"workflow", WorkflowViewSet, basename="workflow")
router.register(r"workflowrun", WorkflowRunViewSet, basename="workflowrun")
router.register(r"payload", PayloadViewSet, basename="payload")

urlpatterns = [
    path(f"{api_base}", include(router.urls)),
]

handler500 = "rest_framework.exceptions.server_error"
handler400 = "rest_framework.exceptions.bad_request"
