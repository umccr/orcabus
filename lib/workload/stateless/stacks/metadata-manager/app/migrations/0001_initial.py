# Generated by Django 5.1 on 2024-09-19 01:23

import django.core.validators
import django.db.models.deletion
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('orcabus_id', models.CharField(editable=False, primary_key=True, serialize=False, unique=True, validators=[django.core.validators.RegexValidator(code='invalid_orcabus_id', message='ULID is expected to be 26 characters long', regex='[\\w]{26}$')])),
                ('contact_id', models.CharField(blank=True, null=True, unique=True)),
                ('name', models.CharField(blank=True, null=True)),
                ('description', models.CharField(blank=True, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Individual',
            fields=[
                ('orcabus_id', models.CharField(editable=False, primary_key=True, serialize=False, unique=True, validators=[django.core.validators.RegexValidator(code='invalid_orcabus_id', message='ULID is expected to be 26 characters long', regex='[\\w]{26}$')])),
                ('individual_id', models.CharField(blank=True, null=True, unique=True)),
                ('source', models.CharField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Sample',
            fields=[
                ('orcabus_id', models.CharField(editable=False, primary_key=True, serialize=False, unique=True, validators=[django.core.validators.RegexValidator(code='invalid_orcabus_id', message='ULID is expected to be 26 characters long', regex='[\\w]{26}$')])),
                ('sample_id', models.CharField(blank=True, null=True, unique=True)),
                ('external_sample_id', models.CharField(blank=True, null=True)),
                ('source', models.CharField(blank=True, choices=[('ascites', 'Ascites'), ('blood', 'Blood'), ('bone-marrow', 'BoneMarrow'), ('buccal', 'Buccal'), ('cell-line', 'Cell_line'), ('cfDNA', 'Cfdna'), ('cyst-fluid', 'Cyst Fluid'), ('DNA', 'Dna'), ('eyebrow-hair', 'Eyebrow Hair'), ('FFPE', 'Ffpe'), ('FNA', 'Fna'), ('OCT', 'Oct'), ('organoid', 'Organoid'), ('PDX-tissue', 'Pdx Tissue'), ('plasma-serum', 'Plasma Serum'), ('RNA', 'Rna'), ('tissue', 'Tissue'), ('skin', 'Skin'), ('water', 'Water')], null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='HistoricalContact',
            fields=[
                ('orcabus_id', models.CharField(db_index=True, editable=False, validators=[django.core.validators.RegexValidator(code='invalid_orcabus_id', message='ULID is expected to be 26 characters long', regex='[\\w]{26}$')])),
                ('contact_id', models.CharField(blank=True, db_index=True, null=True)),
                ('name', models.CharField(blank=True, null=True)),
                ('description', models.CharField(blank=True, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical contact',
                'verbose_name_plural': 'historical contacts',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalIndividual',
            fields=[
                ('orcabus_id', models.CharField(db_index=True, editable=False, validators=[django.core.validators.RegexValidator(code='invalid_orcabus_id', message='ULID is expected to be 26 characters long', regex='[\\w]{26}$')])),
                ('individual_id', models.CharField(blank=True, db_index=True, null=True)),
                ('source', models.CharField(blank=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical individual',
                'verbose_name_plural': 'historical individuals',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalLibrary',
            fields=[
                ('orcabus_id', models.CharField(db_index=True, editable=False, validators=[django.core.validators.RegexValidator(code='invalid_orcabus_id', message='ULID is expected to be 26 characters long', regex='[\\w]{26}$')])),
                ('library_id', models.CharField(blank=True, db_index=True, null=True)),
                ('phenotype', models.CharField(blank=True, choices=[('normal', 'Normal'), ('tumor', 'Tumor'), ('negative-control', 'Negative Control')], null=True)),
                ('workflow', models.CharField(blank=True, choices=[('clinical', 'Clinical'), ('research', 'Research'), ('qc', 'Qc'), ('control', 'Control'), ('bcl', 'Bcl'), ('manual', 'Manual')], null=True)),
                ('quality', models.CharField(blank=True, choices=[('very-poor', 'VeryPoor'), ('poor', 'Poor'), ('good', 'Good'), ('borderline', 'Borderline')], null=True)),
                ('type', models.CharField(blank=True, choices=[('10X', 'Ten X'), ('BiModal', 'Bimodal'), ('ctDNA', 'Ct Dna'), ('ctTSO', 'Ct Tso'), ('exome', 'Exome'), ('MeDIP', 'Me Dip'), ('Metagenm', 'Metagenm'), ('MethylSeq', 'Methyl Seq'), ('TSO-DNA', 'TSO_DNA'), ('TSO-RNA', 'TSO_RNA'), ('WGS', 'Wgs'), ('WTS', 'Wts'), ('other', 'Other')], null=True)),
                ('assay', models.CharField(blank=True, null=True)),
                ('coverage', models.FloatField(blank=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('sample', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='app.sample')),
            ],
            options={
                'verbose_name': 'historical library',
                'verbose_name_plural': 'historical librarys',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalProject',
            fields=[
                ('orcabus_id', models.CharField(db_index=True, editable=False, validators=[django.core.validators.RegexValidator(code='invalid_orcabus_id', message='ULID is expected to be 26 characters long', regex='[\\w]{26}$')])),
                ('project_id', models.CharField(blank=True, db_index=True, null=True)),
                ('name', models.CharField(blank=True, null=True)),
                ('description', models.CharField(blank=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical project',
                'verbose_name_plural': 'historical projects',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalSample',
            fields=[
                ('orcabus_id', models.CharField(db_index=True, editable=False, validators=[django.core.validators.RegexValidator(code='invalid_orcabus_id', message='ULID is expected to be 26 characters long', regex='[\\w]{26}$')])),
                ('sample_id', models.CharField(blank=True, db_index=True, null=True)),
                ('external_sample_id', models.CharField(blank=True, null=True)),
                ('source', models.CharField(blank=True, choices=[('ascites', 'Ascites'), ('blood', 'Blood'), ('bone-marrow', 'BoneMarrow'), ('buccal', 'Buccal'), ('cell-line', 'Cell_line'), ('cfDNA', 'Cfdna'), ('cyst-fluid', 'Cyst Fluid'), ('DNA', 'Dna'), ('eyebrow-hair', 'Eyebrow Hair'), ('FFPE', 'Ffpe'), ('FNA', 'Fna'), ('OCT', 'Oct'), ('organoid', 'Organoid'), ('PDX-tissue', 'Pdx Tissue'), ('plasma-serum', 'Plasma Serum'), ('RNA', 'Rna'), ('tissue', 'Tissue'), ('skin', 'Skin'), ('water', 'Water')], null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical sample',
                'verbose_name_plural': 'historical samples',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalSubject',
            fields=[
                ('orcabus_id', models.CharField(db_index=True, editable=False, validators=[django.core.validators.RegexValidator(code='invalid_orcabus_id', message='ULID is expected to be 26 characters long', regex='[\\w]{26}$')])),
                ('subject_id', models.CharField(blank=True, db_index=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical subject',
                'verbose_name_plural': 'historical subjects',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('orcabus_id', models.CharField(editable=False, primary_key=True, serialize=False, unique=True, validators=[django.core.validators.RegexValidator(code='invalid_orcabus_id', message='ULID is expected to be 26 characters long', regex='[\\w]{26}$')])),
                ('project_id', models.CharField(blank=True, null=True, unique=True)),
                ('name', models.CharField(blank=True, null=True)),
                ('description', models.CharField(blank=True, null=True)),
                ('contact_set', models.ManyToManyField(blank=True, related_name='project_set', to='app.contact')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Library',
            fields=[
                ('orcabus_id', models.CharField(editable=False, primary_key=True, serialize=False, unique=True, validators=[django.core.validators.RegexValidator(code='invalid_orcabus_id', message='ULID is expected to be 26 characters long', regex='[\\w]{26}$')])),
                ('library_id', models.CharField(blank=True, null=True, unique=True)),
                ('phenotype', models.CharField(blank=True, choices=[('normal', 'Normal'), ('tumor', 'Tumor'), ('negative-control', 'Negative Control')], null=True)),
                ('workflow', models.CharField(blank=True, choices=[('clinical', 'Clinical'), ('research', 'Research'), ('qc', 'Qc'), ('control', 'Control'), ('bcl', 'Bcl'), ('manual', 'Manual')], null=True)),
                ('quality', models.CharField(blank=True, choices=[('very-poor', 'VeryPoor'), ('poor', 'Poor'), ('good', 'Good'), ('borderline', 'Borderline')], null=True)),
                ('type', models.CharField(blank=True, choices=[('10X', 'Ten X'), ('BiModal', 'Bimodal'), ('ctDNA', 'Ct Dna'), ('ctTSO', 'Ct Tso'), ('exome', 'Exome'), ('MeDIP', 'Me Dip'), ('Metagenm', 'Metagenm'), ('MethylSeq', 'Methyl Seq'), ('TSO-DNA', 'TSO_DNA'), ('TSO-RNA', 'TSO_RNA'), ('WGS', 'Wgs'), ('WTS', 'Wts'), ('other', 'Other')], null=True)),
                ('assay', models.CharField(blank=True, null=True)),
                ('coverage', models.FloatField(blank=True, null=True)),
                ('project_set', models.ManyToManyField(blank=True, null=True, related_name='library_set', to='app.project')),
                ('sample', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.sample')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='HistoricalProject_contact_set',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('m2m_history_id', models.AutoField(primary_key=True, serialize=False)),
                ('contact', models.ForeignKey(blank=True, db_constraint=False, db_tablespace='', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='app.contact')),
                ('history', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, to='app.historicalproject')),
                ('project', models.ForeignKey(blank=True, db_constraint=False, db_tablespace='', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='app.project')),
            ],
            options={
                'verbose_name': 'HistoricalProject_contact_set',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalLibrary_project_set',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('m2m_history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, to='app.historicallibrary')),
                ('library', models.ForeignKey(blank=True, db_constraint=False, db_tablespace='', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='app.library')),
                ('project', models.ForeignKey(blank=True, db_constraint=False, db_tablespace='', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='app.project')),
            ],
            options={
                'verbose_name': 'HistoricalLibrary_project_set',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('orcabus_id', models.CharField(editable=False, primary_key=True, serialize=False, unique=True, validators=[django.core.validators.RegexValidator(code='invalid_orcabus_id', message='ULID is expected to be 26 characters long', regex='[\\w]{26}$')])),
                ('subject_id', models.CharField(blank=True, null=True, unique=True)),
                ('individual_set', models.ManyToManyField(blank=True, related_name='subject_set', to='app.individual')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='library',
            name='subject',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.subject'),
        ),
        migrations.CreateModel(
            name='HistoricalSubject_individual_set',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('m2m_history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, to='app.historicalsubject')),
                ('individual', models.ForeignKey(blank=True, db_constraint=False, db_tablespace='', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='app.individual')),
                ('subject', models.ForeignKey(blank=True, db_constraint=False, db_tablespace='', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='app.subject')),
            ],
            options={
                'verbose_name': 'HistoricalSubject_individual_set',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.AddField(
            model_name='historicallibrary',
            name='subject',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='app.subject'),
        ),
    ]
