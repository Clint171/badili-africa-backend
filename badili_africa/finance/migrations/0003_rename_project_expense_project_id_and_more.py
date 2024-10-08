# Generated by Django 5.1.1 on 2024-09-19 08:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0002_remove_user_dob'),
    ]

    operations = [
        migrations.RenameField(
            model_name='expense',
            old_name='project',
            new_name='project_id',
        ),
        migrations.RenameField(
            model_name='expense',
            old_name='created_by',
            new_name='project_officer_id',
        ),
        migrations.RenameField(
            model_name='project',
            old_name='project_name',
            new_name='name',
        ),
        migrations.RemoveField(
            model_name='project',
            name='end_date',
        ),
        migrations.RemoveField(
            model_name='project',
            name='start_date',
        ),
        migrations.AddField(
            model_name='expense',
            name='project_name',
            field=models.CharField(default='project1', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='expense',
            name='project_officer',
            field=models.CharField(default='Clint', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='project',
            name='activities',
            field=models.TextField(default="['Visit girls school', 'Visit homes']"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='project',
            name='status',
            field=models.CharField(default='active', max_length=100),
            preserve_default=False,
        ),
    ]
