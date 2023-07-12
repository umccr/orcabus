from django.urls import path, include

from {{project_name}}.routers import OptionalSlashDefaultRouter
from {{project_name}}.viewsets.helloworld import HelloWorldViewSet

router = OptionalSlashDefaultRouter()
router.register(r'hello', HelloWorldViewSet, basename='hello')

urlpatterns = [
    path('', include(router.urls)),
]

handler500 = "rest_framework.exceptions.server_error"
handler400 = "rest_framework.exceptions.bad_request"
