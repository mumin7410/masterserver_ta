# Generated by Django 3.2.25 on 2024-11-10 08:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_transaction_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='camera_location',
            name='status',
            field=models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive')], default='inactive', max_length=10),
        ),
    ]
