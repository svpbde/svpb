from crispy_forms.bootstrap import FormActions, InlineCheckboxes, InlineField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, HTML
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django_select2.forms import Select2Widget, Select2MultipleWidget

from . import models


class CrispyFormMixin(object):
    """Define basic crispy fields
    """

    def __init__(self, *args, **kwargs):
        """
        Add the necessary attributes for crispy to work,
        after the superclass constructur has done its work.
        Arguments:
        - `*args`:
        - `**kwargs`:
        """

        super(CrispyFormMixin, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = self.__class__.__name__
        self.helper.form_method = "post"
        # self.helper.field_template = "bootstrap3/layout/inline_field.html"

##############################
## General input forms
##############################


class CreateLeistungForm(CrispyFormMixin, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        try:
            user = kwargs.pop('user')
        except:
            user = None
            
        super(CreateLeistungForm, self).__init__(*args, **kwargs)

        if user:
            # filter out the Aufgaben for which the user has a Zuteilung: 
            zuteilungQs = models.Zuteilung.objects.filter(ausfuehrer=user)
            # and get the Aufgaben from this zuteliung:
            aufgabenQs = models.Aufgabe.objects.filter(zuteilung__in=zuteilungQs)
            self.fields['aufgabe'].queryset = aufgabenQs
        
        self.helper.layout = Layout(
            'aufgabe',
            Field('wann', css_class="datepicker"),
            'zeit',
            # 'auslagen',
            # 'km',
            'bemerkung',
            )

        self.helper.add_input(Submit ('apply', 'Eintragen'))

    class Meta:
        model = models.Leistung
        exclude = ('melder',
                   'erstellt',
                   'veraendert',
                   'status',
                   'bemerkungVorstand',
                   )


class AufgabengruppeForm(CrispyFormMixin, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(AufgabengruppeForm, self).__init__(*args, **kwargs)
        self.helper.form_tag = False

    class Meta:
        model = models.Aufgabengruppe
        fields = ('gruppe',
                  'verantwortlich',
                  'bemerkung',
                  )


class AufgabeForm(forms.ModelForm):
    schnellzuweisung = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True).all(),
        label="Direkt Zuteilung an ausführende(s) Mitglied(er) erstellen/löschen",
        help_text=(
            "Wenn bereits fest steht, wer diese Aufgabe ausführt, kann hier direkt eine"
            " Zuteilung an das/die Mitglied(er) erstellt werden. Eine separate Meldung "
            "und Zuteilung ist dann nicht mehr nötig. Löschen entfernt die Zuteilung."
        ),
        required=False,
        # Force data-width to 100% to keep select2 from calculating a
        # fixed width (which would break responsiveness), see
        # https://select2.org/appearance#container-width
        widget=Select2MultipleWidget({"data-width": "100%"}),
    )

    class Meta:
        model = models.Aufgabe
        fields = (
            "aufgabe",
            "verantwortlich",
            "gruppe",
            "anzahl",
            "stunden",
            "teamleader",
            "datum",
            "bemerkung",
        )
        widgets = {
            # Force data-width to 100% to keep select2 from calculating a
            # fixed width (which would break responsiveness), see
            # https://select2.org/appearance#container-width
            "verantwortlich": Select2Widget({"data-width": "100%"}),
            "teamleader": Select2Widget(
                {
                    "data-width": "100%",
                    "data-allow-clear": "true",
                }
            ),
        }

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(AufgabeForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_show_errors = True
        self.helper.form_error_title = "Allgemeine Fehler"

        self.helper.layout = Layout(
            'aufgabe',
            'verantwortlich',
            'gruppe',
            'anzahl',
            'stunden',
            'teamleader',
            Field('datum', css_class="datepicker"),
            'bemerkung',
            'schnellzuweisung',
            )

    def clean(self):

        cleaned_data = super(AufgabeForm, self).clean()

        stundenplan = {}
        for k, v in self.request.POST.items():
            if 'uhrzeit' == k[:7] and v != '0':
                try:
                    v = int(v)
                except:
                    v = 0
                if v < 0:
                    raise ValidationError("Keine negativen Personen im Stundenplan",
                                          code="negativNumber")

                uhrzeit = int(k.split('_')[1])
                stundenplan[uhrzeit] = v

        cleaned_data['stundenplan'] = stundenplan

        if (len(stundenplan) > 0) and (cleaned_data['datum'] is None):
            raise ValidationError("Angaben im Stundenplan erfordern ein Datum.",
                                  code ="illogic") 

        # das kann schon sinnvoll sein: 5 h pro Person...
        # und im Stundenplan dann verteilt
        ## if (len(stundenplan) > 0) and (cleaned_data['anzahl'] > 0):
        ##     raise ValidationError ("Entweder Stundenplan oder Anzahl Personen angeben, nicht beides!",
        ##                            code="illogic")

        return cleaned_data


class EmailAddendumForm (forms.Form):
    ergaenzung = forms.CharField(required=False,
                                 label="Ergänzender Text",
                                 )

    def __init__(self, *args, **kwargs):
        super(EmailAddendumForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

##################################
## Filter forms
#################################


class CrispyFilterMixin(CrispyFormMixin):
    """A specific Form mixin, specialiced for filters (common case).

    It tries to be smart in constructing the layout object. It looks at the
    __layout attributes of all the current class and all the mixins, up to this
    base class. In that order, it patches together the layout object itself.
    """

    def get_mixin_names(self):
        """
        Get all the mixins standing between the current class and
        this base class, in mro order.
        We need the names later on, not the class object.
        """
        mixins = []
        for m in self.__class__.mro():
            if m == CrispyFilterMixin:
                break
            mixins.append(m.__name__)
        return mixins

    def get_mixin_attributes(self, attr):
        """Assuming that the current class has several mixings
        which all define a call attribute, get the values
        of these attributes as a list, in mro.
        """

        mixins = self.get_mixin_names()
        res = []
        for m in mixins:
            try:
                tmp = self.__getattribute__('_' + m + '__' + attr)
                res.append(tmp)
            except AttributeError:
                pass

        return res

    def __init__(self, *args, **kwargs):
        """
        Set the form help fields to the specific filtering case
        """
        super(CrispyFilterMixin, self).__init__(*args, **kwargs)

        self.helper.form_method = "get"
        self.helper.form_action = ""

        self.helper.form_class = "row g-2 align-items-center"
        self.helper.wrapper_class = "col-auto"
        self.helper.field_template = "bootstrap5/layout/inline_field.html"

        # get all the __layout attributes from the derived classes,
        # in mro order. Then, patch taht together into the self.helper.layout,
        # adding the filter anwendern always as the last
        layoutattributes = self.get_mixin_attributes('layout')

        self.helper.layout = Layout()
        for l in layoutattributes:
            self.helper.layout = Layout(self.helper.layout,
                                        l)

        self.helper.layout = Layout(self.helper.layout,
                                    FormActions(
                                        Submit('filter', 'Filter anwenden'),
                                        ),
                                    )

        # disabluing test, this seems to work
        # self.fields['first_name'].widget.attrs['disabled'] = True

##################################


class NameFilterForm (CrispyFilterMixin, forms.Form):
    last_name = forms.CharField(
        label="Nachname",
        max_length=20,
        required=False,
        )

    first_name = forms.CharField (
        label = "Vorname",
        max_length = 20,
        required = False,
        )

    __layout = Layout(
        'last_name',
        'first_name',
        )


class AufgabengruppeFilterForm (CrispyFilterMixin, forms.Form):

    aufgabengruppe = forms.ModelChoiceField (queryset = models.Aufgabengruppe.objects.all(),
                                            label="Aufgabengruppe", 
                                            required=False)

    __layout = Layout (
        'aufgabengruppe',
        )
 
class PersonAufgabengruppeFilterForm (NameFilterForm,
                                      AufgabengruppeFilterForm,
                                      forms.Form):
    pass


class PraeferenzFilterForm (CrispyFilterMixin, forms.Form):

    praeferenz = forms.MultipleChoiceField(choices=models.Meldung.Preferences.choices,
                                           widget=forms.CheckboxSelectMultiple,
                                           label="Vorliebe Mitglied",
                                           required=False,
                                           initial=[models.Meldung.Preferences.RELUCTANTLY,
                                                    models.Meldung.Preferences.OK,
                                                    models.Meldung.Preferences.GLADLY,
                                                    ],
                                             )
    __layout = Layout(
        HTML('<br>'),
        InlineCheckboxes('praeferenz'),
        )


class PraeferenzVorstandFilterForm (CrispyFilterMixin, forms.Form):

    praeferenzVorstand = forms.MultipleChoiceField(choices=models.Meldung.Preferences.choices,
                                           widget=forms.CheckboxSelectMultiple,
                                           label="Vorliebe Vorstand",
                                           required=False,
                                           initial=[models.Meldung.Preferences.NEVER,
                                                    models.Meldung.Preferences.RELUCTANTLY,
                                                    models.Meldung.Preferences.OK,
                                                    models.Meldung.Preferences.GLADLY,
                                                    ],
                                             )
    __layout = Layout(
        HTML('<br>'),
        InlineCheckboxes('praeferenzVorstand'),
        )


class PersonAufgGrpPraefernzFilterForm (NameFilterForm,
                                        AufgabengruppeFilterForm,
                                        PraeferenzFilterForm,
                                        PraeferenzVorstandFilterForm,
                                        forms.Form):
    pass


class DateFilterForm (CrispyFilterMixin, forms.Form):
    von = forms.DateField (label="Von",
                           required=False)
    bis = forms.DateField (label="Bis",
                           required=False)
    __layout = Layout(
        InlineField ('von', css_class="datepicker",), 
        InlineField ('bis', css_class="datepicker",), 
        )


class StatusFilterForm(CrispyFilterMixin, forms.Form):
    status = forms.MultipleChoiceField(
        choices=models.Leistung.Status.choices,
        widget=forms.CheckboxSelectMultiple,
        label="Bearbeitungsstatus",
        required=False,
        initial=[
            models.Leistung.Status.OPEN,
            models.Leistung.Status.INQUIRY,
        ],
    )
    __layout = Layout(
        InlineCheckboxes("status"),
    )


class StatusFilterForm2(CrispyFilterMixin, forms.Form):
    status = forms.MultipleChoiceField(
        choices=models.Leistung.Status.choices,
        widget=forms.CheckboxSelectMultiple,
        label="Bearbeitungsstatus",
        required=False,
        initial=[
            models.Leistung.Status.ACCEPTED,
            models.Leistung.Status.INQUIRY,
            models.Leistung.Status.REJECTED,
        ],
    )
    __layout = Layout(
        InlineCheckboxes("status"),
    )


class ZuteilungBenachrichtigungForm(CrispyFilterMixin, forms.Form):
    benachrichtigt = forms.BooleanField(required=False,
                                        initial=False,
                                        label="Auch schon benachrichtige"
                                        " Mitglieder anzeigen?",
                                        )

    __layout = Layout(
        'benachrichtigt'
        )


class MitgliedAusgelastetForm(CrispyFilterMixin, forms.Form):
    """
    Is the Mitglied already assigned sufficient amount of work?
    """

    mitglied_ausgelastet = forms.ChoiceField(required=False,
                                             label="Mitglied ausgelastet?",
                                             choices=(
                                                 ('--', 'Alle Mitglieder'),
                                                 ('AM', 'Mitglieder mit Meldung für Aufgabe/Aufgabengruppe'),
                                                 ('FR', 'Nur freie Mitglieder'),
                                                 ('FRAM', 'Nur freie Mitglieder, mit Meldung für Aufgabe/Aufgabengruppe'),
                                                 ('BU',
                                                  'Nur ausgelastete Mitglieder'),
                                                 ('BUAM',
                                                  'Nur ausgelastete Mitglieder, mit Meldung für Aufgabe/Aufgabengruppe'),
                                                 ),
                                             )

    aktive_aufgaben = forms.BooleanField(required=False,
                                         label="Vergangene Aufgaben ausblenden?",
                                         initial=False,
                                         )
    __layout = Layout(
        'mitglied_ausgelastet',
        'aktive_aufgaben',
        )

    def __init__(self, *args, **kwargs):
        "Let's make sure that AM is the default field value"

        super(MitgliedAusgelastetForm, self).__init__(*args, **kwargs)

        # this works, but does not apply the filter setting :-(
        # besides, it makes zero sense to use this as a default, since
        # intially, there is typically no Aufgabengruppe selected.
        # no obvious way to make this work 
        # self.initial['mitglied_ausgelastet'] = 'AM'


class ZuteilungStatusForm(CrispyFilterMixin, forms.Form):
    """Possible status:
    - aufgabe has not enough zuteilungen
    - aufgabe has not even enough meldungen
    ??
    """

    zuteilungen_ausreichend = forms.ChoiceField(required=False,
                                                label="Zuteilungen ausreichend?",
                                                choices = (
                                                     ('--', 'Alle anzeigen'),
                                                     ('UN', 'Aufgaben mit unzureichenden Zuteilungen'),
                                                     ('ZU', 'Aufgaben mit zureichenden Zuteilungen'),
                                                     ),
                                                 )
    __layout = Layout(
        'zuteilungen_ausreichend',
        )

class StundenplanForm(CrispyFilterMixin, forms.Form):
    
    stundenplan = forms.BooleanField(required=False,
                                     initial=False,
                                     label="Stundenplan anzeigen?")

    __layout = Layout(
        'stundenplan',
        )


class SaldenStatusForm(CrispyFilterMixin, forms.Form):
    saldenstatus = forms.ChoiceField(required=False,
                                     initial=False,
                                     label="Saldenstatus",
                                     choices=(('--', 'Kein Statusfilter'),
                                              ('OK', 'Pensum erfüllt'),
                                              ('CH', 'Chancen zu erfüllen'),
                                              ('PR', 'Pensum kann nicht erfüllt werden'),
                                              ))
    __layout = Layout(
        'saldenstatus'
        )


class GemeldeteAufgabenFilterForm(CrispyFilterMixin, forms.Form):
    gemeldet = forms.ChoiceField(required=False,
                                 initial=False,
                                 label="Gemeldet",
                                 choices=(
                                     ('--', 'Alle Aufgaben'),
                                     ('GA', 'Nur Aufgaben, für die ich gemeldet habe'),
                                     ('NG', 'Nur Aufgaben, für die ich NICHT gemeldet habe'),
                                     ),
                                 )
    __layout = Layout(
        'gemeldet',
        )

class MitgliedsnummerFilterForm(CrispyFilterMixin, forms.Form):
    mitgliedsnummer = forms.CharField(required=False,
                                      label="Mitgliedsnummer",
                                      max_length=10,
                                      )

    __layout = Layout(
        'mitgliedsnummer',
        )

###################################
# Stich Forms together into Filters


class AufgabenDatumFilter(AufgabengruppeFilterForm,
                          DateFilterForm,
                          forms.Form):
    pass


class GemeldeteFilter(
        AufgabengruppeFilterForm,
        GemeldeteAufgabenFilterForm,
        DateFilterForm,
        forms.Form,
        ):
    pass


class LeistungFilter(NameFilterForm,
                     AufgabengruppeFilterForm,
                     DateFilterForm,
                     StatusFilterForm,
                     forms.Form):
    pass


class ZuteilungManuellFilter(AufgabengruppeFilterForm,
                             ZuteilungStatusForm,
                             StundenplanForm,
                             forms.Form,
                             ):
    pass


class ZuteilungMitglied(PersonAufgabengruppeFilterForm,
                        ZuteilungStatusForm,
                        MitgliedAusgelastetForm,
                        forms.Form):
    pass


class ZuteilungEmailFilter(NameFilterForm,
                           ZuteilungBenachrichtigungForm,
                           ):
    pass


class SaldenFilter(NameFilterForm,
                   SaldenStatusForm,
                   forms.Form):
    pass


