from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from app.models import Library
from app.serializers.utils import OrcabusIdSerializerMetaMixin


class LibrarySerializer(ModelSerializer):

    class Meta(OrcabusIdSerializerMetaMixin):
        model = Library
        exclude = ["project_set"]


class LibraryDetailSerializer(ModelSerializer):
    from .sample import SampleSerializer
    from .project import ProjectSerializer
    from .subject import SubjectIndividualSerializer

    project_set = ProjectSerializer(many=True, read_only=True)

    sample = SampleSerializer(read_only=True)
    subject = SubjectIndividualSerializer(read_only=True)
    class Meta(OrcabusIdSerializerMetaMixin):
        model = Library
        fields = "__all__"


class LibraryHistorySerializer(LibrarySerializer):
    class ProjectOrcabusIdSet(serializers.StringRelatedField):
        def to_internal_value(self, data):
            raise NotImplementedError()

    class Meta:
        model = Library.history.model
        fields = "__all__"

    project_set = ProjectOrcabusIdSet(many=True, read_only=True)
