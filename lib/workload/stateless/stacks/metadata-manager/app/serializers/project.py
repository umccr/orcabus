from rest_framework import serializers

from .base import SerializersBase
from app.models import Project, Contact


class ProjectBaseSerializer(SerializersBase):
    prefix = Project.orcabus_id_prefix


class ProjectSerializer(ProjectBaseSerializer):
    class Meta:
        model = Project
        exclude = ["contact_set"]


class ProjectDetailSerializer(ProjectBaseSerializer):
    from .contact import ContactSerializer
    from .library import LibrarySerializer

    contact_set = ContactSerializer(many=True, read_only=True)
    library_set = LibrarySerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = "__all__"


class ProjectHistorySerializer(ProjectBaseSerializer):
    class ContactOrcabusIdSet(serializers.RelatedField):

        def to_internal_value(self, data):
            raise NotImplementedError()

        def to_representation(self, value):
            return Contact.orcabus_id_prefix + value.contact.orcabus_id

    class Meta:
        model = Project.history.model
        fields = "__all__"

    contact_set = ContactOrcabusIdSet(many=True, read_only=True)

