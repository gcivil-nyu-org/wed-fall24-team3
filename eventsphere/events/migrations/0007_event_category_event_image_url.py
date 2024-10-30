# Generated by Django 5.1.2 on 2024-10-28 03:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0006_userprofile_email"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="category",
            field=models.CharField(default="Popular", max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="event",
            name="image_url",
            field=models.URLField(blank=True, null=True),
        ),
    ]