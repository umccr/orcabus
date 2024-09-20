from app.models import Subject
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
