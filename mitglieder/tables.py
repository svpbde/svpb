# -*- coding: utf-8 -*-

import django_tables2
from django.contrib.auth.models import User


class MitgliederTable(django_tables2.Table):
    mitgliedsnummer = django_tables2.Column(accessor="mitglied.mitgliedsnummer")
    edit = django_tables2.TemplateColumn(
        "<a href=\"{% url 'accountOtherEdit' record.pk %}\"> Editieren </a>",
        verbose_name="Editieren",
        orderable=False,
        empty_values=(),
        )
    delete = django_tables2.TemplateColumn(
        "<a href=\"{% url 'accountDelete' record.pk %}\"> Löschen </a>",
        verbose_name="Löschen",
        orderable=False,
        empty_values=(),
        )

    class Meta:
        model = User
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
    age = django_tables2.Column(accessor="age", verbose_name="Alter")
    edit = django_tables2.TemplateColumn(
        "<a href=\"{% url 'accountOtherEdit' record.pk %}\"><i class=\"fa-solid fa-pen-to-square\"></i></a>",
        verbose_name="Editieren",
        orderable=False,
        empty_values=(),
        )
    delete = django_tables2.TemplateColumn(
        "<a href=\"{% url 'accountDelete' record.pk %}\"><i class=\"fa-solid fa-trash-can text-danger\"></i></a>",
        verbose_name="Löschen",
        orderable=False,
        empty_values=(),
        )

    class Meta:
        model = User
        fields = ('first_name',
                  'last_name',
                  'member_number',
                  'status',
                  'age',
                  'workload',
                  'edit',
                  'delete',
                  )
