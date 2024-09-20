from app.models import Individual
from .base import SerializersBase


class IndividualSerializer(SerializersBase):
    prefix = Individual.orcabus_id_prefix

    class Meta:
        model = Individual
        fields = '__all__'


class IndividualDetailSerializer(IndividualSerializer):
    from .subject import SubjectSerializer

    subject_set = SubjectSerializer(many=True, read_only=True)

