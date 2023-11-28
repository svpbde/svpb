# -*- coding: utf-8 -*-

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Div, HTML
from django import forms
from django.core.exceptions import ValidationError
from crispy_bootstrap5.bootstrap5 import FloatingField


class LoginForm(forms.Form):
    username = forms.CharField(
        label="Mitgliedsnummer (fünfstellig)",
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        label="Passwort",
        required=True,
    )

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        super(LoginForm, self).__init__(*args, **kwargs)
        self.helper.form_id = self.__class__.__name__
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Div(
                Div(HTML("""<h3>Anmeldung</h3>"""), css_class="mb-3 fw-normal"),
                FloatingField("username"),
                FloatingField("password"),
                Submit("apply", "Anmelden", css_class="btn-primary w-100 py-2"),
                css_class="form-signin w-100 m-auto",
                style="max-width: 330px; padding: 1rem",
            )
        )

    def clean(self):
        from django.contrib.auth import authenticate

        error = False

        try:
            username = self.cleaned_data["username"]
            password = self.cleaned_data["password"]

            # print username, password
            user = authenticate(username=username, password=password)

            if user:
                self.cleaned_data["user"] = user
            else:
                error = True
        except:
            error = True

        if error:
            print("raising validation in Login", username)
            raise ValidationError("Der Nutzer konnte nicht angemeldet werden.")

        return self.cleaned_data


class MitgliederInactiveResetForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(MitgliederInactiveResetForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()

        self.helper.add_input(Submit("reset", "Passwörter zurücksetzen"))
        self.helper.add_input(Submit("nono", "Lieber nicht!"))
