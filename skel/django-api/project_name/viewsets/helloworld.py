from rest_framework import filters
from rest_framework.viewsets import ModelViewSet

from {{project_name}}.models.helloworld import HelloWorld
from {{project_name}}.pagination import StandardResultsSetPagination
from {{project_name}}.serializers import HelloWorldModelSerializer


class HelloWorldViewSet(ModelViewSet):
    serializer_class = HelloWorldModelSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = '__all__'
    search_fields = ordering_fields
    ordering = ['-id']
    queryset = HelloWorld.objects.all()
