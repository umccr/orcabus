from django.urls import path, include

from sequence_run_manager.routers import OptionalSlashDefaultRouter
from sequence_run_manager.viewsets.sequence import SequenceViewSet
from sequence_run_manager.viewsets.state import StateViewSet
from sequence_run_manager.viewsets.comment import CommentViewSet
from sequence_run_manager.settings.base import API_VERSION

api_namespace = "api"
api_version = API_VERSION
api_base = f"{api_namespace}/{api_version}/"

router = OptionalSlashDefaultRouter()
router.register(r"sequence", SequenceViewSet, basename="sequence")
router.register("sequence/(?P<orcabus_id>[^/.]+)/state", StateViewSet, basename="sequence-state")
router.register("sequence/(?P<orcabus_id>[^/.]+)/comment", CommentViewSet, basename="sequence-comment")

urlpatterns = [
    path(f"{api_base}", include(router.urls)),
]

handler500 = "rest_framework.exceptions.server_error"
handler400 = "rest_framework.exceptions.bad_request"
