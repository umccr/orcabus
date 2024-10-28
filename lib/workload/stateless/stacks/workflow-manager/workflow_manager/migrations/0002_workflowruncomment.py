# Generated by Django 5.1 on 2024-10-22 06:53

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workflow_manager", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="WorkflowRunComment",
            fields=[
                (
                    "orcabus_id",
                    models.CharField(
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                code="invalid_orcabus_id",
                                message="ULID is expected to be 26 characters long",
                                regex="^[\\w]{26}$",
                            )
                        ],
                    ),
                ),
                ("comment", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.CharField(max_length=255)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(default=False)),
                (
                    "workflow_run",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comments",
                        to="workflow_manager.workflowrun",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
