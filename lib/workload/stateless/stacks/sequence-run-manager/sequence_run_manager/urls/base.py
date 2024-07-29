from django.urls import path, include

from sequence_run_manager.routers import OptionalSlashDefaultRouter
from sequence_run_manager.viewsets.sequence import SequenceViewSet
from sequence_run_manager.settings.base import API_VERSION

api_namespace = "srm"
api_version = API_VERSION
api_base = f"{api_namespace}/{api_version}/"

router = OptionalSlashDefaultRouter()
router.register(r"sequence", SequenceViewSet, basename="sequence")

urlpatterns = [
    # path("iam/", include(router.urls)),
    path(f"{api_base}", include(router.urls)),
]

handler500 = "rest_framework.exceptions.server_error"
handler400 = "rest_framework.exceptions.bad_request"
