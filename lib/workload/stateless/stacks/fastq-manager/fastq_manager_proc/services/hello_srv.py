from django.db import transaction

from fastq_manager.models.helloworld import HelloWorld


@transaction.atomic
def persist_hello_srv():
    hello = HelloWorld()
    hello.text = "Hallo Welt"
    hello.save()


@transaction.atomic
def get_hello_from_db():
    return HelloWorld.objects.first()
