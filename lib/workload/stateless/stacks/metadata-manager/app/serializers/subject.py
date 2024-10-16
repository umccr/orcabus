from rest_framework import serializers

from app.models import Subject, Individual
from .base import SerializersBase


class SubjectBaseSerializer(SerializersBase):
    prefix = Subject.orcabus_id_prefix


class SubjectSerializer(SubjectBaseSerializer):
    prefix = Subject.orcabus_id_prefix

    class Meta:
        model = Subject
        exclude = ["individual_set"]


class SubjectDetailSerializer(SubjectBaseSerializer):
    from .individual import IndividualSerializer
    from .library import LibrarySerializer

    class Meta:
        model = Subject
        fields = '__all__'

    individual_set = IndividualSerializer(many=True, read_only=True)
    library_set = LibrarySerializer(many=True, read_only=True)


class SubjectHistorySerializer(SubjectBaseSerializer):
    class IndividualOrcabusIdSet(serializers.RelatedField):
        def to_internal_value(self, data):
            raise NotImplementedError()

        def to_representation(self, value):
            return Individual.orcabus_id_prefix + value.individual.orcabus_id

    class Meta:
        model = Subject.history.model
        fields = "__all__"

    individual_set = IndividualOrcabusIdSet(many=True, read_only=True)
