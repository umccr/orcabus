from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import GenericViewSet
from django.db.models import Q
from sequence_run_manager.models import Sequence, State, Comment, SampleSheet
from sequence_run_manager.serializers.sequence_run import SequenceRunSerializer
from sequence_run_manager.serializers.state import StateSerializer
from sequence_run_manager.serializers.comment import CommentSerializer
from sequence_run_manager.serializers.sample_sheet import SampleSheetSerializer, SampleSheetWithCommentSerializer
from sequence_run_manager.viewsets.state import StateViewSet

class SequenceViewSet(GenericViewSet):
    """
    (sequence and sequence run logic refer: https://github.com/umccr/orcabus/issues/947)
    ViewSet for sequence data group by "instrument run id"
    """
    pagination_class = None

    @extend_schema(responses=SequenceRunSerializer(many=True), description="Get all sequence data by instrument run id")
    @action(detail=False, methods=["get"], url_name="sequence_run_by_instrument_run_id", url_path="sequence_run")
    def sequence_run_by_instrument_run_id(self, request, *args, **kwargs):
        """
        Get all sequence data by instrument run id
        """
        instrument_run_id = kwargs.get('instrument_run_id')
        sequences = Sequence.objects.filter(instrument_run_id=instrument_run_id).filter(status__isnull=False) # filter out fake sequence runs
        serializer = SequenceRunSerializer(sequences, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    @extend_schema(responses=StateSerializer(many=True), description="Get all states by instrument run id")
    @action(detail=False, methods=["get"], url_name="states_by_instrument_run_id", url_path="states")
    def states_by_instrument_run_id(self, request, *args, **kwargs):
        """
        Get all states by instrument run id
        """
        instrument_run_id = kwargs.get('instrument_run_id')
        sequences = Sequence.objects.filter(instrument_run_id=instrument_run_id)
        states = State.objects.filter(sequence__in=sequences)
        serializer = StateSerializer(states, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    @extend_schema(responses=OpenApiTypes.OBJECT, description="Valid states map for new state creation, update")
    @action(detail=False, methods=['get'], url_name='valid_states_map', url_path='valid_states_map')
    def get_valid_states_map(self, request, **kwargs):
        return Response(StateViewSet.valid_states_map, status=status.HTTP_200_OK)
    
    
    @extend_schema(responses=CommentSerializer(many=True), description="Get all comments by instrument run id")
    @action(detail=False, methods=["get"], url_name="comments_by_instrument_run_id", url_path="comments")
    def comments_by_instrument_run_id(self, request, *args, **kwargs):
        """
        Get all comments by instrument run id
        """
        instrument_run_id = kwargs.get('instrument_run_id')
        sequences_orcabus_ids = Sequence.objects.filter(instrument_run_id=instrument_run_id).values_list('orcabus_id', flat=True)
        comments = Comment.objects.filter(association_id__in=sequences_orcabus_ids)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    @extend_schema(responses=SampleSheetWithCommentSerializer(many=True), description="Get all sample sheets by instrument run id")
    @action(detail=False, methods=["get"], url_name="sample_sheets_by_instrument_run_id", url_path="sample_sheets")
    def sample_sheets_by_instrument_run_id(self, request, *args, **kwargs):
        """
        Get all sample sheets by instrument run id
        """
        instrument_run_id = kwargs.get('instrument_run_id')
        sequences = Sequence.objects.filter(instrument_run_id=instrument_run_id)
        sample_sheets = SampleSheet.objects.filter(sequence__in=sequences)
        comments = Comment.objects.filter(association_id__in=sample_sheets.values_list('orcabus_id', flat=True))
        for sample_sheet in sample_sheets:
            sample_sheet.comment = comments.filter(association_id=sample_sheet.orcabus_id).first()
        serializer = SampleSheetWithCommentSerializer(sample_sheets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    