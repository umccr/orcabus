# Generated by Django 5.1.4 on 2025-01-22 11:09

import sequence_run_manager.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "sequence_run_manager",
            "0003_alter_comment_orcabus_id_alter_sequence_orcabus_id_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="comment",
            name="association_id",
            field=sequence_run_manager.fields.OrcaBusIdField(),
        ),
    ]
