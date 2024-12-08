"""Tests of arbeitsplan views."""

from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from arbeitsplan.models import Aufgabe, Mitglied, StundenZuteilung, Zuteilung


class SimpleTest(TestCase):
    fixtures = [
        "arbeitsplan/fixtures/members.json",
        "arbeitsplan/fixtures/taskgroups.json",
        "arbeitsplan/fixtures/tasks.json",
        "arbeitsplan/fixtures/timetables.json",
        "mitglieder/fixtures/groups.json",
        "mitglieder/fixtures/po.json",
        "mitglieder/fixtures/user.json",
    ]
    # In fixtures, all users should have this password
    plainpassword = "Test"
    superuser = "Superuser"

    def login_user(self, user):
        cl = Client()
        response = cl.post(
            "/login/",
            {"username": user, "password": self.plainpassword},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        return cl, response

    def test_login_works(self):
        cl, response = self.login_user(self.superuser)
        self.assertNotIn("login", response.request["PATH_INFO"])

    def test_leistung_bearbeiten(self):
        """Test if leistungenBearbeiten page loads."""
        cl, response = self.login_user(self.superuser)
        response = cl.get("/arbeitsplan/leistungenBearbeiten/z=me/")
        self.assertEqual(response.status_code, 200)

        # and with some qualifiers:
        response = cl.get(
            "/arbeitsplan/leistungenBearbeiten/z=me/?last_name=&first_name=&aufgabengruppe=3&von=&bis=&status=OF&status=RU&filter=Filter+anwenden"
        )
        self.assertEqual(response.status_code, 200)

    def test_zuteilung_email(self):
        """do the zuteilung emails look right?"""
        # Make sure there is at least a single user with a zuteilung_noetig true
        u = Mitglied.objects.get(mitgliedsnummer="00003")
        u.zuteilungBenachrichtigungNoetig = True
        u.save()

        cl, response = self.login_user(self.superuser)

        response = cl.get("/arbeitsplan/benachrichtigen/zuteilung/", follow=True)
        self.assertEqual(response.status_code, 200)
        # the user's email must appear in the response page:
        self.assertContains(response, u.user.email, html=False)

        # let's generate the email
        response = cl.post(
            "/arbeitsplan/benachrichtigen/zuteilung/",
            {
                "eintragen": "Benachrichtigungen eintragen",
                "sendit_4": "on",
                "ergaenzung": "ergaenzungtest",
                "anmerkung_4": "anmerkungtest",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

        # and actually send it off:
        call_command("send_queued_mail")
        self.assertEqual(len(mail.outbox), 1)


class ManuelleZuteilungViewTests(TestCase):
    """Tests for ManuelleZuteilungView."""

    fixtures = [
        "arbeitsplan/fixtures/members.json",
        "arbeitsplan/fixtures/taskgroups.json",
        "arbeitsplan/fixtures/tasks.json",
        "arbeitsplan/fixtures/timetables.json",
        "mitglieder/fixtures/groups.json",
        "mitglieder/fixtures/po.json",
        "mitglieder/fixtures/user.json",
    ]

    def setUp(self):
        self.task = Aufgabe.objects.get(aufgabe="Feuchtfröhliche Bugfixsuche")
        self.user = User.objects.get(username="Superuser")

    def test_assignment_create(self):
        """Test creation of Zuteilung."""
        # Ensure no notification is pending
        self.user.mitglied.zuteilungBenachrichtigungNoetig = False
        self.user.mitglied.save()

        # Test creation of assignment
        self.client.force_login(self.user)
        response = self.client.post(
            reverse(
                "arbeitsplan-manuellezuteilungAufgabe", kwargs={"aufgabe": self.task.id}
            ),
            {
                "box_3_1": "1",
                "eintragen": "Zuteilung+eintragen/ändern",
                "status": "3_1=0",
            },
        )
        self.assertEqual(response.status_code, 302)

        # Check if assignment was created
        try:
            Zuteilung.objects.get(aufgabe=self.task, ausfuehrer=self.user)
        except Zuteilung.DoesNotExist:
            self.fail(f"Zuteilung not found for task {self.task} and user {self.user}.")

        # Check if notification is pending
        self.user.refresh_from_db()
        self.assertTrue(self.user.mitglied.zuteilungBenachrichtigungNoetig)

    def test_assignment_delete(self):
        """Test deletion of Zuteilung."""
        # Ensure assignment exists
        Zuteilung.objects.get_or_create(aufgabe=self.task, ausfuehrer=self.user)
        # Ensure no notification is pending
        self.user.mitglied.zuteilungBenachrichtigungNoetig = False
        self.user.mitglied.save()

        # Test deletion of assigment
        self.client.force_login(self.user)
        response = self.client.post(
            reverse(
                "arbeitsplan-manuellezuteilungAufgabe", kwargs={"aufgabe": self.task.id}
            ),
            {
                "eintragen": "Zuteilung+eintragen/ändern",
                "status": "3_1=1",
            },
        )
        self.assertEqual(response.status_code, 302)

        # Check if assignment was deleted
        with self.assertRaises(Zuteilung.DoesNotExist):
            Zuteilung.objects.get(aufgabe=self.task, ausfuehrer=self.user)

        # Check if notification is pending
        self.user.refresh_from_db()
        self.assertTrue(self.user.mitglied.zuteilungBenachrichtigungNoetig)


class StundenplaeneEditTests(TestCase):
    """Tests for view StundenplaeneEdit."""

    fixtures = [
        "arbeitsplan/fixtures/members.json",
        "arbeitsplan/fixtures/taskgroups.json",
        "arbeitsplan/fixtures/tasks.json",
        "arbeitsplan/fixtures/timetables.json",
        "mitglieder/fixtures/groups.json",
        "mitglieder/fixtures/po.json",
        "mitglieder/fixtures/user.json",
    ]

    def setUp(self):
        self.task = Aufgabe.objects.get(aufgabe="Adventskaffee")
        self.user = User.objects.get(username="Superuser")
        # Ensure assignment exists
        self.assignment, _ = Zuteilung.objects.get_or_create(
            aufgabe=self.task, ausfuehrer=self.user
        )

    def test_timetable_assignment_create(self):
        """Test creation of StundenZuteilung."""
        # Ensure no notification is pending
        self.user.mitglied.zuteilungBenachrichtigungNoetig = False
        self.user.mitglied.save()

        # Test creation of timetable assignment
        self.client.force_login(self.user)
        response = self.client.post(
            reverse(
                "arbeitsplan-stundenplaeneEdit", kwargs={"aufgabeid": self.task.id}
            ),
            {
                "anzahl_3": "0",
                "uhrzeit_3_14": "1",
                "uhrzeit_3_15": "1",
                "uhrzeit_3_16": "1",
                "eintragen": "Stundenzuteilung+eintragen/ändern",
                "checkedboxes": "",
            },
        )
        self.assertEqual(response.status_code, 302)

        # Check if timetable assignments were created
        try:
            StundenZuteilung.objects.get(zuteilung=self.assignment, uhrzeit=14)
            StundenZuteilung.objects.get(zuteilung=self.assignment, uhrzeit=15)
            StundenZuteilung.objects.get(zuteilung=self.assignment, uhrzeit=16)
        except StundenZuteilung.DoesNotExist:
            self.fail(
                f"StundenZuteilung not found for task {self.task} and user {self.user}."
            )

        # Check if notification is pending
        self.user.refresh_from_db()
        self.assertTrue(self.user.mitglied.zuteilungBenachrichtigungNoetig)

    def test_timetable_assignment_delete(self):
        """Test deletion of StundenZuteilung."""
        # Ensure timetable assignment exists
        StundenZuteilung.objects.get_or_create(zuteilung=self.assignment, uhrzeit=14)
        StundenZuteilung.objects.get_or_create(zuteilung=self.assignment, uhrzeit=15)
        StundenZuteilung.objects.get_or_create(zuteilung=self.assignment, uhrzeit=16)
        # Ensure no notification is pending
        self.user.mitglied.zuteilungBenachrichtigungNoetig = False
        self.user.mitglied.save()

        # Test deletion of timetable assignments
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("arbeitsplan-stundenplaeneEdit", kwargs={"aufgabeid": self.task.id}),
            {
                "anzahl_3": "0",
                "eintragen": "Stundenzuteilung+eintragen/ändern",
                "checkedboxes": "3_14,3_15,3_16",
            },
        )
        self.assertEqual(response.status_code, 302)

        # Check if StundenZuteilung objects were deleted
        with self.assertRaises(StundenZuteilung.DoesNotExist):
            StundenZuteilung.objects.get(zuteilung=self.assignment, uhrzeit=14)
        with self.assertRaises(StundenZuteilung.DoesNotExist):
            StundenZuteilung.objects.get(zuteilung=self.assignment, uhrzeit=15)
        with self.assertRaises(StundenZuteilung.DoesNotExist):
            StundenZuteilung.objects.get(zuteilung=self.assignment, uhrzeit=16)

        # Check if notification is pending
        self.user.refresh_from_db()
        self.assertTrue(self.user.mitglied.zuteilungBenachrichtigungNoetig)


class ZuteilungLoeschenViewTests(TestCase):
    """Tests for view ZuteilungLoeschenView."""

    fixtures = [
        "arbeitsplan/fixtures/members.json",
        "arbeitsplan/fixtures/taskgroups.json",
        "arbeitsplan/fixtures/tasks.json",
        "arbeitsplan/fixtures/timetables.json",
        "mitglieder/fixtures/groups.json",
        "mitglieder/fixtures/po.json",
        "mitglieder/fixtures/user.json",
    ]

    def setUp(self):
        self.task = Aufgabe.objects.get(aufgabe="Feuchtfröhliche Bugfixsuche")
        self.user = User.objects.get(username="Superuser")

    def test_assignment_delete(self):
        """Test deletion of Zuteilung."""
        # Ensure assignment exists
        assignment, _ = Zuteilung.objects.get_or_create(
            aufgabe=self.task, ausfuehrer=self.user
        )
        # Ensure no notification is pending
        self.user.mitglied.zuteilungBenachrichtigungNoetig = False
        self.user.mitglied.save()

        # Test deletion of assignment
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("arbeitsplan-zuteilungDelete", kwargs={"pk": assignment.id}),
        )
        self.assertEqual(response.status_code, 302)

        # Check if assignment was deleted
        with self.assertRaises(Zuteilung.DoesNotExist):
            Zuteilung.objects.get(aufgabe=self.task, ausfuehrer=self.user)

        # Check if notification is pending
        self.user.refresh_from_db()
        self.assertTrue(self.user.mitglied.zuteilungBenachrichtigungNoetig)
