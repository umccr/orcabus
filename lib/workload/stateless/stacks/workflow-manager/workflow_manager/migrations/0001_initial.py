# Generated by Django 5.1 on 2024-10-01 05:49

import django.core.serializers.json
import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Library',
            fields=[
                ('orcabus_id', models.CharField(editable=False, primary_key=True, serialize=False, unique=True, validators=[django.core.validators.RegexValidator(code='invalid_orcabus_id', message='ULID is expected to be 26 characters long', regex='[\\w]{26}$')])),
                ('library_id', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Payload',
            fields=[
                ('orcabus_id', models.CharField(editable=False, primary_key=True, serialize=False, unique=True, validators=[django.core.validators.RegexValidator(code='invalid_orcabus_id', message='ULID is expected to be 26 characters long', regex='[\\w]{26}$')])),
                ('payload_ref_id', models.CharField(max_length=255, unique=True)),
                ('version', models.CharField(max_length=255)),
                ('data', models.JSONField(encoder=django.core.serializers.json.DjangoJSONEncoder)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AnalysisContext',
            fields=[
                ('orcabus_id', models.CharField(editable=False, primary_key=True, serialize=False, unique=True, validators=[django.core.validators.RegexValidator(code='invalid_orcabus_id', message='ULID is expected to be 26 characters long', regex='[\\w]{26}$')])),
                ('name', models.CharField(max_length=255)),
                ('usecase', models.CharField(max_length=255)),
                ('description', models.CharField(max_length=255)),
                ('status', models.CharField(max_length=255)),
            ],
            options={
                'unique_together': {('name', 'usecase')},
            },
        ),
        migrations.CreateModel(
            name='Analysis',
            fields=[
                ('orcabus_id', models.CharField(editable=False, primary_key=True, serialize=False, unique=True, validators=[django.core.validators.RegexValidator(code='invalid_orcabus_id', message='ULID is expected to be 26 characters long', regex='[\\w]{26}$')])),
                ('analysis_name', models.CharField(max_length=255)),
                ('analysis_version', models.CharField(max_length=255)),
                ('description', models.CharField(max_length=255)),
                ('status', models.CharField(max_length=255)),
                ('contexts', models.ManyToManyField(to='workflow_manager.analysiscontext')),
            ],
        ),
        migrations.CreateModel(
            name='AnalysisRun',
            fields=[
                ('orcabus_id', models.CharField(editable=False, primary_key=True, serialize=False, unique=True, validators=[django.core.validators.RegexValidator(code='invalid_orcabus_id', message='ULID is expected to be 26 characters long', regex='[\\w]{26}$')])),
                ('analysis_run_name', models.CharField(max_length=255)),
                ('comment', models.CharField(blank=True, max_length=255, null=True)),
                ('status', models.CharField(blank=True, max_length=255, null=True)),
                ('analysis', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='workflow_manager.analysis')),
                ('approval_context', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approval_context', to='workflow_manager.analysiscontext')),
                ('project_context', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='project_context', to='workflow_manager.analysiscontext')),
                ('libraries', models.ManyToManyField(to='workflow_manager.library')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LibraryAssociation',
            fields=[
                ('orcabus_id', models.CharField(editable=False, primary_key=True, serialize=False, unique=True, validators=[django.core.validators.RegexValidator(code='invalid_orcabus_id', message='ULID is expected to be 26 characters long', regex='[\\w]{26}$')])),
                ('association_date', models.DateTimeField()),
                ('status', models.CharField(max_length=255)),
                ('library', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workflow_manager.library')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Workflow',
            fields=[
                ('orcabus_id', models.CharField(editable=False, primary_key=True, serialize=False, unique=True, validators=[django.core.validators.RegexValidator(code='invalid_orcabus_id', message='ULID is expected to be 26 characters long', regex='[\\w]{26}$')])),
                ('workflow_name', models.CharField(max_length=255)),
                ('workflow_version', models.CharField(max_length=255)),
                ('execution_engine', models.CharField(max_length=255)),
                ('execution_engine_pipeline_id', models.CharField(max_length=255)),
            ],
            options={
                'unique_together': {('workflow_name', 'workflow_version')},
            },
        ),
        migrations.AddField(
            model_name='analysis',
            name='workflows',
            field=models.ManyToManyField(to='workflow_manager.workflow'),
        ),
        migrations.CreateModel(
            name='WorkflowRun',
            fields=[
                ('orcabus_id', models.CharField(editable=False, primary_key=True, serialize=False, unique=True, validators=[django.core.validators.RegexValidator(code='invalid_orcabus_id', message='ULID is expected to be 26 characters long', regex='[\\w]{26}$')])),
                ('portal_run_id', models.CharField(max_length=255, unique=True)),
                ('execution_id', models.CharField(blank=True, max_length=255, null=True)),
                ('workflow_run_name', models.CharField(blank=True, max_length=255, null=True)),
                ('comment', models.CharField(blank=True, max_length=255, null=True)),
                ('analysis_run', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='workflow_manager.analysisrun')),
                ('libraries', models.ManyToManyField(through='workflow_manager.LibraryAssociation', to='workflow_manager.library')),
                ('workflow', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='workflow_manager.workflow')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='libraryassociation',
            name='workflow_run',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workflow_manager.workflowrun'),
        ),
        migrations.AlterUniqueTogether(
            name='analysis',
            unique_together={('analysis_name', 'analysis_version')},
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('orcabus_id', models.CharField(editable=False, primary_key=True, serialize=False, unique=True, validators=[django.core.validators.RegexValidator(code='invalid_orcabus_id', message='ULID is expected to be 26 characters long', regex='[\\w]{26}$')])),
                ('status', models.CharField(max_length=255)),
                ('timestamp', models.DateTimeField()),
                ('comment', models.CharField(blank=True, max_length=255, null=True)),
                ('payload', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='workflow_manager.payload')),
                ('workflow_run', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workflow_manager.workflowrun')),
            ],
            options={
                'unique_together': {('workflow_run', 'status', 'timestamp')},
            },
        ),
    ]
