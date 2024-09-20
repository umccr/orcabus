from .base import SerializersBase
from app.models import Project


class ProjectBaseSerializer(SerializersBase):
    prefix = Project.orcabus_id_prefix


class ProjectSerializer(ProjectBaseSerializer):
    class Meta:
        model = Project
        exclude = ["contact_set"]


class ProjectDetailSerializer(ProjectBaseSerializer):
    from .contact import ContactSerializer

    contact_set = ContactSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = "__all__"
