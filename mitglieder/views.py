"""Views for anything that relates to administration of members.
Login and logout stays in SVPB
"""

import codecs
import os
import secrets
import shutil
import string
import subprocess
from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import Group, User
from django.contrib.messages.views import SuccessMessageMixin
from django.core.management import call_command
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, DeleteView, FormView, View
from django_sendfile import sendfile
from jinja2 import Template
from post_office import mail
from post_office.models import EmailTemplate

from arbeitsplan import forms
from arbeitsplan.models import Mitglied
from arbeitsplan.tables import ImpersonateTable
from arbeitsplan.views import FilteredListView
from mitglieder.forms import (
    AccountEdit,
    AccountOtherEdit,
    MemberFilterForm,
    MitgliederAddForm,
    PersonMitgliedsnummer,
)
from mitglieder.tables import FilteredMemberTable, MitgliederTable
from svpb.forms import MitgliederInactiveResetForm
from svpb.views import isVorstand, isVorstandMixin


def preparePassword(accountList=None):
    """
    Generate random passwords for given user accounts and create a PDF letter for each.

    For each user in the account list, this function:
    - Generates a random 10-character password.
    - Sets and saves the password to the user.
    - Prepares data for rendering a LaTeX template.
    - Compiles the LaTeX file into a PDF using `xelatex`.
    - Moves the resulting PDF to a protected directory for Vorstand access.

    Args:
        accountList (list[User]): A list of Django User objects to process.

    Returns:
        list[dict]: List of dictionaries with user and password data used for rendering.

    Raises:
        EmailTemplate.DoesNotExist: If the "newUserLaTeX" template is not found.
        subprocess.CalledProcessError: If LaTeX compilation fails.
    """
    r = []
    for user in accountList:
        pw = "".join(
            secrets.choice(string.ascii_letters + string.digits) for i in range(10)
        )
        user.set_password(pw)
        user.save()
        r.append(
            {
                "user": user,
                "mitglied": user.mitglied,
                "password": pw,
                "status": user.mitglied.get_status_display(),
                "geburtsdatum": user.mitglied.geburtsdatum.strftime("%d.%m.%Y"),
            }
        )

    # Generate the PDF. Assume the template is in templates and process this via latex.
    templateText = EmailTemplate.objects.get(name="newUserLaTeX")
    rendered = Template(templateText.content).render(dicts=r)
    f = codecs.open("letters.tex", "w", "utf-8")
    f.write(rendered)
    f.close()
    # TODO: use better file names, protect against race conditions
    subprocess.call(["xelatex", "-interaction=batchmode", "letters.tex"])
    # Move this file into a directory where only Vorstand has access!
    # remove an older letter first; ignore errors here
    try:
        os.remove(os.path.join(settings.SENDFILE_ROOT, "letters.pdf"))
    except:
        pass
    shutil.move("letters.pdf", settings.SENDFILE_ROOT)
    return r


class AccountAdd(SuccessMessageMixin, isVorstandMixin, CreateView):
    """
    View for creating a new Mitglied (member) along with their associated User account.

    This view handles:
    - Creating and saving a new `User` object with inactive status by default.
    - Populating and saving the associated `Mitglied` object with additional details.
    - Assigning or removing the user from the 'Boote' group based on form input.
    - Generating a password and welcome letter PDF via `preparePassword`.
    - Displaying success or error messages to the admin user.

    Attributes:
        model (Model): The model backing the form (Mitglied).
        title (str): The page title.
        template_name (str): Template used for rendering the form.
        form_class (Form): The form class to use for member input.
        success_url (str): URL to redirect to after successful form submission.
    """

    model = Mitglied
    title = "Mitglied hinzufügen"
    template_name = "mitglied_form.html"
    form_class = MitgliederAddForm
    success_url = "/accounts"

    def get_context_data(self, **kwargs):
        """
        Extend the template context with a title.

        Args:
            **kwargs: Additional context arguments.

        Returns:
            dict: Context data for rendering the template.
        """
        context = super(AccountAdd, self).get_context_data(**kwargs)
        context["title"] = self.title
        return context

    def form_valid(self, form):
        """
        Handle the form submission for creating a new member and associated user.

        This method validates the form, creates a new inactive `User`, sets up
        `Mitglied` data, assigns permissions, and generates the welcome PDF with a
        random password.

        Args:
            form (Form): The validated form instance.

        Returns:
            HttpResponseRedirect: Redirect to the success URL.
        """

        user = User(
            first_name=form.cleaned_data["firstname"],
            last_name=form.cleaned_data["lastname"],
            is_active=False,
            username=form.cleaned_data["mitgliedsnummer"],
            email=form.cleaned_data["email"],
        )
        user.set_password("test")
        user.save()
        member = user.mitglied
        member.user = user
        member.geburtsdatum = form.cleaned_data["geburtsdatum"]
        member.mitgliedsnummer = form.cleaned_data["mitgliedsnummer"]
        member.ort = form.cleaned_data["ort"]
        member.plz = form.cleaned_data["plz"]
        member.strasse = form.cleaned_data["strasse"]
        member.gender = form.cleaned_data["gender"]
        member.status = form.cleaned_data["status"]
        member.arbeitlast = form.cleaned_data["arbeitslast"]
        member.festnetz = form.cleaned_data["festnetz"]
        member.mobil = form.cleaned_data["mobil"]
        member.user.is_active = form.cleaned_data["aktiv"]
        group_boots = Group.objects.get(name="Boote")
        if form.cleaned_data["boots_app"]:
            member.user.groups.add(group_boots)
        else:
            member.user.groups.remove(group_boots)
        member.save()
        user.save()
        messages.success(
            self.request,
            format_html(
                f"Nutzer {user.first_name} {user.last_name} \
                    (Nummer: {member.mitgliedsnummer}, \
                    Account: {user.username}) wurde erfolgreich angelegt",
            ),
        )
        try:
            preparePassword([user])
            # copy the produced PDF to the SENDFILE_ROOT directory
            messages.success(
                self.request,
                format_html(
                    "Das Anschreiben mit dem Passwort kann "
                    '<a href="{}">hier</a>'
                    " heruntergeladen werden.",
                    "letters.pdf",
                ),
            )
        except Exception as e:
            print("Fehler beim Passwort: ", e) #TODO: Log exception
            messages.error(
                self.request,
                "Das Passwort für den Nutzer konnte nicht gesetzt werden "
                "oder das Anschreiben nicht erzeugt werden. Bitte das neue Mitglied, "
                "sich über die Webseite selbst ein Passwort zu generieren.",
            )
        return redirect(self.success_url)


class AccountEdit(SuccessMessageMixin, FormView):
    """
    View that allows an authenticated user to edit their own account information.

    This class-based view presents a form for the logged-in user to update their
    account details (such as name, email, or profile information) and processes
    the form submission to save changes.

    Attributes:
        form_class (Form): The form class used to render and validate the update form.
        template_name (str): Template used to render the form view.
        success_url (str): URL to redirect to after a successful update.
        post_text (str): Additional text to be included in the form context.
    """
    template_name = "registration/justForm.html"
    form_class = AccountEdit
    success_url = "/"
    post_text = format_html(
        """<p>Passwort ändern? <a href="/password/change"> Hier klicken.</a><p>"""
    )

    def get_context_data(self, **kwargs):
        """
        Provides additional context for rendering the account edit form.

        This method adds custom context variables to the view’s context dictionary
        before rendering the template. It includes a title and a custom `post_text`
        for the page.

        Args:
            **kwargs: Additional keyword arguments passed to the context.

        Returns:
            dict: A dictionary of context data to render the view, including the
                  "title" and "post_text".
        """
        context = super(AccountEdit, self).get_context_data(**kwargs)
        context["title"] = "Meine Profildaten editieren"
        context["post_text"] = self.post_text

        return context

    def fetch_initial_data(self, user):
        """
        Prepares the initial data for the account editing form.

        This method retrieves the current user's account details (email, address,
        phone numbers, etc.) and prepares them as initial values for the form
        fields.

        Args:
            user (User): The authenticated user whose details are being edited.

        Returns:
            dict: A dictionary of initial values for the form fields, such as email,
                  address, birthdate, etc.
        """
        initial = {}
        initial["email"] = user.email
        initial["strasse"] = user.mitglied.strasse
        initial["plz"] = user.mitglied.plz
        initial["ort"] = user.mitglied.ort
        initial["geburtsdatum"] = user.mitglied.geburtsdatum
        initial["festnetz"] = user.mitglied.festnetz
        initial["mobil"] = user.mitglied.mobil

        return initial

    def get_initial(self):
        """
        Overrides the `get_initial` method to provide initial data for the form.

        This method ensures that the form is populated with the user's current
        account information when the page is first loaded. It combines the default
        initial data with custom initial values obtained from `fetch_initial_data`.

        Returns:
            dict: A dictionary of initial values to be pre-filled in the form.
        """
        initial = super(AccountEdit, self).get_initial()
        initial.update(self.fetch_initial_data(self.get_user()))
        return initial

    def save_changes(self, form, user):
        """
        Saves the changes made in the account editing form to the user's data.

        This method updates the user’s account information with the validated
        data from the form.

        Args:
            form (Form): The validated form containing the updated account data.
            user (User): The user whose account information is being updated.
        """
        user.email = form.cleaned_data["email"]
        user.mitglied.strasse = form.cleaned_data["strasse"]
        user.mitglied.plz = form.cleaned_data["plz"]
        user.mitglied.ort = form.cleaned_data["ort"]
        user.mitglied.geburtsdatum = form.cleaned_data["geburtsdatum"]
        user.mitglied.festnetz = form.cleaned_data["festnetz"]
        user.mitglied.mobil = form.cleaned_data["mobil"]

    def get_user(self):
        """
        Retrieves the currently authenticated user.

        This method returns the `User` object for the currently logged-in user.

        Returns:
            User: The authenticated user (the one who is editing their account).
        """
        return self.request.user

    def form_valid(self, form):
        """
        Handles a valid form submission and updates the user's account data.

        If there are changes in the form, this method stores the updated user data,
        saves the changes to the database, sends a notification email to the relevant
        board, and shows a success message. If no changes were made, it shows a message
        indicating that no updates were applied.

        Args:
            form (Form): The form containing the user’s updated account information.

        Returns:
            HttpResponseRedirect: Redirects to the success URL after the form is
                                  successfully submitted.
        """
        if form.has_changed():
            user = self.get_user()
            self.save_changes(form, user)

            user.save()
            user.mitglied.save()
            # Inform the relevant Vorstand in charge of memberhsip
            mail.send(
                settings.EMAIL_NOTIFICATION_BOARD,
                template="updatedProfile",
                context={
                    "user": user,
                    "mitglied": user.mitglied,
                    "changed": form.changed_data,
                },
                priority="now",
            )
            messages.success(
                self.request,
                format_html(
                    f"Das Profil {user.first_name} {user.last_name} \
                    ({user.mitglied.mitgliedsnummer}) wurde erfolgreich aktualisiert.",
                ),
            )
        else:
            messages.success(self.request, "Keine Änderungen vorgenommen.")
        return super(AccountEdit, self).form_valid(form)


class AccountOtherEdit(isVorstandMixin, AccountEdit):
    """
    View for editing the account details of another user, used by board members.

    Inherits from:
        - isVorstandMixin: Ensures only board members have access.
        - AccountEdit: Base class providing generic account editing functionality.

    Attributes:
        form_class (Form): The form class used for editing.
        post_text (str): Optional text displayed after form submission.
    """
    form_class = AccountOtherEdit
    post_text = ""

    def get_context_data(self, **kwargs):
        """
        Add custom context variables to the template context.

        Returns:
            dict: Context data including a custom title for the view.
        """
        context = super(AccountOtherEdit, self).get_context_data(**kwargs)
        context["title"] = "Bearbeite das SVPB-Konto eines Mitgliedes"
        return context

    def fetch_initial_data(self, user):
        """
        Prepare initial data for the form based on the given user.

        This method retrieves the current user's account details (email, address,
        phone numbers, etc.) and prepares them as initial values for the form
        fields.

        Args:
            user (User): The user whose data is being edited.

        Returns:
            dict: A dictionary of initial values for the form fields.
        """
        initial = super(AccountOtherEdit, self).fetch_initial_data(user)
        initial["vorname"] = user.first_name
        initial["nachname"] = user.last_name
        initial["arbeitslast"] = user.mitglied.arbeitslast
        initial["status"] = user.mitglied.status
        initial["aktiv"] = user.is_active
        initial["boots_app"] = user.groups.filter(name="Boote").exists()
        return initial

    def save_changes(self, form, user):
        """
        Save changes to the user and related models based on submitted form data.

        Args:
            form (Form): The validated form containing updated data.
            user (User): The user object to update.
        """
        super(AccountOtherEdit, self).save_changes(form, user)
        user.first_name = form.cleaned_data["vorname"]
        user.last_name = form.cleaned_data["nachname"]
        user.is_active = form.cleaned_data["aktiv"]
        user.mitglied.arbeitslast = form.cleaned_data["arbeitslast"]
        user.mitglied.status = form.cleaned_data["status"]
        group_boots = Group.objects.get(name="Boote")
        if form.cleaned_data["boots_app"]:
            user.groups.add(group_boots)
        else:
            user.groups.remove(group_boots)

    def get_user(self):
        """
        Retrieve the user object based on the 'id' URL parameter.

        Returns:
            User: The user instance corresponding to the provided ID.

        Raises:
            Http404: If no user with the given ID exists.
        """
        userid = self.kwargs["id"]
        user = get_object_or_404(User, pk=int(userid))
        return user


class AccountLetters(isVorstandMixin, View):
    """
    View that allows board members (Vorstand) to download the letters.pdf file.

    Access to the file is restricted via the isVorstandMixin.
    """

    def get(self, request):
        """
        Serve the letters.pdf file to the authorized user.

        Args:
            request (HttpRequest): The HTTP GET request.

        Returns:
            HttpResponse: The file response for letters.pdf.
        """
        return sendfile(request, os.path.join(settings.SENDFILE_ROOT, "letters.pdf"))


class AccountList(SuccessMessageMixin, isVorstandMixin, FilteredListView):
    """
    View for board members to filter and manage the list of member accounts.

    Includes filtering by name or member number, and displays results in a table.
    """

    model = User
    template_name = "mitglieder_tff.html"
    title = "Mitglieder bearbeiten"

    filterform_class = PersonMitgliedsnummer
    filtertile = "Mitglieder nach Vor- oder Nachnamen filtern"

    tabletitle = "Alle Mitglieder"
    tableClass = MitgliederTable

    filterconfig = [
        ("first_name", "first_name__icontains"),
        ("last_name", "last_name__icontains"),
        ("mitgliedsnummer", "mitglied__mitgliedsnummer__icontains"),
    ]

    intro_text = mark_safe(
        """Diese Seite zeigt eine Liste aller Mitglieder an. Sie dient vor allem dazu,
        einzelne Mitglieder-Konten zu finden und zu editieren. Eine Übersicht
        über gemeldete, zugeteilte, erbrachte und akzeptieren Arbeitsstunden findet
        sich separat in der <a href="/arbeitsplan/salden/">Saldenübersicht</a>.
        """
    )


class AccountInactiveReset(FormView):
    """
    View to generate new passwords and create a PDF letter for inactive user accounts.

    The generated PDF can be downloaded afterward by authorized users.
    """

    template_name = "inactive_reset.html"
    form_class = MitgliederInactiveResetForm
    success_url = "accounts/"

    def form_valid(self, form):
        """
        Handle valid form submission. If triggered via POST, create new passwords
        for all inactive users and generate a PDF document.

        Args:
            form (Form): The submitted and validated form.

        Returns:
            HttpResponseRedirect: Redirect to the success URL after processing.
        """
        if "reset" in self.request.POST:
            userQs = User.objects.filter(is_active=False)

            try:
                preparePassword(userQs)
                # Copy the produced PDF to the SENDFILE_ROOT directory
                messages.success(
                    self.request,
                    format_html(
                        "Das Anschreiben mit Password kann "
                        '<a href="{}">hier</a>'
                        " heruntergeladen werden.",
                        "accounts/letters.pdf",
                    ),
                )
            except Exception as e:
                print("Fehler bei password: ", e) # TODO: Log exception
                messages.error(
                    self.request,
                    "Ein Password konnte nicht gesetzt werden "
                    "oder das Anschreiben nicht erzeugt werden. "
                    "Bitte benachrichtigen Sie den Administrator.",
                )

        return redirect(self.success_url)


class AccountDelete(SuccessMessageMixin, isVorstandMixin, DeleteView):
    """
    View for deleting a member account, restricted to board members.

    Displays a confirmation page and provides a success message on completion.
    """

    model = User
    success_url = reverse_lazy("accountList")
    template_name = "user_confirm_delete.html"
    success_message = "Mitglied wurde gelöscht!"


class MitgliederExcel(View):
    """
    View to generate and return an Excel file listing all members.

    Only accessible to users with Vorstand privileges.
    """

    @method_decorator(user_passes_test(isVorstand, login_url="/keinVorstand/"))
    def get(self, request):
        """
        Handle GET request to generate and return the Excel file.

        Returns:
            HttpResponse: Excel file download if authorized.
            HttpResponseRedirect: Redirects to 'keinVorstand' if unauthorized.
        """
        if isVorstand(request.user):
            # Generate the Excel file using a management command.
            filename = "mitglieder.xlsx"
            basepath = settings.SENDFILE_ROOT
            # Repeated name, TODO: Move this command and mitgliedExcel.py into settings
            call_command("mitgliedExcel")
            return sendfile(request, os.path.join(basepath, filename))
        else:
            return redirect("keinVorstand")


class ImpersonateListe(isVorstandMixin, FilteredListView):
    """
    Display a list of active members to select one for impersonation.

    Only non-staff, non-superuser members are shown. Requires a table column that links
    to an impersonation URL (e.g., impersonate/<user-id>).
    """

    title = "Darzustellenden Nutzer auswählen"
    tableClass = ImpersonateTable
    tabletitle = "Mitglieder"
    model = User

    filterform_class = forms.NameFilterForm
    filterconfig = [
        ("first_name", "first_name__icontains"),
        ("last_name", "last_name__icontains"),
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
        """
        Return queryset of users eligible for impersonation.

        Filters out inactive users, staff members, superusers, and the current user.

        Returns:
            QuerySet: Filtered list of User objects.
        """
        return (
            self.model.objects.filter(is_active=True)
            .filter(is_staff=False)
            .filter(is_superuser=False)
            .exclude(id=self.request.user.id)
        )


class FilteredMemberList(isVorstandMixin, FilteredListView):
    """
    Display a filterable list of all active members with useful preset queries.

    This view shows additional information such as member status and calculated age.
    """

    title = "Mitglieder filtern"
    tableClass = FilteredMemberTable
    model = User

    template_name = "mitglieder_tff.html"

    filterform_class = MemberFilterForm
    filterconfig = [
        ("first_name", "first_name__icontains"),
        ("last_name", "last_name__icontains"),
        ("member_number", "mitglied__mitgliedsnummer__icontains"),
        ("status", "mitglied__status"),
        ("age", "age__gte"),
    ]

    intro_text = """
        Die Spalte Alter gibt an, wie alt das jeweilige Mitglied dieses Jahr wird.

        Interessante Ansichten:
        <ul>
            <li><a href="?filter=Filter+anwenden">Alle Mitglieder</a></li>
            <li><a href="?age=65&filter=Filter+anwenden ">
                Mitglieder ab 65 (Arbeitsdienst-befreit)
            </a></li>
            <li><a href="?status=Ss&filter=Filter+anwenden">
                Schüler/Studenten/...
            </a></li>
            <li><a href="?status=Ju&age=20&filter=Filter+anwenden">
                Jugendliche ab 20 (müssen Erwachsene werden)
            </a></li>
            <li><a href="?status=Ki&age=20&filter=Filter+anwende">
                Kinder in Familie ab 20 (müssen Erwachsene werden)
            </a></li>
            <li><a href="?status=Kf&age=20&filter=Filter+anwende">
                Beitragsfreie Kinder in Familie ab 20 (müssen Erwachsene werden)
            </a></li>
        </ul>
    """

    def get_data(self):
        """
        Return a queryset of active users annotated with their age.

        Age is calculated based on the current year and the user's birth year.

        Returns:
            QuerySet: Filtered and annotated list of User objects.
        """
        return self.model.objects.filter(is_active=True).annotate(
            age=date.today().year - F("mitglied__geburtsdatum__year")
        )
