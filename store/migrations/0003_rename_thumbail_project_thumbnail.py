# Generated by Django 5.0.6 on 2024-09-02 06:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0002_rename_descriptiom_project_description'),
    ]

    operations = [
        migrations.RenameField(
            model_name='project',
            old_name='thumbail',
            new_name='thumbnail',
        ),
    ]
