"""Check values of choice fields in database for consistency."""
from django.core.management.base import BaseCommand
from django.utils import translation
from django.conf import settings

from arbeitsplan.models import Mitglied


class Command(BaseCommand):
    """Check values of choice fields in database for consistency.

    This command allows to check for values in the database which do not
    correspond to the allowed choices. As database entries are normally
    created by the web interface, which validates choice input, this
    command should actually not be necessary. However, there are some old
    entries in the database with inconsistent values, which can be fixed by
    this command.
    """
    help = "Check values of choice fields in database for consistency."

    def add_arguments(self, parser):
        parser.add_argument(
            "--auto-fix", action="store_true", help="Try to automatically fix problems"
        )

    def handle(self, *args, **options):
        # Set the locale right, to get the dates represented correctly
        translation.activate(settings.LANGUAGE_CODE)

        for member in Mitglied.objects.all():
            # Check status
            if member.status not in Mitglied.Status.values:
                print(f"Unknown status '{member.status}' for member {member}")
                if options["auto_fix"]:
                    if member.status == "Erwachsene":
                        member.status = Mitglied.Status.ADULT
                        member.save()
                        print(f"--> fixed to {member.status}")
                    elif member.status == "Kind in Familie":
                        member.status = Mitglied.Status.CHILD
                        member.save()
                        print(f"--> fixed to {member.status}")
                    else:
                        print("--> Sorry, no auto-fix available")

            # Check gender
            if member.gender not in Mitglied.Gender.values:
                print(f"Unknown gender '{member.gender}' for member {member}")
                if options["auto_fix"]:
                    if member.gender.upper() in Mitglied.Gender.values:
                        member.gender = member.gender.upper()
                        member.save()
                        print(f"--> fixed to {member.gender}")
                    else:
                        print("--> Sorry, no auto-fix available")

        translation.deactivate()
