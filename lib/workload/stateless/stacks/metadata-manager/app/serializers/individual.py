from rest_framework.serializers import ModelSerializer

from app.models import Individual
from app.serializers.utils import OrcabusIdSerializerMetaMixin


class IndividualSerializer(ModelSerializer):
    class Meta(OrcabusIdSerializerMetaMixin):
        model = Individual
        fields = '__all__'


class IndividualDetailSerializer(ModelSerializer):
    from .subject import SubjectSerializer

    class Meta(OrcabusIdSerializerMetaMixin):
        model = Individual
        fields = '__all__'

    subject_set = SubjectSerializer(many=True, read_only=True)


class IndividualHistorySerializer(ModelSerializer):
    class Meta:
        model = Individual.history.model
        fields = "__all__"
