"""Views for the entire svpb app

- Signal receiver to correctly create users
- Permission checks
- Logout
"""
from django.contrib.auth import logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import render
from django.utils.decorators import method_decorator

from arbeitsplan.models import Mitglied


@receiver(post_save, sender=User)
def create_mitglied(sender, instance, created, **kwargs):
    """Create a mitglied if a user is created (called via a Django signal)."""
    # Skip mitglied creation if called via 'manage.py loaddata', as fixtures
    # typically already include mitglied data. Without this, loading fixtures
    # with skipped primary key ids will throw the Exception
    # 'psycopg2.errors.UniqueViolation: duplicate key value violates unique
    # constraint "arbeitsplan_mitglied_user_id_key"'. See also
    # https://docs.djangoproject.com/en/4.2/topics/db/fixtures/#how-fixtures-are-saved-to-the-database
    if kwargs["raw"]:
        return
    if created:
        Mitglied.objects.get_or_create(user=instance)


def isVorstand(user):
    return user.groups.filter(name="Vorstand")


class isVorstandMixin(object):
    @method_decorator(user_passes_test(isVorstand, login_url="/keinVorstand/"))
    def dispatch(self, *args, **kwargs):
        return super(isVorstandMixin, self).dispatch(*args, **kwargs)


def logout_view(request):
    logout(request)
    return render(request, "registration/logged_out.html", {})
