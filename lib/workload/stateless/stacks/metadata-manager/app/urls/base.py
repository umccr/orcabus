from django.urls import path, include

from app.routers import OptionalSlashDefaultRouter
from app.viewsets.lab import LibraryViewSet, SubjectViewSet, SpecimenViewSet

router = OptionalSlashDefaultRouter()
router.register(r"subject", SubjectViewSet, basename="subject")
router.register(r"specimen", SpecimenViewSet, basename="specimen")
router.register(r"library", LibraryViewSet, basename="library")

urlpatterns = [
    # path("iam/", include(router.urls)),
    path("", include(router.urls)),
]

handler500 = "rest_framework.exceptions.server_error"
handler400 = "rest_framework.exceptions.bad_request"
