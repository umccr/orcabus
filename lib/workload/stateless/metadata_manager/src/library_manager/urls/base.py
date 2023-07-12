from django.urls import path, include

from library_manager.routers import OptionalSlashDefaultRouter
from library_manager.viewsets.library import LibraryViewSet

router = OptionalSlashDefaultRouter()
router.register(r"library", LibraryViewSet, basename="library")

urlpatterns = [path("", include(router.urls))]

handler500 = "rest_framework.exceptions.server_error"
handler400 = "rest_framework.exceptions.bad_request"
