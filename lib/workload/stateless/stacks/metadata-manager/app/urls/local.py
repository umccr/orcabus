from django.urls import path, include, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from rest_framework import permissions
from django.contrib import admin

from .base import urlpatterns as base_urlpatterns, router

# schema_view = get_schema_view(
#     openapi.Info(
#         title="UMCCR OrcaBus app API",
#         default_version="v1",
#         description="UMCCR OrcaBus app API",
#         terms_of_service="https://umccr.org/",
#         contact=openapi.Contact(email="services@umccr.org"),
#         license=openapi.License(name="MIT License"),
#     ),
#     public=True,
#     permission_classes=[
#         permissions.AllowAny,
#     ],
#     patterns=[
#         path("", include(router.urls)),
#     ],
# )

urlpatterns = base_urlpatterns + [
    path("admin/", admin.site.urls),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    # re_pah(
    #     r"^swagger(?P<format>\.json|\.yaml)$",
    #     schema_view.without_ui(cache_timeout=0),
    #     name="schema-json",
    # ),
    # re_path(
    #     r"^swagger/$",
    #     schema_view.with_ui("swagger", cache_timeout=0),
    #     name="schema-swagger-ui",
    # ),
    # re_path(
    #     r"^redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"
    # ),
]
