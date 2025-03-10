# Generated by Django 4.2.17 on 2025-02-13 21:19

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arbeitsplan', '0021_remove_mitglied_erstbenachrichtigt_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mitglied',
            name='geburtsdatum',
            field=models.DateField(default=datetime.date(1900, 1, 1), verbose_name='Geburtsdatum'),
        ),
        migrations.AlterField(
            model_name='mitglied',
            name='zuteilungsbenachrichtigung',
            field=models.DateTimeField(default=datetime.datetime(1900, 1, 1, 0, 0, tzinfo=datetime.timezone.utc), help_text='Wann war die letzte Benachrichtigung zu einer Zuteilung?', verbose_name='Letzte Benachrichtigung'),
        ),
    ]
