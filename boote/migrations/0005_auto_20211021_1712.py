# Generated by Django 3.2.8 on 2021-10-21 15:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('boote', '0004_boat_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='boat',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='boote.boattype'),
        ),
        migrations.AlterField(
            model_name='boatissue',
            name='reported_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='user_reporting', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='booking',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
