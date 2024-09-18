from app.models import Contact
from .base import SerializersBase


class ContactSerializer(SerializersBase):
    prefix = Contact.orcabus_id_prefix

    class Meta:
        model = Contact
        fields = "__all__"
