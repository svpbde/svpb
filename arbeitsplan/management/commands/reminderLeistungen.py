"""Send email reminders that Leistungen should be processed."""

import datetime

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import translation
from post_office import mail

import arbeitsplan.models as models


class Command(BaseCommand):
    """Send email reminders that Leistungen should be processed.

    All Leistungen older than 7 days with status open or inquiry trigger an email to
    the person in charge of the Aufgabe.
    """

    help = "Send email reminders that Leistungsmeldungen should be processed."

    def handle(self, *args, **options):
        # Set the locale right, to get the dates represented correctly
        translation.activate(settings.LANGUAGE_CODE)

        offene_leistungen = (
            models.Leistung.objects.filter(
                erstellt__lte=datetime.date.today() - datetime.timedelta(days=7)
            )
            .exclude(status=models.Leistung.Status.ACCEPTED)
            .exclude(status=models.Leistung.Status.REJECTED)
        )

        kontakte = {leistung.aufgabe.verantwortlich for leistung in offene_leistungen}

        for k in kontakte:
            mail.send(
                [k.email],  # to address
                template="leistungReminder",
            )

        call_command("send_queued_mail")

        translation.deactivate()
