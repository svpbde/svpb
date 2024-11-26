"""Reset database at year end to prepare new year."""
from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import translation
from django.conf import settings

from arbeitsplan.models import Leistung, Zuteilung, Meldung


class Command(BaseCommand):
    """Reset database at year end to prepare new year.

    This command resets the database at year end by deleting all entries of
      - Leistung
      - Zuteilung
      - Meldung
      - Session (to ensure everyone is logged out)
      - Mails (deletion is not necessary, but keeps database clean)

    Tasks are kept deliberately, as they do not differ much over the years.
    """
    help = "Reset database at year end to prepare new year."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force", action="store_true", help="Do not ask interactive questions"
        )

    def handle(self, *args, **options):
        # Set the locale right, to get the dates represented correctly
        translation.activate(settings.LANGUAGE_CODE)

        if not options["force"]:
            choice = input("Are you sure you want to delete ALL entries? [y/N]: ")
            if choice != "y":
                return

        # Delete entries related to working hours
        num_deletions, per_object = Leistung.objects.all().delete()
        print(f"Leistung: Deleted {num_deletions} objects, consisting of {per_object}")
        num_deletions, per_object = Zuteilung.objects.all().delete()
        print(f"Zuteilung: Deleted {num_deletions} objects, consisting of {per_object}")
        num_deletions, per_object = Meldung.objects.all().delete()
        print(f"Meldung: Deleted {num_deletions} objects, consisting of {per_object}")

        # Delete sessions to ensure everyone is logged out
        num_deletions, per_object = Session.objects.all().delete()
        print(f"Session: Deleted {num_deletions} objects, consisting of {per_object}")

        # Delete mails
        call_command("cleanup_mail", days=0, delete_attachments=True)

        translation.deactivate()
