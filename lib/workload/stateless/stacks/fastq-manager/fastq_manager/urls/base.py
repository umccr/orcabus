from django.urls import path, include

from fastq_manager.routers import OptionalSlashDefaultRouter
from fastq_manager.viewsets.fastq_pair import FastqPairViewSet
from fastq_manager.settings.base import API_VERSION

api_namespace = "api"
api_version = API_VERSION
api_base = f"{api_namespace}/{api_version}/"

router = OptionalSlashDefaultRouter()
router.register(r"fastq", FastqPairViewSet, basename="fastq")

urlpatterns = [
    path(f"{api_base}", include(router.urls)),
]

handler500 = "rest_framework.exceptions.server_error"
handler400 = "rest_framework.exceptions.bad_request"
