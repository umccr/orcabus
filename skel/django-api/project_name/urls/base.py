from django.urls import path, include

from {{project_name}}.routers import OptionalSlashDefaultRouter
from {{project_name}}.viewsets.helloworld import HelloWorldViewSet
from {{project_name}}.settings.base import API_VERSION

api_version = API_VERSION
api_base = f"api/{api_version}/"

router = OptionalSlashDefaultRouter()
router.register(r"hello", HelloWorldViewSet, basename="hello")

urlpatterns = [
    path(f"{api_base}", include(router.urls)),
]

handler500 = "rest_framework.exceptions.server_error"
handler400 = "rest_framework.exceptions.bad_request"
