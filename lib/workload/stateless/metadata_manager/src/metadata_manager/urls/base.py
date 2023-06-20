from django.urls import path, include

from metadata_manager.routers import OptionalSlashDefaultRouter
from metadata_manager.viewsets.metadata import MetadataViewSet

router = OptionalSlashDefaultRouter()
router.register(r"metadata", MetadataViewSet, basename="metadata")

urlpatterns = [path("iam/", include(router.urls)), path("", include(router.urls))]

handler500 = "rest_framework.exceptions.server_error"
handler400 = "rest_framework.exceptions.bad_request"
