# Generated by Django 5.0 on 2024-03-27 03:22

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
            name='Individual',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('internal_id', models.CharField(blank=True, null=True, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Specimen',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('internal_id', models.CharField(blank=True, null=True, unique=True)),
                ('source', models.CharField(blank=True, choices=[('ascites', 'Ascites'), ('blood', 'Blood'), ('bone-marrow', 'Bone Marrow'), ('buccal', 'Buccal'), ('cell-line', 'Cellline'), ('cfDNA', 'Cfdna'), ('cyst-fluid', 'Cyst Fluid'), ('DNA', 'Dna'), ('eyebrow-hair', 'Eyebrow Hair'), ('FFPE', 'Ffpe'), ('FNA', 'Fna'), ('OCT', 'Oct'), ('organoid', 'Organoid'), ('PDX-tissue', 'Pdx Tissue'), ('plasma-serum', 'Plasma Serum'), ('RNA', 'Rna'), ('tissue', 'Tissue'), ('skin', 'Skin'), ('water', 'Water')], null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='HistoricalIndividual',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('internal_id', models.CharField(blank=True, db_index=True, null=True)),
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
            name='HistoricalSpecimen',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('internal_id', models.CharField(blank=True, db_index=True, null=True)),
                ('source', models.CharField(blank=True, choices=[('ascites', 'Ascites'), ('blood', 'Blood'), ('bone-marrow', 'Bone Marrow'), ('buccal', 'Buccal'), ('cell-line', 'Cellline'), ('cfDNA', 'Cfdna'), ('cyst-fluid', 'Cyst Fluid'), ('DNA', 'Dna'), ('eyebrow-hair', 'Eyebrow Hair'), ('FFPE', 'Ffpe'), ('FNA', 'Fna'), ('OCT', 'Oct'), ('organoid', 'Organoid'), ('PDX-tissue', 'Pdx Tissue'), ('plasma-serum', 'Plasma Serum'), ('RNA', 'Rna'), ('tissue', 'Tissue'), ('skin', 'Skin'), ('water', 'Water')], null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical specimen',
                'verbose_name_plural': 'historical specimens',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalSubject',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('internal_id', models.CharField(blank=True, db_index=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('individual', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='app.individual')),
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
            name='Library',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('internal_id', models.CharField(blank=True, null=True, unique=True)),
                ('phenotype', models.CharField(blank=True, choices=[('normal', 'Normal'), ('tumor', 'Tumor'), ('negative-control', 'Negative Control')], null=True)),
                ('workflow', models.CharField(blank=True, choices=[('clinical', 'Clinical'), ('research', 'Research'), ('qc', 'Qc'), ('control', 'Control'), ('bcl', 'Bcl'), ('manual', 'Manual')], null=True)),
                ('quality', models.CharField(blank=True, choices=[('very-poor', 'Very Poor'), ('poor', 'Poor'), ('good', 'Good'), ('borderline', 'Borderline')], null=True)),
                ('type', models.CharField(blank=True, choices=[('10X', 'Ten X'), ('ctDNA', 'Ct Dna'), ('ctTSO', 'Ct Tso'), ('exome', 'Exome'), ('Metagenm', 'Metagenm'), ('MethylSeq', 'Methyl Seq'), ('TSO-DNA', 'Tso Dna'), ('TSO-RNA', 'Tso Rna'), ('WGS', 'Wgs'), ('WTS', 'Wts'), ('BiModal', 'Bimodal'), ('other', 'Other')], null=True)),
                ('assay', models.CharField(blank=True, null=True)),
                ('coverage', models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True)),
                ('specimen', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.specimen')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='HistoricalLibrary',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('internal_id', models.CharField(blank=True, db_index=True, null=True)),
                ('phenotype', models.CharField(blank=True, choices=[('normal', 'Normal'), ('tumor', 'Tumor'), ('negative-control', 'Negative Control')], null=True)),
                ('workflow', models.CharField(blank=True, choices=[('clinical', 'Clinical'), ('research', 'Research'), ('qc', 'Qc'), ('control', 'Control'), ('bcl', 'Bcl'), ('manual', 'Manual')], null=True)),
                ('quality', models.CharField(blank=True, choices=[('very-poor', 'Very Poor'), ('poor', 'Poor'), ('good', 'Good'), ('borderline', 'Borderline')], null=True)),
                ('type', models.CharField(blank=True, choices=[('10X', 'Ten X'), ('ctDNA', 'Ct Dna'), ('ctTSO', 'Ct Tso'), ('exome', 'Exome'), ('Metagenm', 'Metagenm'), ('MethylSeq', 'Methyl Seq'), ('TSO-DNA', 'Tso Dna'), ('TSO-RNA', 'Tso Rna'), ('WGS', 'Wgs'), ('WTS', 'Wts'), ('BiModal', 'Bimodal'), ('other', 'Other')], null=True)),
                ('assay', models.CharField(blank=True, null=True)),
                ('coverage', models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('specimen', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='app.specimen')),
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
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('internal_id', models.CharField(blank=True, null=True, unique=True)),
                ('individual', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.individual')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='specimen',
            name='subjects',
            field=models.ManyToManyField(blank=True, to='app.subject'),
        ),
        migrations.CreateModel(
            name='HistoricalSpecimen_subjects',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('m2m_history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, to='app.historicalspecimen')),
                ('specimen', models.ForeignKey(blank=True, db_constraint=False, db_tablespace='', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='app.specimen')),
                ('subject', models.ForeignKey(blank=True, db_constraint=False, db_tablespace='', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='app.subject')),
            ],
            options={
                'verbose_name': 'HistoricalSpecimen_subjects',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
