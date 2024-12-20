# Generated by Django 5.1.2 on 2024-10-20 07:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0003_remove_userprofile_birth_date_userprofile_age_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="ticket",
            name="purchase_date",
        ),
        migrations.AddField(
            model_name="ticket",
            name="email",
            field=models.EmailField(default="dummy@example.com", max_length=254),
        ),
        migrations.AddField(
            model_name="ticket",
            name="phone_number",
            field=models.CharField(default="999999999", max_length=12),
        ),
        migrations.AddField(
            model_name="ticket",
            name="quantity",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
