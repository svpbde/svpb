"""Check consistency of Meldungen.

There should be at most one Meldung per Aufgabe, per User.
"""

import datetime

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import translation
from post_office import mail

import arbeitsplan.models as models


class Command(BaseCommand):
    """Check consistency of Meldungen.

    Go through all Users and Aufgaben. Check whether at most one Meldung exist.
    """

    help = "Check Meldung consistency, send out warning emails"

    def handle(self, *args, **options):
        # Set the locale right, to get the dates represented correctly
        translation.activate(settings.LANGUAGE_CODE)

        self.stdout.write(
            "check_meldung_consistency: Checking on " + str(datetime.date.today())
        )

        inconsistent_meldungen = []

        for u in models.User.objects.all():
            for a in models.Aufgabe.objects.all():
                mqs = models.Meldung.objects.filter(melder=u, aufgabe=a)
                c = mqs.count()
                if c > 1:
                    inconsistent_meldungen.append(mqs)

        if inconsistent_meldungen:
            message = "Folgende Meldungen liegen mehrfach vor:\r\n"
            message += "primary keys, Melder, Aufgabe\r\n"
            for entry in inconsistent_meldungen:
                message += (
                    f"{[meldung.pk for meldung in entry]}, {entry[0].melder}, "
                    f"{entry[0].aufgabe}\r\n"
                )
            print(message)

            subject = "[SVPB] Meldungen inkonsistent"

            mail.send(
                recipients=[mail for _, mail in settings.ADMINS],
                sender=settings.DEFAULT_FROM_EMAIL,
                subject=subject,
                message=message,
            )

            # Send out all queued mails
            call_command("send_queued_mail")

        translation.deactivate()
