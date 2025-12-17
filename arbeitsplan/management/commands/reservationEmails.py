"""Send boat reservation and boat issue mails."""

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.template import loader, Context
from django.utils import translation
from post_office import mail

import boote.models as models


class Command(BaseCommand):
    """Send boat reservation and boat issue mails."""

    help = """Send boat reservation and boat issue mails."""

    def handle(self, *args, **options):
        # Set the locale right, to get the dates represented correctly
        translation.activate(settings.LANGUAGE_CODE)

        # EMAIL RESERVATION
        t = loader.get_template("boote/email_booking.html")
        # Get records
        for booking in models.Booking.objects.filter(notified=False).order_by("-date"):
            try:
                c = Context({"booking": booking})
                payload = t.render(c)
                sbj = (
                    "[SVPB] Reservierung ("
                    + booking.date.strftime("%d.%m.%Y")
                    + ") - "
                    + booking.boat.type.name
                    + ' "'
                    + booking.boat.name
                    + '"'
                )
                self.stdout.write("From: " + settings.DEFAULT_FROM_EMAIL)
                self.stdout.write("To: " + booking.user.email)
                self.stdout.write("Subject: " + sbj)
                self.stdout.write("Content:\n\r" + payload)

                mail.send(
                    [booking.user.email],
                    settings.DEFAULT_FROM_EMAIL,
                    subject=sbj,
                    html_message=payload,
                )

                booking.notified = True
                booking.save()
            except:
                print("Unexpected error ")

        call_command("send_queued_mail")

        translation.deactivate()
