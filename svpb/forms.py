from crispy_bootstrap5.bootstrap5 import FloatingField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Div, HTML
from django import forms
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.html import format_html

from svpb.views import isVorstand


class SVPBAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if not user.is_active:
            # This should not occur, as Django's default authentication ModelBackend
            # prohibits inactive users from logging in. However, rejecting inactive
            # users is also the default in Django's default AuthenticationForm, so just
            # replicate it here.
            raise ValidationError(
                "Dieser Account ist inaktiv.",
                code="inactive",
            )
        if settings.JAHRESENDE and not isVorstand(user):
            raise ValidationError(
                "Derzeit ist eine Anmeldung nur für Vorstände möglich.",
                code="no_board_member",
            )

        # Create messages to be displayed after successful login
        if settings.JAHRESENDE:
            messages.warning(
                self.request,
                format_html(
                    "Jahresende-Modus! Bitte <b>vor allem die Aufgaben</b> bearbeiten -"
                    " Datum prüfen, ggf. direkt Mitglieder zuteilen!"
                ),
            )
        missing_fields = user.mitglied.profileIncomplete()
        if missing_fields:
            messages.warning(
                self.request,
                format_html(
                    "Deine Profilangaben sind unvollständig.<br>"
                    "Es fehlt/fehlen: {}.<br>"
                    'Bitte ergänze <a href="/accounts/edit/">dein Profil.</a>',
                    missing_fields,
                ),
            )

    def __init__(self, *args, **kwargs):
        super(SVPBAuthenticationForm, self).__init__(*args, **kwargs)
        self.fields["username"].label = "Mitgliedsnummer (fünfstellig)"
        self.helper = FormHelper()
        self.helper.form_id = self.__class__.__name__
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Div(
                Div(HTML("""<h3>Anmeldung</h3>"""), css_class="mb-3 fw-normal"),
                FloatingField("username", autocomplete="username"),
                FloatingField("password"),
                Submit("apply", "Anmelden", css_class="btn-primary w-100 py-2"),
                css_class="w-100 m-auto",
                style="max-width: 330px; padding: 1rem",
            )
        )


class MitgliederInactiveResetForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(MitgliederInactiveResetForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()

        self.helper.add_input(Submit("reset", "Passwörter zurücksetzen"))
        self.helper.add_input(Submit("nono", "Lieber nicht!"))
