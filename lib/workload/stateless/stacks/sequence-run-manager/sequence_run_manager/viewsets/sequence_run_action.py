from sequence_run_manager_proc.services.bssh_srv import BSSHService
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework.decorators import action
from rest_framework import status
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes
from sequence_run_manager.models import Sequence
import logging
logger = logging.getLogger(__name__)

class SequenceRunActionViewSet(ViewSet):
    """
    ViewSet for sequence run actions
    """
    lookup_value_regex = "[^/]+" 
    queryset = Sequence.objects.all()
    
    @extend_schema(
        responses=OpenApiTypes.OBJECT,
        description="Get the sample sheet for a sequence run"
    )
    @action(detail=True, methods=['get'], url_name='get_sample_sheet', url_path='get_sample_sheet')
    def get_sample_sheet(self, request, *args, **kwargs):
        """
        Get the sample sheet for a sequence run
        """
        pk = self.kwargs.get('pk')
        sequence_run = get_object_or_404(self.queryset, pk=pk)
        
        logger.info(f'Sequence run api url: {sequence_run.api_url},  sample sheet name: {sequence_run.sample_sheet_name}')
        
        bssh_srv = BSSHService()
        sample_sheet = bssh_srv.get_sample_sheet_from_bssh_run_files(sequence_run.api_url, sequence_run.sample_sheet_name)
        if not sample_sheet:
            return Response({"detail": "Sample sheet not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            response = {
                "sampleSheetName": sequence_run.sample_sheet_name,
                "sampleSheetContent": sample_sheet
            }
            return Response(response, status=status.HTTP_200_OK)
