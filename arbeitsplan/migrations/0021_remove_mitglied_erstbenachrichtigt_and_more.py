# Generated by Django 4.2.17 on 2025-02-12 21:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('arbeitsplan', '0020_auto_20240820_2016'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mitglied',
            name='erstbenachrichtigt',
        ),
        migrations.RemoveField(
            model_name='mitglied',
            name='zustimmungsDatum',
        ),
    ]
