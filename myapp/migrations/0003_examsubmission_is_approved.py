# Generated by Django 5.0.4 on 2024-04-22 13:47

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("myapp", "0002_examsubmission_is_graded"),
    ]

    operations = [
        migrations.AddField(
            model_name="examsubmission",
            name="is_approved",
            field=models.BooleanField(default=False),
        ),
    ]
