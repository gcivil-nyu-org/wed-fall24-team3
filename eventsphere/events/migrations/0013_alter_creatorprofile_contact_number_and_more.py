# Generated by Django 5.1.1 on 2024-11-07 22:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0012_remove_creatorprofile_age_remove_creatorprofile_bio_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="creatorprofile",
            name="contact_number",
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name="creatorprofile",
            name="organization_email",
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name="creatorprofile",
            name="organization_name",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]