from django.urls import path, include

from case_manager.routers import OptionalSlashDefaultRouter
from case_manager.viewsets.case import CaseViewSet
from case_manager.viewsets.case_data import CaseDataViewSet
from case_manager.viewsets.state import StateViewSet
# from case_manager.viewsets.library import LibraryViewSet
from case_manager.settings.base import API_VERSION

api_namespace = "api"
api_version = API_VERSION
api_base = f"{api_namespace}/{api_version}/"

router = OptionalSlashDefaultRouter()
router.register(r"case", CaseViewSet, basename="case")

# may no longer need this as it's currently included in the detail response for an individual CaseRun record
router.register(
    "case/(?P<orcabus_id>[^/.]+)/state",
    StateViewSet,
    basename="case-state",
)

router.register(
    "caserun/(?P<orcabus_id>[^/.]+)/data",
    CaseDataViewSet,
    basename="case-data",
)

# router.register(
#     "caserun/(?P<caserun_id>[^/.]+)/library",
#     LibraryViewSet,
#     basename="caserun-library",
# )

# router.register(
#     "case/(?P<orcabus_id>[^/.]+)/comment",
#     CaseCommentViewSet,
#     basename="case-comment",
# )

urlpatterns = [
    path(f"{api_base}", include(router.urls)),
]

handler500 = "rest_framework.exceptions.server_error"
handler400 = "rest_framework.exceptions.bad_request"
