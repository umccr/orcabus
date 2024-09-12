# Generated by Django 5.1.1 on 2024-09-12 01:20

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FastqPair',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('rgid', models.CharField(blank=True, max_length=255, null=True)),
                ('rgsm', models.CharField(blank=True, max_length=255, null=True)),
                ('rglb', models.CharField(blank=True, max_length=255, null=True)),
                ('coverage', models.CharField(blank=True, max_length=255, null=True)),
                ('quality', models.CharField(blank=True, max_length=255, null=True)),
                ('is_archived', models.BooleanField(blank=True, null=True)),
                ('is_compressed', models.BooleanField(blank=True, null=True)),
                ('read_1_id', models.CharField(blank=True, max_length=255, null=True)),
                ('read_2_id', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
