from django.db import models

from workflow_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager


class HelloWorldManager(OrcaBusBaseManager):
    pass


class HelloWorld(OrcaBusBaseModel):
    id = models.BigAutoField(primary_key=True)
    text = models.CharField(max_length=255)

    objects = HelloWorldManager()

    def __str__(self):
        return f"ID: {self.id}, text: {self.text}"
