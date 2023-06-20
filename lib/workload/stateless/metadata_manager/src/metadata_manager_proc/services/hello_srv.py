from django.db import transaction

from metadata_manager.models.metadata import Metadata


@transaction.atomic
def persist_hello_srv():
    hello = Metadata()
    hello.text = "Hallo Welt"
    hello.save()


@transaction.atomic
def get_hello_from_db():
    return Metadata.objects.first()
