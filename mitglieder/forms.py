"""Forms related to handling Mitglieder data
"""
from crispy_bootstrap5.bootstrap5 import FloatingField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Div, Layout, Row, Submit
from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from phonenumber_field.formfields import PhoneNumberField

from arbeitsplan import models
from arbeitsplan.forms import (
    CrispyFilterMixin,
    MitgliedsnummerFilterForm,
    NameFilterForm,
)


class MitgliederAddForm(forms.ModelForm):
    """Form for adding a new member (Mitglied)."""

    firstname = forms.CharField(
        max_length=20,
        label="Vorname",
    )
    lastname = forms.CharField(
        max_length=20,
        label="Nachname",
    )
    email = forms.EmailField(label="E-Mail")
    aktiv = forms.BooleanField(
        initial=True,
        required=False,
        label="Aktiver Nutzer",
        help_text="Nur aktive Nutzer können sich einloggen.",
    )
    boats_app = forms.BooleanField(
        initial=True,
        required=False,
        label="Zugriff auf \"Boote und Kran\""
    )
    def __init__(self, *args, **kwargs):
        """Initializes the form and applies a custom layout using crispy-forms."""

        super(MitgliederAddForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column(
                    FloatingField("firstname"), css_class="form-group col-md-6 mb-0"
                ),
                Column(FloatingField("lastname"), css_class="form-group col-md-6 mb-0"),
            ),
            Row(
                Column(FloatingField("email"), css_class="form-group col-md-6 mb-0"),
                Column(
                    FloatingField("geburtsdatum", css_class="datepicker"),
                    css_class="form-group col-md-4 mb-0",
                ),
                Column(FloatingField("gender"), css_class="form-group col-md-2 mb-0"),
            ),
            Row(
                Column(FloatingField("strasse"), css_class="form-group col-md-6 mb-0"),
                Column(FloatingField("ort"), css_class="form-group col-md-4 mb-0"),
                Column(FloatingField("plz"), css_class="form-group col-md-2 mb-0"),
            ),
            Row(
                Column(FloatingField("festnetz"), css_class="form-group col-md-6 mb-0"),
                Column(FloatingField("mobil"), css_class="form-group col-md-6 mb-0"),
            ),
            Row(
                Column(
                    FloatingField("mitgliedsnummer"),
                    css_class="form-group col-md-4 mb-0",
                ),
                Column(FloatingField("status"), css_class="form-group col-md-4 mb-0"),
                Column(
                    FloatingField("arbeitslast"), css_class="form-group col-md-4 mb-0"
                ),
            ),
            Row(
                Column("boats_app", css_class="form-group col-md-6 mb-0"),
                Column("aktiv", css_class="form-group col-md-6 mb-0"),
            ),
        )
        self.helper.add_input(Submit("apply", "Mitglied anlegen"))

    def clean(self):
        """Validates the 'mitgliedsnummer' field.

        Ensures the input is a number and checks that no existing user
        already uses the given member number. Formats the number as a
        5-digit string (with leading zeros if needed).

        Returns:
            dict: The cleaned form data.

        Raises:
            ValidationError: If the input is not a number or already in use.
        """
        try:
            mnrnum = int(self.cleaned_data["mitgliedsnummer"])
        except:
            raise ValidationError(
                "Die Mitgliedsnummer muss eine Zahl sein (führende Nullen sind ok).",
                code="invalid",
            )

        # turn it back, search for such a user:
        mnr = "%05d" % mnrnum
        try:
            u = User.objects.get(username=mnr)
            raise ValidationError(
                f"Ein Nutzer mit dieser Mitgliedsnummer existiert bereits!\
                  ({u.first_name} {u.last_name}) Bitte wähle eine andere Nummer.",
                code="invalid",
            )
        except User.DoesNotExist:
            pass
        self.cleaned_data["mitgliedsnummer"] = mnr

        return self.cleaned_data

    class Meta:
        model = models.Mitglied
        fields = [
            "mitgliedsnummer",
            "geburtsdatum",
            "gender",
            "strasse",
            "plz",
            "ort",
            "festnetz",
            "mobil",
            "status",
            "arbeitslast",
        ]


class AccountEdit(forms.Form):
    """Form for editing a member's own account information."""

    email = forms.EmailField(required=True)
    strasse = forms.CharField(required=False)
    ort = forms.CharField(required=False)
    plz = forms.DecimalField(required=False)
    geburtsdatum = forms.DateField(required=False)
    festnetz = PhoneNumberField(required=False)
    mobil = PhoneNumberField(required=False)

    def computeLayout(self):
        """Constructs and returns the crispy-forms layout for this form.

        Returns:
            Layout: The crispy layout instance.
        """
        return Layout(
            Row(
                Column(FloatingField("email"), css_class="form-group col-md-8 mb-0"),
                Column(
                    FloatingField("geburtsdatum", css_class="datepicker"),
                    css_class="form-group col-md-4 mb-0",
                ),
            ),
            Row(
                Column(FloatingField("strasse"), css_class="form-group col-md-6 mb-0"),
                Column(FloatingField("ort"), css_class="form-group col-md-4 mb-0"),
                Column(FloatingField("plz"), css_class="form-group col-md-2 mb-0"),
            ),
            Row(
                Column(FloatingField("festnetz"), css_class="form-group col-md-6 mb-0"),
                Column(FloatingField("mobil"), css_class="form-group col-md-6 mb-0"),
            ),
        )

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        super(AccountEdit, self).__init__(*args, **kwargs)
        self.helper.form_id = self.__class__.__name__
        self.helper.form_method = "post"
        self.helper.layout = self.computeLayout()
        self.helper.add_input(Submit("apply", "Aktualisieren"))


class AccountOtherEdit(AccountEdit):
    """Extended version of AccountEdit for administrators editing other members."""

    vorname = forms.CharField(label="Vorname")
    nachname = forms.CharField(label="Nachname")
    arbeitslast = forms.IntegerField(
        required=False,
        label="Arbeitsstunden",
    )
    status = forms.ChoiceField(
        required=False,
        label="Mitgliedsstatus",
        choices=models.Mitglied.Status.choices,
    )
    aktiv = forms.BooleanField(
        required=False,
        label="Aktiver Nutzer",
        help_text="Nur aktive Nutzer können sich einloggen.",
    )
    boats_app = forms.BooleanField(
        required=False,
        label="Zugriff auf \"Boote und Kran\""
    )

    def computeLayout(self):
        """Constructs and returns the crispy-forms layout for this form.

        Returns:
            Layout: The crispy layout instance.
        """
        account_data = super(AccountOtherEdit, self).computeLayout()
        return Layout(
            Row(
                Column(FloatingField("vorname"), css_class="form-group col-md-6 mb-0"),
                Column(FloatingField("nachname"), css_class="form-group col-md-6 mb-0"),
            ),
            account_data,
            Row(
                Column(FloatingField("status"), css_class="form-group col-md-6 mb-0"),
                Column(
                    FloatingField("arbeitslast"), css_class="form-group col-md-6 mb-0"
                ),
            ),
            Row(
                Column("boats_app", css_class="form-group col-md-6 mb-0"),
                Column("aktiv", css_class="form-group col-md-6 mb-0"),
            ),
        )


class PersonMitgliedsnummer(NameFilterForm, MitgliedsnummerFilterForm):
    """Filter form combining name and member number fields."""
    pass


class MemberFilterForm(CrispyFilterMixin, forms.Form):
    """Filter form for searching members in a list view."""

    first_name = forms.CharField(label="Vorname", max_length=20, required=False)
    last_name = forms.CharField(label="Nachname", max_length=20, required=False)
    member_number = forms.CharField(
        required=False, label="Mitgliedsnummer", max_length=10
    )
    status = forms.ChoiceField(
        required=False,
        initial=False,
        label="Mitgliedsstatus",
        choices=(("", "Alle anzeigen"), *models.Mitglied.Status.choices),
    )
    age = forms.IntegerField(required=False, label="Alter ab")
    __layout = Layout("first_name", "last_name", "member_number", "status", "age")


class SVPBPasswordChangeForm(PasswordChangeForm):
    """Custom password change form using Django's built-in PasswordChangeForm."""

    def __init__(self, *args, **kwargs):
        super(SVPBPasswordChangeForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = self.__class__.__name__
        self.helper.form_method = "post"

        self.helper.layout = Layout(
            Div(
                FloatingField("old_password"),
                FloatingField("new_password1"),
                FloatingField("new_password2"),
                Submit("apply", "Passwort ändern"),
                css_class="w-100 m-auto",
                style="max-width: 530px;",
            )
        )
