"""Notify members about assignments to tasks."""

from datetime import datetime, timezone

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import translation
from django.conf import settings
from post_office import mail

from arbeitsplan.models import Mitglied, Zuteilung


class Command(BaseCommand):
    """Notify members about assignments to tasks.

    This command sends a summary of all assignments to members, if something
    changed. It should be called once per night. Compared to directly sending
    notifications, this summary approach
        - Allows adding custom comments in ZuteilungEmailView
        - Prevents spamming of members with too many mails, if several
          assignments and timetable assignments are created successively
    Individual changes are not stored in the database, so this command always
    sends a summary of all existing assignments.
    """

    help = "Notify members about assignments to tasks."

    def handle(self, *args, **options):
        # Set the locale right, to get the dates represented correctly
        translation.activate(settings.LANGUAGE_CODE)

        # Get members with pending notification
        for member in Mitglied.objects.filter(zuteilungBenachrichtigungNoetig=True):
            # Prepare mail context
            context = {
                "first_name": member.user.first_name,
                "last_name": member.user.last_name,
                "u": member.user,
                "zuteilungen": Zuteilung.objects.filter(ausfuehrer=member.user),
            }
            # Add mail to queue
            mail.send([member.user.email], template="zuteilungEmail", context=context)

            # Clear pending notification
            member.zuteilungsbenachrichtigung = datetime.now(timezone.utc)
            member.zuteilungBenachrichtigungNoetig = False
            member.save()

        # Actually send mails
        call_command("send_queued_mail")

        translation.deactivate()
