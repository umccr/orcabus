from django.urls import path, include
from django.urls import path
from drf_spectacular.views import SpectacularJSONAPIView, SpectacularSwaggerView

from sequence_run_manager.routers import OptionalSlashDefaultRouter
from sequence_run_manager.viewsets.sequence_run import SequenceRunViewSet
from sequence_run_manager.viewsets.sequence import SequenceViewSet
from sequence_run_manager.viewsets.state import StateViewSet
from sequence_run_manager.viewsets.comment import CommentViewSet
from sequence_run_manager.viewsets.sequence_run_stats import SequenceStatsViewSet
from sequence_run_manager.viewsets.sample_sheet import SampleSheetViewSet
from sequence_run_manager.viewsets.sequence_run_action import SequenceRunActionViewSet
from sequence_run_manager.settings.base import API_VERSION

api_namespace = "api"
api_version = API_VERSION
api_base = f"{api_namespace}/{api_version}/"

router = OptionalSlashDefaultRouter()
router.register(r"sequence_run", SequenceRunViewSet, basename="sequence-run")
router.register(r"sequence_run", SampleSheetViewSet, basename="sequence-run-sample-sheet")
router.register("sequence_run/(?P<orcabus_id>[^/]+)/comment", CommentViewSet, basename="sequence-run-comment")
router.register("sequence_run/(?P<orcabus_id>[^/]+)/state", StateViewSet, basename="sequence-run-states")
router.register(r"sequence_run/stats", SequenceStatsViewSet, basename="sequence-run-stats")

# Sequence Run Action
router.register(r"sequence_run/action", SequenceRunActionViewSet, basename="sequence-run-action")

# Sequence Concept (refer:https://github.com/umccr/orcabus/issues/947); sequence-runs group by instrument run id
# future: router.register(r"sequence", SequenceViewSet, basename="sequence-run")
router.register("sequence/(?P<instrument_run_id>[^/]+)", SequenceViewSet, basename="sequence-by-instrument-run-id")

urlpatterns = [
    path(f"{api_base}", include(router.urls)),
    path('schema/openapi.json', SpectacularJSONAPIView.as_view(), name='schema'),
    path('schema/swagger-ui/',
         SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

handler500 = "rest_framework.exceptions.server_error"
handler400 = "rest_framework.exceptions.bad_request"
