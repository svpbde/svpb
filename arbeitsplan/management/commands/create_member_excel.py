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

        cursor("Keine Arbeitsdienst-Erfassung")
        cursor("Rentner, Vorstand, Personen mit festen Aufgaben")
        cursor(
            "Werden in nachfolgenden Tabellen nicht berücksichtigt. Können freiwillig "
            "trotzdem erfassen."
        )
        cursor.cr()

        cursor("Zuteilungen unzureichend")
        cursor("Zugeteilte Stunden reichen nicht, um Arbeitslast zu erfüllen")
        cursor(
            "Bedenklich (selbst Schnellzuteilung erstellt Zuteilung). "
            "Sollten weitere Meldungen abgeben bzw. zugeteilt werden!"
        )
        cursor.cr()

        cursor("Leistungen unzureichend")
        cursor("Arbeitslast größer als die akzeptierten geleisteten Stunden")
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
        cursor.cr()
        cursor("Hinweis für LibreOffice-Nutzer")
        cursor(
            'Wenn die letzte Spalte "Noch zu leistende Stunden" nur "0" anzeigt, bitte '
            'die Formeln "neu berechnen" (über Menü oder Tastenkombination '
            'Shift+Strg+F9).'
        )

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
            "Keine Arbeitsdienst-Erfassung",
            ap_models.Mitglied.objects.filter(
                user__is_active=True,
                arbeitslast__gte=settings.BEGIN_CODED_HOURS_PER_YEAR,
            ),
        )

        self.createSheet(
            workbook,
            "Zuteilungen unzureichend",
            [
                m
                for m in ap_models.Mitglied.objects.filter(
                    user__is_active=True
                ).exclude(arbeitslast__gte=settings.BEGIN_CODED_HOURS_PER_YEAR)
                if (
                    m.arbeitslast > m.akzeptierteStunden()
                    and m.arbeitslast > m.zugeteilteStunden()
                )
            ],
            ap_models.Mitglied,
        )

        self.createSheet(
            workbook,
            "Leistungen unzureichend",
            [
                m
                for m in ap_models.Mitglied.objects.filter(
                    user__is_active=True
                ).exclude(arbeitslast__gte=settings.BEGIN_CODED_HOURS_PER_YEAR)
                if (m.arbeitslast > m.akzeptierteStunden())
            ],
            ap_models.Mitglied,
        )

        workbook.close()
        translation.deactivate()
