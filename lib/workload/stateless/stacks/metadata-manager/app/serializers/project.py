from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from app.models import Project, Contact
from app.serializers.utils import OrcabusIdSerializerMetaMixin


class ProjectSerializer(ModelSerializer):
    class Meta(OrcabusIdSerializerMetaMixin):
        model = Project
        exclude = ["contact_set"]


class ProjectDetailSerializer(ModelSerializer):
    from .contact import ContactSerializer

    contact_set = ContactSerializer(many=True, read_only=True)

    class Meta(OrcabusIdSerializerMetaMixin):
        model = Project
        fields = "__all__"


class ProjectHistorySerializer(ModelSerializer):
    class ContactOrcabusIdSet(serializers.StringRelatedField):

        def to_internal_value(self, data):
            raise NotImplementedError()

        def to_representation(self, value):
            return Contact.orcabus_id_prefix + value.contact.orcabus_id

    class Meta:
        model = Project.history.model
        fields = "__all__"

    contact_set = ContactOrcabusIdSet(many=True, read_only=True)
