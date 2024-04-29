# Generated by Django 3.2.23 on 2024-04-29 20:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boote', '0005_auto_20211021_1712'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='type',
            field=models.CharField(choices=[('PRV', 'Freie Nutzung'), ('AUS', 'Ausbildung'), ('REG', 'Regatta'), ('REP', 'Reparatur')], default='PRV', max_length=3),
        ),
    ]
