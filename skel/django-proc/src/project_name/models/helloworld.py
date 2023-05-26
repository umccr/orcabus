from django.db import models


class HelloWorldManager(models.Manager):
    pass


class HelloWorld(models.Model):
    id = models.BigAutoField(primary_key=True)
    text = models.CharField(max_length=255)

    objects = HelloWorldManager()

    def __str__(self):
        return f"ID: {self.id}, text: {self.text}"
