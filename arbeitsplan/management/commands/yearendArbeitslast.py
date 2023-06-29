# -*- coding: utf-8 -*-
"""Set arbeitslast of new users to default at the end of the year."""
import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.mail import send_mail

import arbeitsplan.models as models


class Command(BaseCommand):
    """Set arbeitslast of new users to default at the end of the year.

    Command to run at the end of a year.
    Goal: Iterate over everybody registered in the second half of that year.
    Set the arbeitslast of those users to the default.
    Notify the Geschäftsführer via mail!
    """
    help = "Set all new Mitglieder's Arbeitslast to standard value. New is anybody how joined in the second half of a year"

    def handle(self, *args, **options):
        thisyear = datetime.datetime.now().year
        midyear = datetime.datetime(thisyear, 7, 1)

        newmitglieder = models.Mitglied.objects.filter(
            user__date_joined__gte=midyear)

        for m in newmitglieder:
            m.arbeitslast = settings.JAHRESSTUNDEN
            m.save()

        # Mail:
        subject = "Arbeitsstunden neuer Mitglieder auf Jahressoll angepasst"
        to = ['hkarl@ieee.org', 'dieter.peitz@svpb.de']
        fromEmail = "mein@svpb.de"

        body = """
Für folgende Mitglieder wurden die Arbeitsstunden auf das Jahressoll gesetzt:

{}

Ist das nicht korrekt, bitte die entsprechenden Mitglieder direkt in der Webseite editieren.

Rückfragen bitte an mein@svpb.de
        """.format('\n'.join(['- ' + str(m) for m in newmitglieder]))

        send_mail(subject,
                  body,
                  fromEmail,
                  to,
                  fail_silently=False)
