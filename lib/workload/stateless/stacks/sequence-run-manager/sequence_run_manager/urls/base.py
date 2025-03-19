from django.urls import path, include
from django.urls import path
from drf_spectacular.views import SpectacularJSONAPIView, SpectacularSwaggerView

from sequence_run_manager.routers import OptionalSlashDefaultRouter
from sequence_run_manager.viewsets.sequence import SequenceViewSet
from sequence_run_manager.viewsets.state import StateViewSet
from sequence_run_manager.viewsets.comment import CommentViewSet
from sequence_run_manager.viewsets.sequence_run_stats import SequenceStatsViewSet
from sequence_run_manager.viewsets.sample_sheet import SampleSheetViewSet
from sequence_run_manager.settings.base import API_VERSION

api_namespace = "api"
api_version = API_VERSION
api_base = f"{api_namespace}/{api_version}/"

router = OptionalSlashDefaultRouter()
router.register(r"sequence", SequenceViewSet, basename="sequence")
router.register(r"sequence", SampleSheetViewSet, basename="sequence-sample-sheet")
router.register("sequence/(?P<orcabus_id>[^/]+)/comment", CommentViewSet, basename="sequence-comment")
router.register("sequence/(?P<orcabus_id>[^/]+)/state", StateViewSet, basename="sequence-states")
router.register(r"sequence/stats", SequenceStatsViewSet, basename="sequence-stats")


urlpatterns = [
    path(f"{api_base}", include(router.urls)),
    path('schema/openapi.json', SpectacularJSONAPIView.as_view(), name='schema'),
    path('schema/swagger-ui/',
         SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

handler500 = "rest_framework.exceptions.server_error"
handler400 = "rest_framework.exceptions.bad_request"
