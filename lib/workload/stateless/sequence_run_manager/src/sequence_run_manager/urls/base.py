from django.urls import path, include

from sequence_run_manager.routers import OptionalSlashDefaultRouter
from sequence_run_manager.viewsets.sequence import SequenceViewSet

router = OptionalSlashDefaultRouter()
router.register(r"sequence", SequenceViewSet, basename="sequence")

urlpatterns = [
    # path("iam/", include(router.urls)),
    path("", include(router.urls)),
]

handler500 = "rest_framework.exceptions.server_error"
handler400 = "rest_framework.exceptions.bad_request"
