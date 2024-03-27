from rest_framework import filters
from rest_framework.viewsets import ReadOnlyModelViewSet

from app.models import Subject, Specimen, Library
from app.models.lab.individual import Individual
from app.pagination import StandardResultsSetPagination
from app.serializers import SubjectSerializer, SpecimenSerializer, LibrarySerializer, IndividualSerializer


class IndividualViewSet(ReadOnlyModelViewSet):
    serializer_class = IndividualSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = "__all__"
    ordering = ["-id"]
    search_fields = Individual.get_base_fields()

    def get_queryset(self):
        return Individual.objects.get_by_keyword(**self.request.query_params)


class SubjectViewSet(ReadOnlyModelViewSet):
    serializer_class = SubjectSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = "__all__"
    ordering = ["-id"]
    search_fields = Subject.get_base_fields()

    def get_queryset(self):
        return Subject.objects.get_by_keyword(**self.request.query_params)


class SpecimenViewSet(ReadOnlyModelViewSet):
    serializer_class = SpecimenSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = "__all__"
    ordering = ["-id"]
    search_fields = Subject.get_base_fields()

    def get_queryset(self):
        return Specimen.objects.get_by_keyword(**self.request.query_params)


class LibraryViewSet(ReadOnlyModelViewSet):
    serializer_class = LibrarySerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = "__all__"
    ordering = ["-id"]
    search_fields = Subject.get_base_fields()

    def get_queryset(self):
        return Library.objects.get_by_keyword(**self.request.query_params)
