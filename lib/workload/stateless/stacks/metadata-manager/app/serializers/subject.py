from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from app.models import Subject, Individual
from app.serializers.utils import OrcabusIdSerializerMetaMixin


class SubjectSerializer(ModelSerializer):
    class Meta(OrcabusIdSerializerMetaMixin):
        model = Subject
        exclude = ["individual_set"]


class SubjectDetailSerializer(ModelSerializer):
    from .individual import IndividualSerializer
    from .library import LibrarySerializer

    class Meta(OrcabusIdSerializerMetaMixin):
        model = Subject
        fields = '__all__'

    individual_set = IndividualSerializer(many=True, read_only=True)
    library_set = LibrarySerializer(many=True, read_only=True)


class SubjectHistorySerializer(ModelSerializer):
    class IndividualOrcabusIdSet(serializers.StringRelatedField):
        def to_internal_value(self, data):
            raise NotImplementedError()

    class Meta:
        model = Subject.history.model
        fields = "__all__"

    individual_set = IndividualOrcabusIdSet(many=True, read_only=True)
