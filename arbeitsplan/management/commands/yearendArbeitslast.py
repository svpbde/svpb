"""Set arbeitslast of new users to default at the end of the year."""

import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string

import arbeitsplan.models as models


class Command(BaseCommand):
    """Set arbeitslast of new users to default at the end of the year.

    Command to run at the end of a year.
    Goal: Iterate over everybody registered in the second half of that year.
    Set the arbeitslast of those users to the default.
    Also, look for unusual arbeitslast settings.
    Notify the Geschäftsführer via mail.
    """

    help = (
        "Set all new members arbeitslast to standard value. New is anybody who joined "
        "in the second half of a year. Also, look for unusual arbeitslast settings."
    )

    def handle(self, *args, **options):
        thisyear = datetime.datetime.now().year
        midyear = datetime.datetime(thisyear, 7, 1)

        # Get members who joined after mid of year and exclude members not participating
        # in hour tracking or members who were already updated
        new_members = (
            models.Mitglied.objects.filter(user__date_joined__gte=midyear)
            .exclude(arbeitslast__gte=settings.BEGIN_CODED_HOURS_PER_YEAR)
            .exclude(arbeitslast=settings.JAHRESSTUNDEN)
        )

        old_working_hours = []

        for m in new_members:
            old_working_hours.append(m.arbeitslast)
            m.arbeitslast = settings.JAHRESSTUNDEN
            m.save()

        # Get members with unusual working hours
        unusual_members = (
            models.Mitglied.objects.filter(user__is_active=True)
            .exclude(arbeitslast__gte=settings.BEGIN_CODED_HOURS_PER_YEAR)
            .exclude(arbeitslast=settings.JAHRESSTUNDEN)
        )

        # Prepare and send mail
        subject = "Arbeitsstunden neuer Mitglieder auf Jahressoll angepasst"
        to_mail = settings.EMAIL_NOTIFICATION_BOARD
        from_mail = settings.DEFAULT_FROM_EMAIL

        body = render_to_string(
            "commands/yearend_arbeitslast_email.txt",
            context={
                # Convert zip to list, since empty zip doesn't evaluate to False
                "new_members_and_old_hours": list(zip(new_members, old_working_hours)),
                "unusual_members": unusual_members,
            },
        )

        send_mail(subject, body, from_mail, to_mail, fail_silently=False)
