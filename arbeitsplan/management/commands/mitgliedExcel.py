"""Create xlsx document with info and working hours of members."""

import os

from django.core.management.base import BaseCommand
from django.utils import timezone, translation
from django.conf import settings
import xlsxwriter
from xlsxcursor import XlsxCursor

import arbeitsplan.models as ap_models


def get_attribute(instance, name):
    """helper function: getattr does not follow foreign keys;
    this version here does.
    """

    if hasattr(instance, name):
        return getattr(instance, name)

    names = name.split("__")
    name = names.pop(0)
    if len(names) == 0:
        return ""

    if hasattr(instance, name):
        value = getattr(instance, name)
        return get_attribute(value, "__".join(names))

    return ""


class Command(BaseCommand):
    """Produce an Excel file of all the Mitglieder.

    Different filters are applied and output on separate sheets.
    """

    help = "Produce excel file of all Mitglieder"

    def ExcelExport(self, qs, cursor, mod=None):
        """Turn a query set into an Excel sheet.

        Args:
            - qs: Query set
            - cursor: XlsxCursor object
            - mod: Model with attribute excelFields defining properties to include in
                    Excel sheet (defaults to model of query set)
        """

        if not mod:
            mod = qs.model

        for fieldname, fieldkey in mod.excelFields:
            cursor(fieldname)

        cursor("Noch zu leistende Stunden")
        cursor.cr()

        row = 2
        for r in qs:
            for fieldname, fieldkey in mod.excelFields:
                a = get_attribute(r, fieldkey)
                if hasattr(a, "__call__"):
                    a = a()
                cursor(a)
            cursor("=MAX(0,J{}-R{})".format(row, row))
            cursor.cr()
            row += 1

    def createSheet(self, workbook, name, qs, mod=None):
        """Create sheet with info on Mitglieder.

        Args:
            - workbook: xlsxwriter Workbook object
            - name: Name of sheet
            - qs: Query set
            - mod: Model which contains fields to export in attribute excelFields
        """
        sheet = workbook.add_worksheet(name)
        sheet.set_column(0, 20, 15)
        cursor = XlsxCursor(workbook, sheet)
        self.ExcelExport(qs, cursor, mod)

    def uebersichtsblatt(self, workbook):
        """Create overview sheet with info on following sheets.

        Args:
            - workbook: xlsxwriter Workbook object
        """
        uebersicht = workbook.add_worksheet("Übersicht")
        uebersicht.set_column(0, 0, 30)
        uebersicht.set_column(1, 3, 60)
        cursor = XlsxCursor(workbook, uebersicht)
        cursor("Übersicht der einzelnen Kategorien")
        cursor.cr()
        cursor.cr()
        cursor("Alle Mitglieder")
        cursor("Alle aktiven Mitglieder")
        cursor.cr()

        cursor("Ehemalige Mitglieder")
        cursor("Ehemalige Mitglieder, die inaktiv in der Datenbank sind")
        cursor.cr()

        cursor("Ohne Meldung")
        cursor("Keine Meldung abgegeben")
        cursor(
            "Nicht unbedingt ein Problem; z.B. für Mitglieder, die direkt eingeteilt "
            "wurden"
        )
        cursor.cr()

        cursor("Ohne Zuteilung")
        cursor("Keine Aufgabe wurde zugeteilt")
        cursor(
            "Bedenklich (selbst Schnellzuweisung erstellt Zuteilung). "
            "Sollte zugeteilt werden!"
        )
        cursor.cr()

        cursor("Weder Meldung, noch Zuteilung")
        cursor("Weder Meldung abgeben, noch Zuteilung erfolgt.")
        cursor("Sehr bedenklich. Braucht Rücksprache, falls Arbeitslast.")
        cursor.cr()

        cursor("Leistungen unzureichend")
        cursor(
            "Arbeitslast größer als die akzeptierten geleisteten Stunden"
        )
        cursor(
            "Am Jahresende sind das die Mitglieder, von denen Geld abgebucht werden "
            "muss."
        )
        cursor.cr()
        cursor.cr()
        cursor("Stand der Daten")
        # Add date as string to circumvent dealing with excel's cell formating
        cursor(timezone.make_naive(timezone.now()).strftime("%d.%m.%Y %H:%M"))
        cursor.cr()

    def handle(self, *args, **options):
        # set the locale right, to get the dates represented correctly
        translation.activate(settings.LANGUAGE_CODE)

        # Create new file
        workbook = xlsxwriter.Workbook(
            os.path.join(settings.SENDFILE_ROOT, "mitglieder.xlsx")
        )
        # Add overview sheet
        self.uebersichtsblatt(workbook)

        # Add sheets with actual content
        self.createSheet(
            workbook,
            "Alle Mitglieder",
            ap_models.Mitglied.objects.filter(user__is_active=True),
        )

        self.createSheet(
            workbook,
            "Ehemalige Mitglieder",
            ap_models.Mitglied.objects.filter(user__is_active=False),
        )

        self.createSheet(
            workbook,
            "Ohne Meldung",
            [
                m
                for m in ap_models.Mitglied.objects.filter(user__is_active=True)
                if m.gemeldeteAnzahlAufgaben() == 0
            ],
            ap_models.Mitglied,
        )

        self.createSheet(
            workbook,
            "Ohne Zuteilung",
            [
                m
                for m in ap_models.Mitglied.objects.filter(user__is_active=True)
                if m.zugeteilteAufgaben() == 0
            ],
            ap_models.Mitglied,
        )

        self.createSheet(
            workbook,
            "Weder Meldung, noch Zuteilung",
            [
                m
                for m in ap_models.Mitglied.objects.filter(user__is_active=True)
                if (m.gemeldeteAnzahlAufgaben() == 0 and m.zugeteilteAufgaben() == 0)
            ],
            ap_models.Mitglied,
        )

        self.createSheet(
            workbook,
            "Leistungen unzureichend",
            [
                m
                for m in ap_models.Mitglied.objects.filter(user__is_active=True)
                if (m.arbeitslast > m.akzeptierteStunden())
            ],
            ap_models.Mitglied,
        )

        workbook.close()
        translation.deactivate()
