# Generated by Django 5.1.4 on 2024-12-17 01:44

import app.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_remove_historicalcontact_history_user_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='orcabus_id',
            field=app.fields.OrcaBusIdField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='historicalcontact',
            name='orcabus_id',
            field=app.fields.OrcaBusIdField(db_index=True),
        ),
        migrations.AlterField(
            model_name='historicalindividual',
            name='orcabus_id',
            field=app.fields.OrcaBusIdField(db_index=True),
        ),
        migrations.AlterField(
            model_name='historicallibrary',
            name='orcabus_id',
            field=app.fields.OrcaBusIdField(db_index=True),
        ),
        migrations.AlterField(
            model_name='historicalproject',
            name='orcabus_id',
            field=app.fields.OrcaBusIdField(db_index=True),
        ),
        migrations.AlterField(
            model_name='historicalsample',
            name='orcabus_id',
            field=app.fields.OrcaBusIdField(db_index=True),
        ),
        migrations.AlterField(
            model_name='historicalsubject',
            name='orcabus_id',
            field=app.fields.OrcaBusIdField(db_index=True),
        ),
        migrations.AlterField(
            model_name='individual',
            name='orcabus_id',
            field=app.fields.OrcaBusIdField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='library',
            name='orcabus_id',
            field=app.fields.OrcaBusIdField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='project',
            name='orcabus_id',
            field=app.fields.OrcaBusIdField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='sample',
            name='orcabus_id',
            field=app.fields.OrcaBusIdField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='subject',
            name='orcabus_id',
            field=app.fields.OrcaBusIdField(primary_key=True, serialize=False),
        ),
    ]
