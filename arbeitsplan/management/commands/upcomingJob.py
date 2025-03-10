"""
Define a command that should be run from a crontab
Send out emails to everybody who has a job coming up
on the following day.
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import translation
from django.conf import settings
from post_office import mail

import arbeitsplan.models as models

import datetime
from collections import defaultdict


class Command(BaseCommand):
    """Notify on upcoming jobs in leaddays days.

    Grab all users which have a job starting in leaddays days.
    Send out emails to them.
    Store all those data in a list, to be sent to the corresponding
    responsible person as well.
    """
    help = "Send emails for upcoming jobs with given leaddays"

    def add_arguments(self, parser):
        parser.add_argument('leaddays', type=int,
                            help="days to look in the future for jobs")

    def handle(self, *args, **options):
        # set the locale right, to get the dates represented correctly
        translation.activate(settings.LANGUAGE_CODE)

        self.stdout.write('upcomingJob: Checking on ' +
                          str(datetime.date.today()))

        # find out the date of tomorrow to be used in zuteilung filter
        tomorrow = (datetime.date.today() +
                    datetime.timedelta(days=options['leaddays']))

        zuteilungTomorrow = models.Zuteilung.objects.filter(
            aufgabe__datum=tomorrow)

        self.stdout.write('upcomingJob: Found {0} zuteilungen for {1}'
                          .format(
                              zuteilungTomorrow.count(),
                              str(tomorrow)))

        kontaktKontext = defaultdict(list)

        for z in zuteilungTomorrow:
            kontakt = z.aufgabe.kontakt()
            context = {'datum': z.aufgabe.datum,
                       'u': z.ausfuehrer,
                       'aufgabe': z.aufgabe,
                       'a': z.aufgabe,
                       'uhrzeit': z.stundenString(),
                       'verantwortlich': kontakt,
                       }

            kontaktKontext[kontakt].append(context)

            if z.ausfuehrer.email:
                mail.send(
                    [z.ausfuehrer.email],
                    template="upcomingJob",
                    context=context,
                    )

        # and for each verantwortlicher with a task someone
        # has been remained about,
        # send him/her an email reminding about the reminding

        for kontakt, liste in kontaktKontext.items():
            if kontakt.email:
                mail.send(
                    [kontakt.email],
                    template="upcomingJob-Kontakt",
                    context={'liste': liste,
                             'verantwortlich': kontakt,
                             'aufgabe': z.aufgabe,
                             },
                    headers={'Reply-to': (z.aufgabe.verantwortlich.email
                                          if z.aufgabe.verantwortlich.email
                                          else settings.DEFAULT_FROM_EMAIL), }
                    )

        # and finally send out all queued mails:
        call_command('send_queued_mail')

        translation.deactivate()
