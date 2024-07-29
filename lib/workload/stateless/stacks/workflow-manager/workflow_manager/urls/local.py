from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .base import urlpatterns as base_urlpatterns

urlpatterns = base_urlpatterns + [
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger-ui/',
         SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
