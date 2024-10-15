from abc import ABC

from rest_framework import serializers

from app.models import Library, Sample, Subject, Project
from .base import SerializersBase


class LibraryBaseSerializer(SerializersBase):
    prefix = Library.orcabus_id_prefix


class LibrarySerializer(LibraryBaseSerializer):
    class Meta:
        model = Library
        exclude = ["project_set"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if representation.get('sample', None):
            representation['sample'] = Sample.orcabus_id_prefix + representation['sample']
        if representation.get('subject', None):
            representation['subject'] = Subject.orcabus_id_prefix + representation['subject']
        return representation


class LibraryDetailSerializer(LibraryBaseSerializer):
    from .sample import SampleSerializer
    from .project import ProjectSerializer
    from .subject import SubjectSerializer

    project_set = ProjectSerializer(many=True, read_only=True)

    sample = SampleSerializer(read_only=True)
    subject = SubjectSerializer(read_only=True)

    class Meta:
        model = Library
        fields = "__all__"


class LibraryHistorySerializer(LibrarySerializer):
    class ProjectOrcabusIdSet(serializers.RelatedField):
        def to_internal_value(self, data):
            return None

        def to_representation(self, value):
            return Project.orcabus_id_prefix + value.project.orcabus_id

    class Meta:
        model = Library.history.model
        fields = "__all__"

    project_set = ProjectOrcabusIdSet(many=True, read_only=True)
