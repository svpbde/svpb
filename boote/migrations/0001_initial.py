# -*- coding: utf-8 -*-


from django.db import models, migrations
import datetime
from django.conf import settings
import boote.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Boat',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('photo', models.ImageField(null=True, upload_to=boote.models.boat_img_path)),
                ('name', models.CharField(max_length=30)),
                ('remarks', models.CharField(max_length=2000, null=True)),
                ('club_boat', models.BooleanField(default=False)),
                ('booking_remarks', models.CharField(default='', max_length=2000, null=True)),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.PROTECT)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BoatIssue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.IntegerField(default=1)),
                ('reported_date', models.DateField()),
                ('reported_descr', models.CharField(max_length=2000)),
                ('fixed_date', models.DateField(null=True)),
                ('fixed_descr', models.CharField(max_length=2000, null=True)),
                ('boat', models.ForeignKey(to='boote.Boat', on_delete=models.CASCADE)),
                ('fixed_by', models.ForeignKey(related_name='user_fixing', to=settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)),
                ('reported_by', models.ForeignKey(related_name='user_reporting', to=settings.AUTH_USER_MODEL, on_delete=models.SET_NULL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BoatType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=30)),
                ('url', models.CharField(max_length=256)),
                ('length', models.CharField(max_length=15)),
                ('beam', models.CharField(max_length=15)),
                ('draught', models.CharField(max_length=15)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_date', models.DateField(default=datetime.datetime.now)),
                ('status', models.IntegerField(default=1)),
                ('type', models.CharField(default='PRV', max_length=3, choices=[('PRV', 'Freie Nutzung'), ('AUS', 'Ausbildung'), ('REG', 'Regatta')])),
                ('date', models.DateField()),
                ('time_from', models.TimeField()),
                ('time_to', models.TimeField()),
                ('boat', models.ForeignKey(to='boote.Boat', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.SET_NULL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='boat',
            name='type',
            field=models.ForeignKey(to='boote.BoatType', on_delete=models.SET_NULL),
            preserve_default=True,
        ),
    ]
