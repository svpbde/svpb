# -*- coding: utf-8 -*-

import django_tables2
from django.contrib.auth.models import User


class MitgliederTable(django_tables2.Table):
    mitgliedsnummer = django_tables2.Column(accessor="mitglied.mitgliedsnummer")
    edit = django_tables2.TemplateColumn(
        "<a href=\"{% url 'accountOtherEdit' record.pk %}\"> Editieren </a></i>",
        verbose_name="Editieren",
        orderable=False,
        empty_values=(),
        )
    delete = django_tables2.TemplateColumn(
        "<a href=\"{% url 'accountDelete' record.pk %}\"> Löschen </a></i>",
        verbose_name="Löschen",
        orderable=False,
        empty_values=(),
        )

    class Meta:
        model = User
        attrs = {"class": "paleblue"}        
        fields = ('first_name',
                  'last_name',
                  'mitgliedsnummer',
                  'edit',
                  'delete',
                  )


class FilteredMemberTable(django_tables2.Table):
    member_number = django_tables2.Column(accessor="mitglied.mitgliedsnummer")
    workload = django_tables2.Column(accessor="mitglied.arbeitslast")
    status = django_tables2.Column(accessor="mitglied.status")
    age = django_tables2.Column(accessor="age")
    edit = django_tables2.TemplateColumn(
        "<a href=\"{% url 'accountOtherEdit' record.pk %}\"> Editieren </a></i>",
        verbose_name="Editieren",
        orderable=False,
        empty_values=(),
        )
    delete = django_tables2.TemplateColumn(
        "<a href=\"{% url 'accountDelete' record.pk %}\"> Löschen </a></i>",
        verbose_name="Löschen",
        orderable=False,
        empty_values=(),
        )

    class Meta:
        model = User
        attrs = {"class": "table table-hover table-striped"}
        template_name = "django_tables2/bootstrap-responsive.html"
        fields = ('first_name',
                  'last_name',
                  'member_number',
                  'status',
                  'age',
                  'workload',
                  'edit',
                  'delete',
                  )
