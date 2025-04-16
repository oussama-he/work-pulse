# Generated by Django 5.1.5 on 2025-04-16 09:31
from django.db import migrations, models



def alter_viewed_field_value(apps, schema_editor):
    Project = apps.get_model('core', 'Project')
    Project.objects.filter(viewed=True).update(viewed_new=models.F('updated'))


def backwards(apps, schema_editor):
    Project = apps.get_model('core', 'Project')
    Project.objects.filter(viewed_new__isnull=False).update(viewed=True)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_alter_project_url"),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='viewed_new',
            field=models.DateTimeField(null=True),
        ),
        migrations.RunPython(alter_viewed_field_value, backwards),
        migrations.RemoveField(
            model_name='project',
            name='viewed',
        ),
        migrations.RenameField(
            model_name='project',
            old_name='viewed_new',
            new_name='viewed',
        ),
        migrations.AlterModelOptions(
            name="project",
            options={"ordering": ["-viewed"]},
        ),
    ]