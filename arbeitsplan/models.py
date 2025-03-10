"""Django models for the Arbeitsplan at SVPB.

Main classes:

* :class:`Mitglied`: 1on1 with User, provides Vereins unique ID and dates of
  messages sent to User
* :class:`Aufgabe` : Describes a single task
* :class:`Aufgabengruppe` : Grouping :class:`Aufgabe` together,
  with responsible Mitglied
* :class:`Stundenplan` : How many people are needed for a given Aufgabe at a
  given hour?
* :class:`Meldung` : Mitglied wants to contribute to a given Aufgabe
* :class:`Zuteilung` : a task has been assigned to a particular Mitglied
* :class:`StundenZuteilung`: a Zuteilung might pertain only to particular
  times; represented via this class
* :class:`Leistung` : Mitglied claims to have performaed a certain amount of
  work on a particular job
"""
import datetime

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from phonenumber_field.modelfields import PhoneNumberField


# Patch the display of a user:
User.__str__ = lambda s: "%s %s (Nr.: %s)" % (
    s.first_name,
    s.last_name,
    s.mitglied.mitgliedsnummer,
)


class Mitglied(models.Model):
    """Provide additional information on a User by a 1:1 relationship:
    ID, dates of messages

    This class is a one-to-one relationship with user, extending
    information stored about a particular user. It provides an
    additional mitgliedsnummer, corresponding to Vereins-Data.  It
    also stores date when a message has been last sent to a Mitglied
    and whether it is necessary to sent a message.

    It is not possible to derive necessity of messaging form date of
    last message - there simply might not have anything happened to
    this member since its last message.
    """

    class Status(models.TextChoices):
        ADULT = "Er", "Erwachsene"
        YOUTH = "Ju", "Jugendlicher"
        PUPIL = "Ss", "Schüler, Studenten, BW, Zivi"
        CHILD = "Ki", "Kind in Familie"
        CHILD_NO_FEE = "Kf", "Kind in Familie, beitragsfrei"
        PASSIVE = "PM", "Passives Mitglied"
        NON_MEMBER = "Nm", "Nichtmitglied"
        NO_FEE = "Bf", "Beitragsfreies Mitglied"
        PARTNER_ACTIVE = "Pa", "Partner aktives Mitglied"
        PARTNER_PASSIVE = "Pp", "Partner passives Mitglied"

    class Gender(models.TextChoices):
        M = "M", "M"
        W = "W", "W"

    excelFields = [
        ("Vorname", "user__first_name"),
        ("Nachname", "user__last_name"),
        ("M/W", "gender"),
        ("E-Mail", "user__email"),
        ("ID", "mitgliedsnummer"),
        ("Straße", "strasse"),
        ("PLZ", "plz"),
        ("Ort", "ort"),
        ("Status", "status"),
        ("Arbeitslast", "arbeitslast"),
        ("# Meldungen", "gemeldeteAnzahlAufgaben"),
        ("Stunden Meldungen ", "gemeldeteStunden"),
        ("# Zuteilungen", "zugeteilteAufgaben"),
        ("Stunden Zuteilungen", "zugeteilteStunden"),
        ("Behauptete Leistungen (h) insges.", "behaupteteStunden"),
        ("Unbearbeitete Leistungen (h)", "offeneStunden"),
        ("Abgelehnte Leistungen (h)", "abgelehnteStunden"),
        ("Akzeptierte Leistungen (h)", "akzeptierteStunden"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    """Couple Mitglied to User via 1:1 field."""

    mitgliedsnummer = models.CharField(max_length=10, default=0)
    """ID as assigned by Verein. Unique?! Use this as default login."""

    zuteilungsbenachrichtigung = models.DateTimeField(
        help_text="Wann war die letzte Benachrichtigung zu einer Zuteilung?",
        default=datetime.datetime(1900, 1, 1, tzinfo=datetime.timezone.utc),
        verbose_name="Letzte Benachrichtigung",
    )
    """Date and time of most recent message to user"""

    zuteilungBenachrichtigungNoetig = models.BooleanField(
        help_text="Muss an diese Nutzer"
        " eine Benachrichtigung"
        " wegen Änderung der "
        "Zuteilungen gesendet werden?",
        default=False,
        verbose_name="Benachrichtigung zu Zuteilungen nötig?",
    )
    """Does Mitglied need a message?"""

    geburtsdatum = models.DateField(
        default=datetime.date(1900, 1, 1),
        verbose_name="Geburtsdatum",
    )

    strasse = models.CharField(
        max_length=50, verbose_name="Straße und Hausnummer", default=""
    )

    plz = models.DecimalField(
        max_digits=5, verbose_name="PLZ", decimal_places=0, default=0
    )

    gender = models.CharField(
        max_length=1,
        verbose_name="Geschlecht",
        default=Gender.M,
        choices=Gender.choices,
    )

    ort = models.CharField(max_length=50, verbose_name="Ort", default="")

    festnetz = PhoneNumberField(blank=True, verbose_name="Festnetznummer", default="")

    mobil = PhoneNumberField(blank=True, verbose_name="Mobilnummer", default="")

    status = models.CharField(
        max_length=20,
        verbose_name="Mitgliedsstatus",
        default=Status.ADULT,
        choices=Status.choices,
    )

    arbeitslast = models.IntegerField(
        verbose_name="Arbeitslast (h/Jahr)",
        default=12,
    )

    def __str__(self):
        return self.user.__str__()

    def gemeldeteAnzahlAufgaben(self):
        return self.user.meldung_set.exclude(
            prefMitglied=Meldung.Preferences.NEVER
        ).count()

    def gemeldeteStunden(self):
        """Compute hours for which the Mitglied has entered a Meldung."""
        echteMeldungen = self.user.meldung_set.exclude(
            prefMitglied=Meldung.Preferences.NEVER
        )
        return sum([m.aufgabe.stunden for m in echteMeldungen])

    def zugeteilteAufgaben(self):
        z = self.user.zuteilung_set.all()
        return z.count()

    def zugeteilteStunden(self, time=None):
        """Compute hours already assigned to this user.

        This is difficult because some aufgaben have easily identified hours,
        others have to be checked specifically for the
        stundenplan Zuteilung.

        :param time: -1: tasks from past,
                     +1: tasks from future,
                     0: Tasks without date (not sure this is useful?),
                     None: do not filter assigned tasks any more.
        :returns: Hours assigned to user, for the desired time frame.
        :rtype: int
        """
        qs = self.user.zuteilung_set.all()

        if time == -1:
            qs = qs.filter(aufgabe__datum__lte=datetime.date.today())
        if time == +1:
            qs = qs.filter(aufgabe__datum__gt=datetime.date.today())
        if time == 0:
            qs = qs.filter(aufgabe__datum__isnull=True)

        stundenlist = [z.stunden() for z in qs]
        return sum(stundenlist)

    def behaupteteStunden(self):
        leistungen = self.user.leistung_set.all()
        return sum([leistung.zeit for leistung in leistungen])

    def akzeptierteStunden(self):
        leistungen = self.user.leistung_set.filter(status=Leistung.Status.ACCEPTED)
        return sum([leistung.zeit for leistung in leistungen])

    def offeneStunden(self):
        leistungen = self.user.leistung_set.filter(status=Leistung.Status.OPEN)
        return sum([leistung.zeit for leistung in leistungen])

    def abgelehnteStunden(self):
        leistungen = self.user.leistung_set.filter(status=Leistung.Status.REJECTED)
        return sum([leistung.zeit for leistung in leistungen])

    def profileIncomplete(self):
        r = []
        if not self.user.email:
            r.append("E-Mail")
        if not self.festnetz and not self.mobil:
            r.append("Telefonnummer (Festnetznummer oder Mobil)")
        return ", ".join(r)

    class Meta:
        verbose_name_plural = "Mitglieder"
        verbose_name = "Mitglied"


def get_default_vorstand(self):
    """When deleting an entry with a Vorstand in charge,
    assign a default Vorstand member."""
    # TODO
    pass


class Aufgabengruppe(models.Model):
    gruppe = models.CharField(
        max_length=30, help_text="Aussagefähiger Name für Gruppe von Aufgaben"
    )

    verantwortlich = models.ForeignKey(
        User,
        # actually, we should do this:
        #   on_delete=models.SET(models.get_default_vorstand),
        # but for simplicity, let's just do that: TODO
        # (means: have to remove responsibility from Vorstand, before deleting it)
        on_delete=models.PROTECT,
        help_text="Verantwortliches Vorstandsmitglied",
    )

    bemerkung = models.TextField(blank=True)

    def __str__(self):
        return self.gruppe

    class Meta:
        verbose_name_plural = "Aufgabengruppen"
        verbose_name = "Aufgabengruppe"
        ordering = ["gruppe"]


# Work around the django_tables2 issue:
def validate_notDot(value):
    if "." in value:
        raise ValidationError(
            "Leider dürfen Aufgabennamen keinen . enthalten! "
            "Bitte umformulieren, danke."
        )


class Aufgabe(models.Model):
    aufgabe = models.CharField(max_length=50, validators=[validate_notDot], unique=True)
    verantwortlich = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        help_text="Verantwortliches Vorstandsmitglied",
    )
    teamleader = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,  # ok not to have a teamleader
        related_name="teamleader_set",
        help_text="Ein optionaler Teamleader für "
        "die Aufgabe (nicht notwendig Vorstand)",
        verbose_name="Team-Leader",
        blank=True,
        null=True,
    )

    gruppe = models.ForeignKey(Aufgabengruppe, on_delete=models.PROTECT)

    anzahl = models.IntegerField(
        default=0,
        help_text="Wieviele Personen werden für diese Aufgabe gebraucht?",
        verbose_name="Anzahl benötigte Helfer",
    )

    stunden = models.IntegerField(
        default=0,
        help_text="Wieviele Stunden Arbeit pro Person?",
        verbose_name="Stunden",
    )

    datum = models.DateField(
        blank=True,
        null=True,
        help_text="Wann fällt die Aufgabe an? (freilassen möglich)",
    )

    bemerkung = models.TextField(blank=True)

    def kontakt(self):
        if self.teamleader:
            return self.teamleader
        else:
            return self.verantwortlich

    def numMeldungen(self):
        """How many Meldungen of status better than NEVER
        exist for this Aufgabe?
        """
        return self.meldung_set.exclude(prefMitglied=Meldung.Preferences.NEVER).count()

    def has_Stundenplan(self):
        """Is there a Stundenplan for this Aufgabe?"""

        return self.stundenplan_set.filter(anzahl__gt=0).count() > 0

    def stundenplan_complete(self):
        """Is there enough manpower for every hour in the Stundenplan?"""
        stundenplan = self.stundenplan_set.filter(anzahl__gt=0)
        if stundenplan.count() > 0:
            for s in stundenplan:
                zuteilungen = self.zuteilung_set.filter(
                    stundenzuteilung__uhrzeit=s.uhrzeit
                )
                zugewiesen = sum([z.zusatzhelfer + 1 for z in zuteilungen])
                if zugewiesen < s.anzahl:
                    return False

        return True

    def is_open(self):
        """Do enough Zuteilungen already exist for this Aufgabe?"""
        return self.zuteilung_set.count() < self.anzahl

    def __str__(self):
        return "{} ({})".format(self.aufgabe, self.id)

    class Meta:
        verbose_name_plural = "Aufgaben"
        verbose_name = "Aufgabe"
        ordering = ["aufgabe"]


class Stundenplan(models.Model):
    aufgabe = models.ForeignKey(
        Aufgabe,
        on_delete=models.CASCADE,
        # no need to have Stundenplan for non-existing Aufgabe
    )

    uhrzeit = models.IntegerField(help_text="Beginn")
    anzahl = models.IntegerField(
        default=0, help_text="Wieviele Personen werden um diese Uhrzeit benötigt?"
    )

    startZeit = 8
    stopZeit = 23

    def __str__(self):
        return (
            self.aufgabe.__str__() + "@" + str(self.uhrzeit) + ": " + str(self.anzahl)
        )

    class Meta:
        verbose_name_plural = "Stundenpläne"
        verbose_name = "Stundenplan"


class Meldung(models.Model):
    class Preferences(models.IntegerChoices):
        NEVER = -1, "Nein"
        RELUCTANTLY = 0, "Wenn es sein muss"
        OK = 1, "Ok"
        GLADLY = 2, "Gerne!"

    PREFERENCES_STRING = "; ".join(
        [f"{value}: {label}" for (value, label) in Preferences.choices]
    )
    PREFERENCES_BUTTONS = {
        Preferences.NEVER: "btn-outline-secondary",
        Preferences.RELUCTANTLY: "btn-outline-secondary",
        Preferences.OK: "btn-outline-secondary",
        Preferences.GLADLY: "btn-outline-secondary",
    }
    MODELDEFAULTS = {
        "prefMitglied": Preferences.NEVER,
        "prefVorstand": Preferences.OK,
        "bemerkung": "",
        "bemerkungVorstand": "",
    }

    erstellt = models.DateField(auto_now_add=True)
    veraendert = models.DateField(auto_now=True)
    # on_delete: Deleting User deletes the Meldung
    melder = models.ForeignKey(User, on_delete=models.CASCADE)
    # on_delete: Deleting Aufgabe deletes the Meldung. Using PROTECT is not feasible
    # here, as Meldungen are created for every existing Aufgabe once a user visits the
    # Meldung page, effectively blocking deletion.
    aufgabe = models.ForeignKey(Aufgabe, on_delete=models.CASCADE)

    prefMitglied = models.IntegerField(
        choices=Preferences.choices,
        default=Preferences.OK,
        verbose_name="Präferenz",
        help_text="Haben Sie Vorlieben für diese Aufgabe?",
    )
    prefVorstand = models.IntegerField(
        choices=Preferences.choices,
        default=Preferences.OK,
        help_text="Trauen Sie diesem Mitglied die Aufgabe zu?",
    )
    bemerkung = models.TextField(blank=True)
    bemerkungVorstand = models.TextField(blank=True)

    def __str__(self):
        return (
            self.melder.__str__()
            + " ; "
            + self.aufgabe.__str__()
            + " ; "
            + (self.veraendert.strftime("%d/%m/%y") if self.veraendert else "--")
        )

    class Meta:
        verbose_name_plural = "Meldungen"
        verbose_name = "Meldung"


class Zuteilung(models.Model):
    aufgabe = models.ForeignKey(Aufgabe, on_delete=models.PROTECT)
    ausfuehrer = models.ForeignKey(User, on_delete=models.CASCADE)

    automatisch = models.BooleanField(default=False)
    zusatzhelfer = models.IntegerField(default=0)

    def __str__(self):
        return (
            self.aufgabe.__str__()
            + ": "
            + self.ausfuehrer.__str__()
            + (" @ " + ",".join([s.__str__() for s in self.stundenzuteilung_set.all()]))
        )

    def save(self, *args, **kwargs):
        super(Zuteilung, self).save(*args, **kwargs)
        self.ausfuehrer.mitglied.zuteilungBenachrichtigungNoetig = True
        self.ausfuehrer.mitglied.save()

    def delete(self, *args, **kwargs):
        self.ausfuehrer.mitglied.zuteilungBenachrichtigungNoetig = True
        self.ausfuehrer.mitglied.save()
        super(Zuteilung, self).delete(*args, **kwargs)

    def stunden(self):
        """Compute the hours allocated to this zuteilung.
        Depends on whether a Stundenplan exists for this job.

        If a Stundenplan exists for this job, but is not allocated yet, the planned job
        time is reported.
        """
        tmp = self.stundenzuteilung_set.count()
        if tmp > 0:
            return tmp
        else:
            return self.aufgabe.stunden

    def stundenTuple(self):
        """Produce a list of tuples with the Stunden correpsonding to this Zuteilung.
        Compress it so that only consecutive intervals show up.
        """
        outlist = []
        inlist = sorted([s.uhrzeit for s in self.stundenzuteilung_set.all()])

        try:
            if inlist:
                now = inlist.pop(0)
                currentTuple = (now, now + 1)
                while inlist:
                    now = inlist.pop(0)
                    if now == currentTuple[1]:
                        currentTuple = (currentTuple[0], now + 1)
                    else:
                        outlist.append(currentTuple)
                        currentTuple = (now, now + 1)

                outlist.append(currentTuple)
        except Exception:
            # TODO: Log exception
            pass

        return outlist

    def stundenString(self):
        st = self.stundenTuple()
        r = ", ".join(["{0} Uhr - {1} Uhr".format(s[0], s[1]) for s in st])
        return r

    class Meta:
        verbose_name_plural = "Zuteilungen"
        verbose_name = "Zuteilung"


class StundenZuteilung(models.Model):
    zuteilung = models.ForeignKey(Zuteilung, on_delete=models.CASCADE)

    uhrzeit = models.IntegerField(blank=True, null=True)

    def save(self, *args, **kwargs):
        super(StundenZuteilung, self).save(*args, **kwargs)
        self.zuteilung.ausfuehrer.mitglied.zuteilungBenachrichtigungNoetig = True
        self.zuteilung.ausfuehrer.mitglied.save()

    def delete(self, *args, **kwargs):
        self.zuteilung.ausfuehrer.mitglied.zuteilungBenachrichtigungNoetig = True
        self.zuteilung.ausfuehrer.mitglied.save()
        super(StundenZuteilung, self).delete(*args, **kwargs)

    class Meta:
        verbose_name = "Zuteilung einer Stunde"
        verbose_name_plural = "Zuteilungen für einzelne Stunden"

    def __str__(self):
        return str(self.uhrzeit)


class Leistung(models.Model):
    class Status(models.TextChoices):
        OPEN = "OF", "Offen"
        ACCEPTED = "AK", "Akzeptiert"
        INQUIRY = "RU", "Rückfrage"
        REJECTED = "NE", "Abgelehnt"

    STATUS_BUTTONS = {
        Status.OPEN: "btn-outline-secondary",
        Status.ACCEPTED: "btn-outline-secondary",
        Status.INQUIRY: "btn-outline-secondary",
        Status.REJECTED: "btn-outline-secondary",
    }

    melder = models.ForeignKey(User, on_delete=models.CASCADE)
    aufgabe = models.ForeignKey(Aufgabe, on_delete=models.PROTECT)
    erstellt = models.DateTimeField(auto_now_add=True)
    veraendert = models.DateTimeField(auto_now=True)
    wann = models.DateField(
        help_text="An welchem Tag haben Sie die Leistung erbracht?",
    )
    zeit = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        help_text="Wie viele Stunden hast du gearbeitet? Eingabe von Zehntelstunden "
        "möglich. Je nach Browsereinstellung mit . oder , die Nachkommastelle abtrennen"
        ": 1.4 oder 1,4 für 1 Stunde 24 Minuten.",
    )
    status = models.CharField(max_length=2, choices=Status.choices, default=Status.OPEN)

    bemerkung = models.TextField(blank=True)
    bemerkungVorstand = models.TextField(blank=True, verbose_name="Bemerkung Vorstand")

    class Meta:
        verbose_name_plural = "Leistungen"
        verbose_name = "Leistung"

    def __str__(self):
        return (
            self.melder.__str__()
            + " ; "
            + self.aufgabe.__str__()
            + " ; "
            + (self.veraendert.strftime("%d/%m/%y") if self.veraendert else "--")
        )
