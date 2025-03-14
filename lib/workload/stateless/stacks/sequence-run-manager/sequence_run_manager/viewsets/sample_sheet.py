from sequence_run_manager.models import SampleSheet
from sequence_run_manager.serializers.sample_sheet import SampleSheetSerializer
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins

import logging
logger = logging.getLogger(__name__)

class SampleSheetViewSet(mixins.ListModelMixin, GenericViewSet):
    """
    ViewSet for sample sheet
    """
    serializer_class = SampleSheetSerializer
    search_fields = SampleSheet.get_base_fields()
    pagination_class = None
    lookup_value_regex = "[^/]+" # to allow id prefix
    
    def get_queryset(self):
        return SampleSheet.objects.filter(sequence_id=self.kwargs["orcabus_id"], association_status='active')
    
