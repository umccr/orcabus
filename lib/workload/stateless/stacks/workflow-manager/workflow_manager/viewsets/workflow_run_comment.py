from rest_framework import mixins, status
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action

from workflow_manager.models import WorkflowRunComment, WorkflowRun
from workflow_manager.serializers.workflow_run_comment import WorkflowRunCommentSerializer


class WorkflowRunCommentViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.ListModelMixin,
                                GenericViewSet):
    serializer_class = WorkflowRunCommentSerializer
    search_fields = WorkflowRunComment.get_base_fields()
    http_method_names = ['get', 'post', 'patch', 'delete']
    pagination_class = None
    lookup_value_regex = "[^/]+" # to allow id prefix

    def get_queryset(self):
        return WorkflowRunComment.objects.filter(
            workflow_run=self.kwargs["orcabus_id"],
            is_deleted=False
        )

    def create(self, request, *args, **kwargs):
        wfr_orcabus_id = self.kwargs["orcabus_id"]

        # Check if the WorkflowRun exists
        try:
            WorkflowRun.objects.get(orcabus_id=wfr_orcabus_id)
        except WorkflowRun.DoesNotExist:
            return Response({"detail": "WorkflowRun not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if created_by and comment are provided
        if not request.data.get('created_by') or not request.data.get('comment'):
            return Response({"detail": "created_by and comment are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Add workflow_run_id to the request data
        mutable_data = request.data.copy()
        mutable_data['workflow_run'] = wfr_orcabus_id

        serializer = self.get_serializer(data=mutable_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save()  # Assuming you're using email as the user identifier

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Check if the user updating the comment is the same as the one who created it
        if instance.created_by != request.data.get('created_by'):
            raise PermissionDenied("You don't have permission to update this comment.")

        # Ensure only the comment field can be updated
        if set(request.data.keys()) - {'comment', 'created_by'}:
            return Response({"detail": "Only the comment field can be updated."},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)

    def perform_update(self, serializer):
        serializer.save()

    @action(detail=True, methods=['delete'])
    def soft_delete(self, request, *args, **kwargs):
        instance = self.get_object()

        # Check if the user deleting the comment is the same as the one who created it
        if instance.created_by != request.data.get('created_by'):
            raise PermissionDenied("You don't have permission to delete this comment.")

        instance.is_deleted = True
        instance.save()

        return Response({"detail": "Comment successfully marked as deleted."}, status=status.HTTP_204_NO_CONTENT)
