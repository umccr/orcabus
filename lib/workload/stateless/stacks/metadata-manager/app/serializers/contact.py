from abc import ABC

from rest_framework import serializers

from app.models import Contact
from .base import SerializersBase


class ContactBaseSerializer(SerializersBase):
    prefix = Contact.orcabus_id_prefix


class ContactSerializer(ContactBaseSerializer):
    class Meta:
        model = Contact
        fields = "__all__"


class ContactDetailSerializer(ContactBaseSerializer):
    from .project import ProjectSerializer

    project_set = ProjectSerializer(many=True, read_only=True)

    class Meta:
        model = Contact
        fields = "__all__"


class ContactHistorySerializer(ContactBaseSerializer):
    class Meta:
        model = Contact.history.model
        fields = "__all__"
