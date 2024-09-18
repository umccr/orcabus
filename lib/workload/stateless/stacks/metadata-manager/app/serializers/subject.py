from app.models import Subject
from .base import SerializersBase


class SubjectSerializer(SerializersBase):
    prefix = Subject.orcabus_id_prefix

    class Meta:
        model = Subject
        exclude = ["individual_set"]


class SubjectDetailSerializer(SubjectSerializer):
    from .individual import IndividualSerializer

    class Meta:
        model = Subject
        fields = '__all__'

    individual_set = IndividualSerializer(many=True, read_only=True)
