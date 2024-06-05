# Generated by Django 3.2.23 on 2024-06-04 20:40

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boote', '0006_alter_booking_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='boat',
            name='instructions',
            field=models.FileField(blank=True, upload_to='boat_instructions', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf'])]),
        ),
    ]
