from rest_framework.serializers import ModelSerializer
from app.models import Contact
from app.serializers.utils import OrcabusIdSerializerMetaMixin


class ContactSerializer(ModelSerializer):
    class Meta(OrcabusIdSerializerMetaMixin):
        model = Contact
        fields = "__all__"


class ContactDetailSerializer(ModelSerializer):
    from .project import ProjectSerializer

    project_set = ProjectSerializer(many=True, read_only=True)

    class Meta(OrcabusIdSerializerMetaMixin):
        model = Contact
        fields = "__all__"


class ContactHistorySerializer(ModelSerializer):
    class Meta:
        model = Contact.history.model
        fields = "__all__"
