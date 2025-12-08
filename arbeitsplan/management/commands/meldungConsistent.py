"""Check consistency of Meldungen.

There should be at most one Meldung per Aufgabe, per User.
"""

from collections import defaultdict
import datetime
import pprint

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import translation

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
            "meldungConsistent: Checking on " + str(datetime.date.today())
        )

        inconsistent_users = defaultdict(list)

        for u in models.User.objects.all():
            for a in models.Aufgabe.objects.all():
                mqs = models.Meldung.objects.filter(melder=u, aufgabe=a)
                c = mqs.count()
                if c > 1:
                    inconsistent_users[u].append(a)

        print(inconsistent_users)

        if inconsistent_users:
            subject = "SVPB: PROBLEM with Meldungenkonsistenz"
            body = pprint.pformat(inconsistent_users)
        else:
            subject = "SVPB: Meldungen all good"
            body = "rechoice"

        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            ["d.dimka89@gmail.com"],
            fail_silently=False,
        )
        translation.deactivate()
