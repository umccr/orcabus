from sequence_run_manager.models import SampleSheet, Sequence
from sequence_run_manager.serializers.sample_sheet import SampleSheetSerializer
from rest_framework.viewsets import ViewSet
from rest_framework import mixins
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiResponse

import logging
logger = logging.getLogger(__name__)

class SampleSheetViewSet(ViewSet):
    """
    ViewSet for sample sheet
    """
    queryset = Sequence.objects.all()
    pagination_class = None
    lookup_value_regex = "[^/]+" # to allow id prefix
    
    @extend_schema(
        responses={
            200: SampleSheetSerializer,
            404: OpenApiResponse(description="No active sample sheet found for this sequence.")
        },
        operation_id="get_sequence_sample_sheet"
    )
    @action(detail=True, methods=["get"], url_name="sample_sheet", url_path="sample_sheet")
    def sample_sheet(self, request, *args, **kwargs):
        """
        Returns a queryset containing a single SampleSheet record or an empty queryset.
        """
        
        sample_sheet = SampleSheet.objects.filter(sequence_id = kwargs.get('pk'), association_status='active').first()
        if sample_sheet:
            return Response(SampleSheetSerializer(sample_sheet).data, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
    
    