from django.urls import path, include

from app.routers import OptionalSlashDefaultRouter
from app.viewsets import LibraryViewSet, SubjectViewSet, SampleViewSet, ProjectViewSet, ContactViewSet, \
    IndividualViewSet, SyncViewSet
from app.settings.base import API_VERSION

api_namespace = "api"
api_version = API_VERSION
api_base = f"{api_namespace}/{api_version}/"

router = OptionalSlashDefaultRouter()
router.register(r"individual", IndividualViewSet, basename="individual")
router.register(r"subject", SubjectViewSet, basename="subject")
router.register(r"sample", SampleViewSet, basename="sample")
router.register(r"library", LibraryViewSet, basename="library")
router.register(r"project", ProjectViewSet, basename="project")
router.register(r"contact", ContactViewSet, basename="contact")
router.register(r"sync", SyncViewSet, basename="sync")

urlpatterns = [
    path(f"{api_base}", include(router.urls)),
]

handler500 = "rest_framework.exceptions.server_error"
handler400 = "rest_framework.exceptions.bad_request"
