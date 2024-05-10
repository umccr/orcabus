from rest_framework import filters
from rest_framework.viewsets import ModelViewSet

from workflow_manager.models.helloworld import HelloWorld
from workflow_manager.pagination import StandardResultsSetPagination
from workflow_manager.serializers import HelloWorldModelSerializer


class HelloWorldViewSet(ModelViewSet):
    serializer_class = HelloWorldModelSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = '__all__'
    search_fields = ordering_fields
    ordering = ['-id']
    queryset = HelloWorld.objects.all()
