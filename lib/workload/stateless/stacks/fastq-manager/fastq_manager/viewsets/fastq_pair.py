from rest_framework import filters
from rest_framework.viewsets import ModelViewSet

from fastq_manager.models.fastq_pair import FastqPair
from fastq_manager.pagination import StandardResultsSetPagination
from fastq_manager.serializers import FastqPairModelSerializer


class FastqPairViewSet(ModelViewSet):
    serializer_class = FastqPairModelSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = '__all__'
    search_fields = ordering_fields
    ordering = ['-id']
    queryset = FastqPair.objects.all()
