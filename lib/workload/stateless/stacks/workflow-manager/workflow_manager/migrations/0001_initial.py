# Generated by Django 5.0.6 on 2024-05-17 20:10

import django.core.serializers.json
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Payload",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("payload_ref_id", models.CharField(max_length=255, unique=True)),
                ("version", models.CharField(max_length=255)),
                (
                    "data",
                    models.JSONField(
                        encoder=django.core.serializers.json.DjangoJSONEncoder
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Workflow",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("workflow_name", models.CharField(max_length=255)),
                ("workflow_version", models.CharField(max_length=255)),
                ("execution_engine", models.CharField(max_length=255)),
                ("execution_engine_pipeline_id", models.CharField(max_length=255)),
                ("approval_state", models.CharField(max_length=255)),
            ],
            options={
                "unique_together": {("workflow_name", "workflow_version")},
            },
        ),
        migrations.CreateModel(
            name="WorkflowRun",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("portal_run_id", models.CharField(max_length=255)),
                ("status", models.CharField(max_length=255)),
                ("timestamp", models.DateTimeField()),
                (
                    "execution_id",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "workflow_run_name",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("comment", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "payload",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="workflow_manager.payload",
                    ),
                ),
                (
                    "workflow",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="workflow_manager.workflow",
                    ),
                ),
            ],
            options={
                "unique_together": {("portal_run_id", "status", "timestamp")},
            },
        ),
    ]
