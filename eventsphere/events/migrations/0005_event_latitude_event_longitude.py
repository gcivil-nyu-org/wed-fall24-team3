# Generated by Django 5.1.1 on 2024-10-24 19:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0004_remove_ticket_purchase_date_ticket_email_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="latitude",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="event",
            name="longitude",
            field=models.FloatField(blank=True, null=True),
        ),
    ]
