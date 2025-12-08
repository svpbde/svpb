"""Send email reminders to everybody who has a job coming up in the following days."""

import datetime
from collections import defaultdict

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import translation
from post_office import mail

import arbeitsplan.models as models


class Command(BaseCommand):
    """Notify on upcoming jobs in leaddays days.

    Grab all users which have a job starting in leaddays days.
    Send out emails to them.
    Store all those data in a list, to be sent to the corresponding
    responsible person as well.
    """

    help = "Send emails for upcoming jobs with given leaddays"

    def add_arguments(self, parser):
        parser.add_argument(
            "leaddays", type=int, help="days to look in the future for jobs"
        )

    def handle(self, *args, **options):
        # Set the locale right, to get the dates represented correctly
        translation.activate(settings.LANGUAGE_CODE)

        self.stdout.write("upcomingJob: Checking on " + str(datetime.date.today()))

        # Find out the target date to be used in zuteilung filter
        target_date = datetime.date.today() + datetime.timedelta(
            days=options["leaddays"]
        )

        zuteilung_target_date = models.Zuteilung.objects.filter(
            aufgabe__datum=target_date
        )

        self.stdout.write(
            f"upcomingJob: Found {zuteilung_target_date.count()} Zuteilungen "
            f"for {target_date}"
        )

        kontaktKontext = defaultdict(list)

        # Send mails to assigned members
        for z in zuteilung_target_date:
            kontakt = z.aufgabe.verantwortlich
            context = {
                "datum": z.aufgabe.datum,
                "u": z.ausfuehrer,
                "aufgabe": z.aufgabe,
                "a": z.aufgabe,
                "uhrzeit": z.stundenString(),
                "verantwortlich": kontakt,
            }

            kontaktKontext[kontakt].append(context)

            if z.ausfuehrer.email:
                mail.send(
                    [z.ausfuehrer.email],
                    template="upcomingJob",
                    context=context,
                )

        # For each verantwortlicher with a task someone has been reminded about, send
        # him/her an email reminding about the reminding
        for kontakt, liste in kontaktKontext.items():
            if kontakt.email:
                mail.send(
                    [kontakt.email],
                    template="upcomingJob-Kontakt",
                    context={
                        "liste": liste,
                        "verantwortlich": kontakt,
                        "aufgabe": z.aufgabe,
                    },
                    headers={
                        "Reply-to": (
                            z.aufgabe.verantwortlich.email
                            if z.aufgabe.verantwortlich.email
                            else settings.DEFAULT_FROM_EMAIL
                        ),
                    },
                )

        # And finally send out all queued mails
        call_command("send_queued_mail")

        translation.deactivate()
