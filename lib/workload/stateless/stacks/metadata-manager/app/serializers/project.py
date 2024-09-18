from .base import SerializersBase
from app.models import Project
from .contact import ContactSerializer


class ProjectSerializer(SerializersBase):
    prefix = Project.orcabus_id_prefix

    contact_set = ContactSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = "__all__"
