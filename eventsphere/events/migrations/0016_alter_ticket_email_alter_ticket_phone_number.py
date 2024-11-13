# Generated by Django 5.1.1 on 2024-11-12 23:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0015_alter_ticket_email_alter_ticket_phone_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticket',
            name='email',
            field=models.EmailField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='phone_number',
            field=models.CharField(blank=True, max_length=12),
        ),
    ]
