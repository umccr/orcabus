from django.urls import path, include, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from .base import urlpatterns as base_urlpatterns, router

schema_view = get_schema_view(
    openapi.Info(
        title="UMCCR OrcaBus {{project_name}} API",
        default_version="v1",
        description="UMCCR OrcaBus {{project_name}} API",
        terms_of_service="https://umccr.org/",
        contact=openapi.Contact(email="services@umccr.org"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny, ],
    patterns=[path("", include(router.urls)), ],
)

urlpatterns = base_urlpatterns + [
    re_path(r"^swagger(?P<format>\.json|\.yaml)$", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    re_path(r"^swagger/$", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    re_path(r"^redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]
