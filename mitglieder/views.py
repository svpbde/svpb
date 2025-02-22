"""Views for anything that relates to administration of members.
Login and logout stays in SVPB
"""
from datetime import date
import os
import string
import secrets

from django.contrib.auth.decorators import user_passes_test
from django.core.management import call_command

from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.views.generic import View, FormView, CreateView, DeleteView
from django.utils.html import format_html
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import F
from django.shortcuts import redirect, get_object_or_404

from django.contrib.auth.models import User, Group

from post_office import mail
from post_office.models import EmailTemplate
from django_sendfile import sendfile

import mitglieder.forms
from arbeitsplan import forms
from arbeitsplan.tables import ImpersonateTable
from mitglieder.tables import MitgliederTable, FilteredMemberTable
from arbeitsplan.views import FilteredListView

from mitglieder.forms import (AccountEdit,
                              AccountOtherEdit,
                              MemberFilterForm,
                              MitgliederAddForm,
                              PersonMitgliedsnummer,
                              )
from arbeitsplan.models import Mitglied
from svpb.forms import MitgliederInactiveResetForm
from django.conf import settings
from svpb.views import isVorstandMixin, isVorstand


#-------------------------------------------------


def preparePassword(accountList=None):
    """For the given accounts, prepare the passwords and the PDFs for the letters

    Arguments:
    - `accountList`: List of User objects
    Returns:
    - List of tuples: (user object, PDF file)
    """

    from jinja2 import Template
    import codecs, subprocess

    r = []

    for u in accountList:
        pw = ''.join(
            secrets.choice(string.ascii_letters + string.digits) for i in range(10)
        )

        u.set_password(pw)
        u.save()

        r.append({'user': u,
                  'mitglied': u.mitglied,
                  'password': pw,
                  'status': u.mitglied.get_status_display(),
                  'geburtsdatum': u.mitglied.geburtsdatum.strftime('%d.%m.%Y'),
                  })

    # generate the PDF
    # assume the template is in templates

    templateText = EmailTemplate.objects.get(name='newUserLaTeX')

    rendered = Template(templateText.content).render(dicts=r)

    # and now process this via latex:
    f = codecs.open('letters.tex', 'w', 'utf-8')
    f.write(rendered)
    f.close()

    # TODO: use better file names, protect against race conditions

    retval = subprocess.call (["xelatex",
                                '-interaction=batchmode',
                                "letters.tex"])

    # move this file into a directory where only Vorstand has access!
    # remove an older letter first; ignore errors here
    import shutil, os
    try:
        os.remove(os.path.join(settings.SENDFILE_ROOT, 'letters.pdf'))
    except:
        pass

    shutil.move("letters.pdf", settings.SENDFILE_ROOT)

    return r

class AccountAdd(SuccessMessageMixin, isVorstandMixin, CreateView):
    model = Mitglied
    title = "Mitglied hinzufügen"
    template_name = "mitglied_form.html"
    form_class = MitgliederAddForm
    success_url = "/accounts"

    def get_context_data(self, **kwargs):
        context = super(AccountAdd, self).get_context_data(**kwargs)

        context['title'] = self.title

        return context

    def form_valid(self, form):
        # create User and Mitglied based on cleaned data

        # first, make some sanity checks to provide warnings
        u = User(first_name=form.cleaned_data['firstname'],
                 last_name=form.cleaned_data['lastname'],
                 is_active=False,
                 username=form.cleaned_data['mitgliedsnummer'],
                 email=form.cleaned_data['email'],
                 )

        u.set_password('test')
        u.save()

        m = u.mitglied

        m.user = u

        m.geburtsdatum = form.cleaned_data['geburtsdatum']
        m.mitgliedsnummer = form.cleaned_data['mitgliedsnummer']
        m.ort = form.cleaned_data['ort']
        m.plz = form.cleaned_data['plz']
        m.strasse = form.cleaned_data['strasse']
        m.gender = form.cleaned_data['gender']
        m.status = form.cleaned_data['status']
        m.arbeitlast = form.cleaned_data['arbeitslast']
        m.festnetz = form.cleaned_data['festnetz']
        m.mobil = form.cleaned_data['mobil']

        m.save()
        u.save()

        messages.success(self.request,
                         format_html(
                             "Nutzer {} {} (Nummer: {}, Account: {}) "
                             "wurde erfolgreich angelegt",
                             u.first_name,
                             u.last_name, m.mitgliedsnummer,
                             u.username
                             ))

        try:
            r = preparePassword([u])

            # copy the produced PDF to the SENDFILE_ROOT directory

            messages.success(self.request,
                             format_html(
                                 'Das Anschreiben mit Password kann '
                                 '<a href="{}">hier</a>'
                                 ' heruntergeladen werden.',
                                 'letters.pdf'
                                 ))

        except Exception as e:
            print("Fehler bei password: ", e)  # TODO: Log exception
            messages.error(self.request,
                           "Das Password für den Nutzer konnte nicht gesetzt werden "
                           "oder das Anschreiben nicht erzeugt werden. Bitten Sie das "
                           "neue Mitglied, sich über die Webseite selbst ein Password zu "
                           "generieren.")

        return redirect(self.success_url)


class AccountEdit(SuccessMessageMixin, FormView):
    template_name = "registration/justForm.html"
    form_class = AccountEdit
    success_url = "/"
    post_text = format_html("""
    <p>
    Passwort ändern? <a href="/password/change"> Hier klicken.</a>
    <p>
    """)

    def get_context_data(self, **kwargs):
        context = super(AccountEdit, self).get_context_data(**kwargs)
        context['title'] = "Meine Profildaten editieren"
        context['post_text'] = self.post_text
        return context

    def fillinUser(self, user):
        initial = {}
        initial['email'] = user.email
        initial['strasse'] = user.mitglied.strasse
        initial['plz'] = user.mitglied.plz
        initial['ort'] = user.mitglied.ort
        initial['geburtsdatum'] = user.mitglied.geburtsdatum
        initial['festnetz'] = user.mitglied.festnetz
        initial['mobil'] = user.mitglied.mobil

        return initial

    def get_initial(self):
        initial = super(AccountEdit, self).get_initial()
        initial.update(self.fillinUser(self.get_user()))
        return initial

    def storeUser(self, form, user):
        user.email = form.cleaned_data['email']
        user.mitglied.strasse = form.cleaned_data['strasse']
        user.mitglied.plz = form.cleaned_data['plz']
        user.mitglied.ort = form.cleaned_data['ort']
        user.mitglied.geburtsdatum = form.cleaned_data['geburtsdatum']
        user.mitglied.festnetz = form.cleaned_data['festnetz']
        user.mitglied.mobil = form.cleaned_data['mobil']

    def get_user(self):
        return self.request.user

    def form_valid(self, form):

        if form.has_changed():
            user = self.get_user()
            self.storeUser(form, user)

            user.save()
            user.mitglied.save()

            # inform the relevant Vorstand in charge of memberhsip
            mail.send(settings.EMAIL_NOTIFICATION_BOARD,
                      template="updatedProfile",
                      context={'user': user,
                               'mitglied': user.mitglied,
                               'changed': form.changed_data},
                      priority='now',
                      )

            messages.success(self.request,
                             format_html(
                                 "Das Profil {} {} ({}) wurde erfolgreich aktualisiert.",
                                 user.first_name, user.last_name,
                                 user.mitglied.mitgliedsnummer))
        else:
            messages.success(self.request,
                             "Keine Änderungen vorgenommen."
                             )

        return super(AccountEdit, self).form_valid(form)


class AccountOtherEdit(isVorstandMixin, AccountEdit):
    form_class = AccountOtherEdit
    post_text = ""

    def get_context_data(self, **kwargs):
        context = super(AccountOtherEdit, self).get_context_data(**kwargs)
        context['title'] = "Bearbeite das SVPB-Konto eines Mitgliedes"
        return context

    def fillinUser(self, user):      
        
        initial = super(AccountOtherEdit, self).fillinUser(user)
        initial['vorname'] = user.first_name
        initial['nachname'] = user.last_name
        initial['arbeitslast'] = user.mitglied.arbeitslast
        initial['status'] = user.mitglied.status
        initial['aktiv'] = user.is_active
        initial['boots_app'] = user.groups.filter(name='Boote').exists()

        return initial

    def storeUser(self, form, user):
        super(AccountOtherEdit, self).storeUser(form, user)
        user.first_name = form.cleaned_data['vorname']
        user.last_name = form.cleaned_data['nachname']
        user.is_active = form.cleaned_data['aktiv']
        user.mitglied.arbeitslast = form.cleaned_data['arbeitslast']
        user.mitglied.status = form.cleaned_data['status']

        # assign BOOTE group
        group_boots = Group.objects.get(name="Boote")
        if (form.cleaned_data['boots_app']):            
            user.groups.add(group_boots)
        else:
            user.groups.remove(group_boots)
        

    def get_user(self):
        userid = self.kwargs['id']
        user = get_object_or_404(User, pk=int(userid))
        return user


class AccountLetters(isVorstandMixin, View):
    """Check whether this user is allowed to download a letters.pdf file
    """

    def get(self, request):
        return sendfile(request,
                        os.path.join(settings.SENDFILE_ROOT,
                                "letters.pdf"))


class AccountList(SuccessMessageMixin, isVorstandMixin, FilteredListView):
    model = User
    template_name = "mitglieder_tff.html"

    title = "Mitglieder bearbeiten"

    # filterform_class = forms.NameFilterForm
    filterform_class = PersonMitgliedsnummer
    filtertile = "Mitglieder nach Vor- oder Nachnamen filtern"

    tabletitle = "Alle Mitglieder"
    tableClass = MitgliederTable

    filterconfig = [('first_name', 'first_name__icontains'),
                    ('last_name', 'last_name__icontains'),
                    ('mitgliedsnummer', 'mitglied__mitgliedsnummer__icontains'),
                    ]

    intro_text = mark_safe("""Diese Seite zeigt eine Liste aller Mitglieder an.
    Sie dient vor allem dazu, einzelne Mitglieder-Konten zu finden und zu editieren.
    Eine Übersicht über gemeldete, zugeteilte, erbrachte und akzeptieren
    Arbeitsstunden findet sich separat in der <a href="/arbeitsplan/salden/">Saldenübersicht</a>.
    """)


class AccountInactiveReset(FormView):
    """Für allen nicht-aktiven Accounts neue Passwörter erzeugen und PDF anlegen.
    """

    template_name = "inactive_reset.html"
    form_class = MitgliederInactiveResetForm
    success_url = "accounts/"

    def form_valid(self, form):

        if 'reset' in self.request.POST:
            userQs = User.objects.filter(is_active=False)

            try:
                r = preparePassword(userQs)

                # copy the produced PDF to the SENDFILE_ROOT directory

                messages.success(self.request,
                                 format_html(
                                     'Das Anschreiben mit Password kann '
                                     '<a href="{}">hier</a>'
                                     ' heruntergeladen werden.',
                                     'accounts/letters.pdf'
                                     ))

            except Exception as e:
                print("Fehler bei password: ", e)  # TODO: Log exception
                messages.error(self.request,
                               "Ein Password konnte nicht gesetzt werden "
                               "oder das Anschreiben nicht erzeugt werden. "
                               "Bitte benachrichtigen Sie den Administrator.")

        return redirect(self.success_url)


class AccountDelete(SuccessMessageMixin, isVorstandMixin, DeleteView):
    model = User
    success_url = reverse_lazy("accountList")
    # success_url = "/accounts/list"
    template_name = "user_confirm_delete.html"
    # success_message = "%(first_name) %(last_name) wurde gelöscht!"
    success_message = "Mitglied wurde gelöscht!"


class MitgliederExcel(View):
    """For Vorstand, send back an Excel file with all
    the Mitlgieders in various filtering combinations"""

    @method_decorator(user_passes_test(isVorstand, login_url="/keinVorstand/"))
    def get(self, request):

        if isVorstand(request.user):
            # call the command to prepare the excel file

            # repeated name; TODO: move this from here and mitgliedExcel.py into settings
            filename = "mitglieder.xlsx"
            basepath = settings.SENDFILE_ROOT

            call_command('mitgliedExcel')

            return sendfile(request,
                            os.path.join(basepath, filename))
        else:
            return redirect ("keinVorstand")


class ImpersonateListe(isVorstandMixin, FilteredListView):
    """Show a table with all Mitglieder,
    pick one to impersonate.
    Needs a suitable linked Column to point
    to impersonate/user-id
    """
    title = "Darzustellenden Nutzer auswählen"
    tableClass = ImpersonateTable
    tabletitle = "Mitglieder"
    model = User

    filterform_class = forms.NameFilterForm
    filterconfig = [('first_name', 'first_name__icontains'),
                    ('last_name', 'last_name__icontains'),
                    ]


    intro_text = """Sie können die Identität eines
    anderen Nutzers annehmen,
    beispielsweise um Meldungen oder Leistungen für diesen einzutragen.
    <p>
    Bitte gehen Sie verantwortlich mit dieser Möglichkeit um!
    <p>
    Beachten Sie: Diese Funktion funktioniert nicht bei Mitgliedern
    mit Sonderstatus (z.B. Adminstratoren dieser Webseite).
    """

    def get_data(self):
        return (self.model.objects
                .filter(is_active=True)
                .filter(is_staff=False)
                .filter(is_superuser=False)
                .exclude(id=self.request.user.id))


class FilteredMemberList(isVorstandMixin, FilteredListView):
    """Show a table with all members and several filter options.
    """
    title = "Mitglieder filtern"
    tableClass = FilteredMemberTable
    model = User

    template_name = "mitglieder_tff.html"

    filterform_class = MemberFilterForm
    filterconfig = [('first_name', 'first_name__icontains'),
                    ('last_name', 'last_name__icontains'),
                    ('member_number', 'mitglied__mitgliedsnummer__icontains'),
                    ('status', 'mitglied__status'),
                    ('age', 'age__gte')
                    ]

    intro_text = ("""Die Spalte Alter gibt an, wie alt das jeweilige Mitglied dieses Jahr wird.

    Interessante Ansichten:
    <ul>
        <li><a href="?filter=Filter+anwenden">Alle Mitglieder</a></li>
        <li><a href="?age=65&filter=Filter+anwenden ">Mitglieder ab 65 (Arbeitsdienst-befreit)</a></li>
        <li><a href="?status=Ss&filter=Filter+anwenden">Schüler/Studenten/...</a></li>
        <li><a href="?status=Ju&age=20&filter=Filter+anwenden">Jugendliche ab 20 (müssen Erwachsene werden)</a></li>
        <li><a href="?status=Ki&age=20&filter=Filter+anwende">Kinder in Familie ab 20 (müssen Erwachsene werden)</a></li>
        <li><a href="?status=Kf&age=20&filter=Filter+anwende">Beitragsfreie Kinder in Familie ab 20 (müssen Erwachsene werden)</a></li>
    </ul>
    """)

    def get_data(self):
        return (self.model.objects
                .filter(is_active=True)
                .annotate(age=date.today().year -
                          F('mitglied__geburtsdatum__year')))
