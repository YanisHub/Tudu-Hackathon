# Generated by Django 5.2 on 2025-04-16 21:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_expertisearea_userprofile_userexpertise'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userexpertise',
            name='verification_method',
            field=models.CharField(blank=True, max_length=400, null=True),
        ),
    ]
