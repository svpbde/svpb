"""Calculate year-end work statistics."""

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import translation
from django.db.models import Sum, Count

import arbeitsplan.models as models


class Command(BaseCommand):
    """Calculate year-end work statistics."""

    help = "Produce statistics for yearly analysis"

    def handle(self, *args, **options):
        # Set the locale right, to get the dates represented correctly
        translation.activate(settings.LANGUAGE_CODE)

        with open("leistungen.csv", "w") as csvfile:
            csvfile.write(
                "#AufgabeNr, Aufgabe, Gruppe, Angefordert(h), Geleistet(h), #Personen, "
                "#Durchschnitt\n"
            )
            # Get accepted Leistung objects and annotate them grouped by tasks
            annotated_tasks = (
                models.Leistung.objects.filter(status="AK")
                .values(
                    "aufgabe",
                    "aufgabe__aufgabe",
                    "aufgabe__anzahl",
                    "aufgabe__stunden",
                    "aufgabe__gruppe__gruppe",
                )
                .annotate(geleistet=Sum("zeit"))
                .annotate(melder=Count("melder", distinct=True))
            )

            for task in annotated_tasks:
                csvfile.write(
                    "{},{},{},{},{},{},{}\n".format(
                        task["aufgabe"],
                        task["aufgabe__aufgabe"].encode("utf8"),
                        task["aufgabe__gruppe__gruppe"].encode("utf8"),
                        task["aufgabe__anzahl"] * task["aufgabe__stunden"],
                        int(task["geleistet"]),
                        task["melder"],
                        float(task["geleistet"]) / task["melder"],
                    )
                )

        translation.deactivate()
