from drf_spectacular.utils import extend_schema, OpenApiParameter
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
    ordering = ["-library_id"]
    search_fields = Subject.get_base_fields()
    queryset = Subject.objects.none()

    @extend_schema(parameters=[
        SubjectSerializer
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return Subject.objects.get_by_keyword(**self.request.query_params)

    @extend_schema(operation_id='/api/v1/subject/full/',
                   responses={200: SubjectFullSerializer(many=True)},
                   parameters=[
                       SubjectSerializer,
                       OpenApiParameter(name='libraryId',
                                        description='Filter the subjects that has the given library_id in '
                                                    'the Library model.',
                                        required=False,
                                        type=str),
                   ],
                   )
    @action(detail=False, methods=['get'], url_path='full')
    def get_full_model_set(self, request):
        query_params = self.request.query_params.copy()
        qs = Subject.objects.prefetch_related("specimen_set__library_set").all().order_by("-subject_id")

        # Allow filtering by libraryId
        library_id = query_params.get("libraryId", None)
        if library_id:
            query_params.pop("library_id")
            qs = qs.filter(specimen__library__library_id=library_id)

        # Following same pattern with other filter where if unknown query params returns empty qs
        qs = Subject.objects.get_model_fields_query(qs, **query_params)

        page = self.paginate_queryset(qs)
        serializer = SubjectFullSerializer(page, many=True)

        return self.get_paginated_response(serializer.data)

    @extend_schema(operation_id='/api/v1/subject/id/full/', responses={200: SubjectFullSerializer(many=True)})
    @action(detail=True, methods=['get'], url_path='full')
    def get_full_model_detail(self, request, pk=None):
        subject = Subject.objects.get(orcabus_id=pk)
        serializer = SubjectFullSerializer(subject)

        return Response(serializer.data)


class SpecimenViewSet(ReadOnlyModelViewSet):
    serializer_class = SpecimenSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = "__all__"
    ordering = ["-specimen_id"]
    search_fields = Specimen.get_base_fields()
    queryset = Specimen.objects.none()

    @extend_schema(parameters=[
        SpecimenSerializer
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return Specimen.objects.get_by_keyword(**self.request.query_params)


class LibraryViewSet(ReadOnlyModelViewSet):
    serializer_class = LibrarySerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = "__all__"
    ordering = ["-library_id"]
    search_fields = Library.get_base_fields()
    queryset = Library.objects.none()

    @extend_schema(parameters=[
        LibrarySerializer
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return Library.objects.get_by_keyword(**self.request.query_params)

    @extend_schema(responses={200: LibraryFullSerializer(many=True)})
    @action(detail=False, methods=['get'], url_path='full')
    def get_full_model_set(self, request):
        qs = Library.objects.select_related("specimen__subject").all().order_by("-library_id")

        # Allow filtering by the keys inside the library model
        qs = Library.objects.get_model_fields_query(qs, **self.request.query_params)

        page = self.paginate_queryset(qs)
        serializer = LibraryFullSerializer(page, many=True)

        return self.get_paginated_response(serializer.data)

    @extend_schema(responses={200: LibraryFullSerializer(many=False)})
    @action(detail=True, methods=['get'], url_path='full')
    def get_full_model_detail(self, request, pk=None):
        lib = Library.objects.get(orcabus_id=pk)
        serializer = LibraryFullSerializer(lib)

        return Response(serializer.data)
