from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema, swagger_serializer_method
from rest_framework import filters
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from app.models import Subject, Specimen, Library
from app.pagination import StandardResultsSetPagination
from app.serializers import SubjectSerializer, SpecimenSerializer, LibrarySerializer, SubjectFullSerializer, \
    LibraryFullSerializer


class SubjectViewSet(ReadOnlyModelViewSet):
    serializer_class = SubjectSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = "__all__"
    ordering = ["-id"]
    search_fields = Subject.get_base_fields()

    def get_queryset(self):
        return Subject.objects.get_by_keyword(**self.request.query_params)

    @action(detail=False, methods=['get'], url_path='full')
    @swagger_auto_schema(responses={200: SubjectFullSerializer(many=False)}, manual_parameters=[
        openapi.Parameter(
            'library_internal_id',
            openapi.IN_QUERY,
            description="Filter the subjects that contain this particular internal_id in the Library model.",
            type=openapi.TYPE_STRING,
        ), ])
    def get_full_model_set(self, request):
        query_params = self.request.query_params.copy()
        qs = Subject.objects.prefetch_related("specimen_set__library_set").all().order_by("-id")

        # Allow filtering by library_internal_id
        library_internal_id = query_params.get("library_internal_id", None)
        if library_internal_id:
            query_params.pop("library_internal_id")
            qs = qs.filter(specimen__library__internal_id=library_internal_id)

        # Following same pattern with other filter where if unknown query params returns empty qs
        qs = Subject.objects.get_model_fields_query(qs, **query_params)

        page = self.paginate_queryset(qs)
        serializer = SubjectFullSerializer(page, many=True)

        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['get'], url_path='full')
    @swagger_auto_schema(responses={200: SubjectFullSerializer(many=True)})
    def get_full_model_detail(self, request, pk=None):
        subject = Subject.objects.get(id=pk)
        serializer = SubjectFullSerializer(subject)

        return Response(serializer.data)


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

    @action(detail=False, methods=['get'], url_path='full')
    @swagger_auto_schema(responses={200: LibraryFullSerializer(many=True)})
    def get_full_model_set(self, request):
        qs = Library.objects.select_related("specimen__subject").all().order_by("-id")

        # Allow filtering by the keys inside the library model
        qs = Library.objects.get_model_fields_query(qs, **self.request.query_params)

        page = self.paginate_queryset(qs)
        serializer = LibraryFullSerializer(page, many=True)

        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['get'], url_path='full')
    @swagger_auto_schema(responses={200: LibraryFullSerializer(many=False)})
    def get_full_model_detail(self, request, pk=None):
        lib = Library.objects.get(id=pk)
        serializer = LibraryFullSerializer(lib)

        return Response(serializer.data)
