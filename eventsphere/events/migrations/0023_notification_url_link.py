# Generated by Django 5.1.2 on 2024-11-26 18:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0022_notification_sub_title_notification_title_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="notification",
            name="url_link",
            field=models.CharField(default="https://www.google.com/", max_length=2083),
            preserve_default=False,
        ),
    ]
