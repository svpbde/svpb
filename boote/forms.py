from datetime import datetime, timedelta
import io
import locale

from crispy_forms.bootstrap import TabHolder, Tab
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout
from django import forms
from django.utils.safestring import mark_safe
from PIL import Image

from .custom_widgets import AdvancedFileInput
from .models import Boat


locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")


TIME = []
TIME.append(["-", "-"])
TIME.append(["08:00", "08:00"])
TIME.append(["08:30", "08:30"])
TIME.append(["09:00", "09:00"])
TIME.append(["09:30", "09:30"])
TIME.append(["10:00", "10:00"])
TIME.append(["10:30", "10:30"])
TIME.append(["11:00", "11:00"])
TIME.append(["11:30", "11:30"])
TIME.append(["12:00", "12:00"])
TIME.append(["12:30", "12:30"])
TIME.append(["13:00", "13:00"])
TIME.append(["13:30", "13:30"])
TIME.append(["14:00", "14:00"])
TIME.append(["14:30", "14:30"])
TIME.append(["15:00", "15:00"])
TIME.append(["15:30", "15:30"])
TIME.append(["16:00", "16:00"])
TIME.append(["16:30", "16:30"])
TIME.append(["17:00", "17:00"])
TIME.append(["17:30", "17:30"])
TIME.append(["18:00", "18:00"])
TIME.append(["18:30", "18:30"])
TIME.append(["19:00", "19:00"])

# Time for priority reservations has to be longer than time for standard bookings, as
# standard bookings may end at TIME[-1] + DURATION[-1].
# Note that PRIORITY_TIME is intentionally not set to 24 hours, as the booking views
# available to club members only show a limited time frame, i.e. bookings outside this
# frame wouldn't be noticed by anyone.
PRIORITY_TIME = [
    ["08:00", "08:00"],
    ["08:30", "08:30"],
    ["09:00", "09:00"],
    ["09:30", "09:30"],
    ["10:00", "10:00"],
    ["10:30", "10:30"],
    ["11:00", "11:00"],
    ["11:30", "11:30"],
    ["12:00", "12:00"],
    ["12:30", "12:30"],
    ["13:00", "13:00"],
    ["13:30", "13:30"],
    ["14:00", "14:00"],
    ["14:30", "14:30"],
    ["15:00", "15:00"],
    ["15:30", "15:30"],
    ["16:00", "16:00"],
    ["16:30", "16:30"],
    ["17:00", "17:00"],
    ["17:30", "17:30"],
    ["18:00", "18:00"],
    ["18:30", "18:30"],
    ["19:00", "19:00"],
    ["19:30", "19:30"],
    ["20:00", "20:00"],
    ["20:30", "20:30"],
    ["21:00", "21:00"],
    ["21:30", "21:30"],
    ["22:00", "22:00"],
]

DURATION = []
DURATION.append(["-", "-"])
DURATION.append(["60", "1 Stunde"])
DURATION.append(["90", "1.5 Stunden"])
DURATION.append(["120", "2 Stunden"])
DURATION.append(["150", "2.5 Stunden"])
DURATION.append(["180", "3 Stunden"])

BOOKING_TYPE = [
    ["AUS", "Ausbildung"],
    ["REG", "Regatta"],
    ["REP", "Reparatur"],
]

MONTHS = []
MONTHS.append(["01", "Januar"])
MONTHS.append(["02", "Februar"])
MONTHS.append(["03", "März"])
MONTHS.append(["04", "April"])
MONTHS.append(["05", "Mai"])
MONTHS.append(["06", "Juni"])
MONTHS.append(["07", "Juli"])
MONTHS.append(["08", "August"])
MONTHS.append(["09", "September"])
MONTHS.append(["10", "Oktober"])
MONTHS.append(["11", "November"])
MONTHS.append(["12", "Dezember"])

DAYS = []
for i in range(1, 10):
    DAYS.append(["0" + str(i), "0" + str(i)])
for i in range(10, 32):
    DAYS.append([str(i), str(i)])


class NewReservationForm(forms.Form):
    res_date = forms.ChoiceField(
        label="Datum",
        required=True,
        widget=forms.Select(attrs={"onChange": "showbooking()"}),
        choices=[],
    )
    res_start = forms.ChoiceField(
        label="Von",
        required=True,
        widget=forms.Select(attrs={"onChange": "showbooking()"}),
        choices=TIME,
    )
    res_duration = forms.ChoiceField(
        label="Dauer",
        required=True,
        widget=forms.Select(attrs={"onChange": "showbooking()"}),
        choices=DURATION,
    )

    accepted_agb = forms.BooleanField(
        label=mark_safe(
            "Ich akzeptiere die "
            "<a href='/static/boote/AllgRegelnVereinsboote.pdf' target='_blank'>"
            "Allgemeinen Regeln zur Nutzung der Vereinsboote</a>. Datenschutzhinweis: "
            "Durch die Reservierung wird mein Vor- und Nachname für bestehende oder "
            "angehende Vereinsmitglieder im internen und geschützen Bereich auf "
            "mein.svpb.de und auf dem Tabletdisplay im Vereinshaus zugänglich."
        ),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super(NewReservationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "id-reservation-form"
        self.helper.form_class = "blueForms"
        self.helper.form_method = "POST"

        # initialize DATES
        DATES = []
        d = datetime.now()
        for i in range(1, 7):
            d = d + timedelta(days=1)
            DATES.append([d.strftime("%Y-%m-%d"), d.strftime("%A (%d. %b)")])
        self.fields["res_date"] = forms.ChoiceField(
            label="Datum",
            required=True,
            widget=forms.Select(attrs={"onChange": "showbooking()"}),
            choices=DATES,
        )

        self.helper.add_input(Submit("submit", "Verbindlich reservieren"))

    def clean(self):
        cleaned_data = super(NewReservationForm, self).clean()

        # check date and time
        try:
            res_date = cleaned_data["res_date"]
            res_start = cleaned_data["res_start"]
        except KeyError:
            res_date = ""
            res_start = ""

        try:
            start = datetime.strptime(res_date + " " + res_start, "%Y-%m-%d %H:%M")
        except ValueError:
            raise forms.ValidationError("Bitte Datum und Uhrzeit auswählen.")

        # check duration
        res_duration = cleaned_data["res_duration"]
        try:
            res_duration = int(res_duration)
        except ValueError:
            raise forms.ValidationError("Bitte Dauer auswählen.")

        if res_duration < 30:
            raise forms.ValidationError("Minimal sind 30 Minuten möglich.")
        if res_duration > 180:
            raise forms.ValidationError("Maximal sind 3 Stunden möglich.")


class NewClubReservationForm(forms.Form):
    CBOATS = []

    try:
        club_boats = Boat.objects.filter(club_boat=True)
        for cb in club_boats:
            CBOATS.append([cb.pk, cb.name + " (" + cb.type.name + ")"])
    except Exception:
        pass

    res_type = forms.ChoiceField(
        label="Reservierungs-Typ",
        required=True,
        widget=forms.Select(),
        choices=BOOKING_TYPE,
    )
    res_boat = forms.MultipleChoiceField(
        label="Vereinsboot",
        required=True,
        widget=forms.CheckboxSelectMultiple,
        choices=CBOATS,
    )
    res_month = forms.ChoiceField(
        label="Monat", required=True, widget=forms.Select(), choices=MONTHS
    )
    res_day = forms.ChoiceField(
        label="Tag des Monats", required=True, widget=forms.Select(), choices=DAYS
    )
    res_start = forms.ChoiceField(
        label="Von",
        required=True,
        widget=forms.Select(),
        choices=PRIORITY_TIME,
        initial="08:00",
    )
    res_end = forms.ChoiceField(
        label="Bis",
        required=True,
        widget=forms.Select(),
        choices=PRIORITY_TIME,
        initial="22:00",
    )

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = "id-reservation-form-club"
        self.helper.form_class = "blueForms"
        self.helper.form_method = "POST"

        self.helper.add_input(Submit("submit", "Termin speichern"))
        super(NewClubReservationForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(NewClubReservationForm, self).clean()

        # check date and time
        now = datetime.now()
        res_year = now.year
        res_month = cleaned_data["res_month"]
        res_day = cleaned_data["res_day"]
        res_start = cleaned_data["res_start"]
        res_end = cleaned_data["res_end"]

        res_date = str(res_year) + "-" + res_month + "-" + res_day

        try:
            start = datetime.strptime(res_date + " " + res_start, "%Y-%m-%d %H:%M")
        except ValueError:
            raise forms.ValidationError("Bitte Datum und Start-Uhrzeit auswählen.")
        try:
            end = datetime.strptime(res_date + " " + res_end, "%Y-%m-%d %H:%M")
        except ValueError:
            raise forms.ValidationError("Bitte Datum und End-Uhrzeit auswählen.")

        if start >= end:
            raise forms.ValidationError("Das Ende muss nach dem Start sein.")


class BootIssueForm(forms.Form):
    res_reported_descr = forms.CharField(
        label="Beschreibung", required=True, widget=forms.Textarea
    )

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = "id-boot-issue"
        self.helper.form_class = "blueForms"
        self.helper.form_method = "POST"

        self.helper.add_input(Submit("submit", "Speichern"))
        super(BootIssueForm, self).__init__(*args, **kwargs)


class BootEditForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(BootEditForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = "id-boot-edit"
        self.helper.form_class = "blueForms"
        self.helper.form_method = "POST"

        self.helper.add_input(Submit("submit", "Speichern"))

        self.helper.layout = Layout(
            TabHolder(
                Tab(
                    "Hauptinformationen",
                    "active",
                    "type",
                    "name",
                    "remarks",
                ),
                Tab(
                    "Bild und Benutzungshinweise",
                    "photo",
                    "instructions",
                ),
                Tab("Reservierung", "club_boat", "briefing", "booking_remarks"),
            )
        )

        self.fields["booking_remarks"].required = False
        self.fields["booking_remarks"].label = "Wichtige Hinweise (Reservierung)"

        self.fields["briefing"].required = False
        self.fields["briefing"].label = "Einweisung"

        self.fields["club_boat"].label = "Vereinsboot"

        self.fields["photo"].required = False
        self.fields["photo"].label = "Bild (Format: JPG)"

        self.fields["instructions"].required = False
        self.fields["instructions"].label = "Hinweise zur Bootsbenutzung (Format: pdf)"

    def clean(self):
        super(BootEditForm, self).clean()

        # scale image
        image_field = self.cleaned_data.get("photo")
        if image_field:
            image_file = io.BytesIO(image_field.read())
            image = Image.open(image_file)
            w, h = image.size

            image = image.resize((400, int(400 * h / w)), Image.ANTIALIAS)

            image_file = io.BytesIO()
            image.save(image_file, "JPEG", quality=90)

            image_field.file = image_file

    class Meta:
        model = Boat
        exclude = ("owner",)
        widgets = {
            "remarks": forms.Textarea(attrs={"rows": 4, "cols": 15}),
            "booking_remarks": forms.Textarea(attrs={"rows": 4, "cols": 15}),
            "briefing": forms.Textarea(attrs={"rows": 4, "cols": 15}),
            "photo": AdvancedFileInput(),
        }
