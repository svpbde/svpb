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


class AufgabenCreateTests(TestCase):
    """Tests for view AufgabenCreate."""

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
        self.user = User.objects.get(username="Superuser")
        self.worker = User.objects.get(username="Mitglied")

    def test_quick_assignment(self):
        """Test quick assignment feature when creating a new task."""
        # Ensure no notification is pending
        self.worker.mitglied.zuteilungBenachrichtigungNoetig = False
        self.worker.mitglied.save()

        # Test creation of new task with quick assignment
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("arbeitsplan-aufgabenErzeugen"),
            {
                "aufgabe": "Schnellzuweisung testen",
                "verantwortlich": "3",
                "gruppe": "1",
                "anzahl": "1",
                "stunden": "1",
                "teamleader": "",
                "datum": "",
                "bemerkung": "",
                "schnellzuweisung": str(self.worker.id),
                "uhrzeit_8": "0",
                "uhrzeit_9": "0",
                "uhrzeit_10": "0",
                "uhrzeit_11": "0",
                "uhrzeit_12": "0",
                "uhrzeit_13": "0",
                "uhrzeit_14": "0",
                "uhrzeit_15": "0",
                "uhrzeit_16": "0",
                "uhrzeit_17": "0",
                "uhrzeit_18": "0",
                "uhrzeit_19": "0",
                "uhrzeit_20": "0",
                "uhrzeit_21": "0",
                "uhrzeit_22": "0",
                "uhrzeit_23": "0",
                "_edit": "Aufgabe anlegen",
            },
        )
        self.assertEqual(response.status_code, 302)

        # Check if task was created
        try:
            task = Aufgabe.objects.get(aufgabe="Schnellzuweisung testen")
        except Aufgabe.DoesNotExist:
            self.fail("Task not found.")

        # Check if assignment was created
        try:
            Zuteilung.objects.get(aufgabe=task, ausfuehrer=self.worker)
        except Zuteilung.DoesNotExist:
            self.fail(f"Zuteilung not found for task {task} and user {self.worker}.")

        # Check if notification is pending
        self.worker.refresh_from_db()
        self.assertTrue(self.worker.mitglied.zuteilungBenachrichtigungNoetig)


class AufgabenUpdateTests(TestCase):
    """Tests for view AufgabenUpdate."""

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
        self.worker = User.objects.get(username="Mitglied")
        self.worker_2 = User.objects.get(username="Teamleiter")
        self.post_data = {
            # Note missing key "schnellzuweisung" (missing = empty)
            "aufgabe": "Feuchtfröhliche Bugfixsuche",
            "verantwortlich": "1",
            "gruppe": "1",
            "anzahl": "1",
            "stunden": "12",
            "teamleader": "4",
            "datum": "",
            "bemerkung": "Dies ist eine ganzjährige Testaufgabe.",
            "uhrzeit_8": "0",
            "uhrzeit_9": "0",
            "uhrzeit_10": "0",
            "uhrzeit_11": "0",
            "uhrzeit_12": "0",
            "uhrzeit_13": "0",
            "uhrzeit_14": "0",
            "uhrzeit_15": "0",
            "uhrzeit_16": "0",
            "uhrzeit_17": "0",
            "uhrzeit_18": "0",
            "uhrzeit_19": "0",
            "uhrzeit_20": "0",
            "uhrzeit_21": "0",
            "uhrzeit_22": "0",
            "uhrzeit_23": "0",
            "_edit": "Änderung eintragen",
        }

    def test_quick_assignment_add_single(self):
        """Test quick assignment feature - add single user."""
        # Ensure no notification is pending
        self.worker.mitglied.zuteilungBenachrichtigungNoetig = False
        self.worker.mitglied.save()

        # Test updating task with quick assignment
        self.client.force_login(self.user)
        # Prepare data to post (copy dict to prevent side effects for other tests)
        post_data = self.post_data.copy()
        post_data["schnellzuweisung"] = str(self.worker.id)
        response = self.client.post(
            reverse("arbeitsplan-aufgabenEdit", kwargs={"pk": self.task.id}),
            post_data,
        )
        self.assertEqual(response.status_code, 302)

        # Check if assignment was created
        try:
            Zuteilung.objects.get(aufgabe=self.task, ausfuehrer=self.worker)
        except Zuteilung.DoesNotExist:
            self.fail(
                f"Zuteilung not found for task {self.task} and user {self.worker}."
            )

        # Check if notification is pending
        self.worker.refresh_from_db()
        self.assertTrue(self.worker.mitglied.zuteilungBenachrichtigungNoetig)

    def test_quick_assignment_add_multiple(self):
        """Test quick assignment feature - add multiple users."""
        # Ensure no notifications are pending
        self.worker.mitglied.zuteilungBenachrichtigungNoetig = False
        self.worker.mitglied.save()
        self.worker_2.mitglied.zuteilungBenachrichtigungNoetig = False
        self.worker_2.mitglied.save()

        # Test updating task with quick assignment
        self.client.force_login(self.user)
        # Prepare data to post (copy dict to prevent side effects for other tests)
        post_data = self.post_data.copy()
        post_data["schnellzuweisung"] = [str(self.worker.id), str(self.worker_2.id)]
        response = self.client.post(
            reverse("arbeitsplan-aufgabenEdit", kwargs={"pk": self.task.id}),
            post_data,
        )
        self.assertEqual(response.status_code, 302)

        # Check if assignments were created
        try:
            Zuteilung.objects.get(aufgabe=self.task, ausfuehrer=self.worker)
        except Zuteilung.DoesNotExist:
            self.fail(
                f"Zuteilung not found for task {self.task} and user {self.worker}."
            )
        try:
            Zuteilung.objects.get(aufgabe=self.task, ausfuehrer=self.worker_2)
        except Zuteilung.DoesNotExist:
            self.fail(
                f"Zuteilung not found for task {self.task} and user {self.worker_2}."
            )

        # Check if notifications are pending
        self.worker.refresh_from_db()
        self.assertTrue(self.worker.mitglied.zuteilungBenachrichtigungNoetig)
        self.worker_2.refresh_from_db()
        self.assertTrue(self.worker_2.mitglied.zuteilungBenachrichtigungNoetig)

    def test_quick_assignment_delete_single(self):
        """Test quick assignment feature - delete single user."""
        # Ensure assignment exists
        Zuteilung.objects.get_or_create(aufgabe=self.task, ausfuehrer=self.worker)
        # Ensure no notification is pending
        self.worker.mitglied.zuteilungBenachrichtigungNoetig = False
        self.worker.mitglied.save()

        # Test updating task with quick assignment
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("arbeitsplan-aufgabenEdit", kwargs={"pk": self.task.id}),
            self.post_data,
        )
        self.assertEqual(response.status_code, 302)

        # Check if assignment was deleted
        with self.assertRaises(Zuteilung.DoesNotExist):
            Zuteilung.objects.get(aufgabe=self.task, ausfuehrer=self.worker)

        # Check if notification is pending
        self.worker.refresh_from_db()
        self.assertTrue(self.worker.mitglied.zuteilungBenachrichtigungNoetig)

    def test_quick_assignment_delete_multiple(self):
        """Test quick assignment feature - delete multiple users."""
        # Ensure assignment exists
        Zuteilung.objects.get_or_create(aufgabe=self.task, ausfuehrer=self.worker)
        Zuteilung.objects.get_or_create(aufgabe=self.task, ausfuehrer=self.worker_2)
        # Ensure no notifications are pending
        self.worker.mitglied.zuteilungBenachrichtigungNoetig = False
        self.worker.mitglied.save()
        self.worker_2.mitglied.zuteilungBenachrichtigungNoetig = False
        self.worker_2.mitglied.save()

        # Test updating task with quick assignment
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("arbeitsplan-aufgabenEdit", kwargs={"pk": self.task.id}),
            self.post_data,
        )
        self.assertEqual(response.status_code, 302)

        # Check if assignments were deleted
        with self.assertRaises(Zuteilung.DoesNotExist):
            Zuteilung.objects.get(aufgabe=self.task, ausfuehrer=self.worker)
        with self.assertRaises(Zuteilung.DoesNotExist):
            Zuteilung.objects.get(aufgabe=self.task, ausfuehrer=self.worker_2)

        # Check if notifications are pending
        self.worker.refresh_from_db()
        self.assertTrue(self.worker.mitglied.zuteilungBenachrichtigungNoetig)
        self.worker_2.refresh_from_db()
        self.assertTrue(self.worker_2.mitglied.zuteilungBenachrichtigungNoetig)

    def test_quick_assignment_replace(self):
        """Test quick assignment feature - replace assigned user with new one."""
        # Ensure assignment exists
        Zuteilung.objects.get_or_create(aufgabe=self.task, ausfuehrer=self.worker)
        # Ensure no notifications are pending
        self.worker.mitglied.zuteilungBenachrichtigungNoetig = False
        self.worker.mitglied.save()
        self.worker_2.mitglied.zuteilungBenachrichtigungNoetig = False
        self.worker_2.mitglied.save()

        # Test updating task with quick assignment
        self.client.force_login(self.user)
        # Prepare data to post (copy dict to prevent side effects for other tests)
        post_data = self.post_data.copy()
        post_data["schnellzuweisung"] = str(self.worker_2.id)
        response = self.client.post(
            reverse("arbeitsplan-aufgabenEdit", kwargs={"pk": self.task.id}),
            post_data,
        )
        self.assertEqual(response.status_code, 302)

        # Check if assignment for worker was deleted
        with self.assertRaises(Zuteilung.DoesNotExist):
            Zuteilung.objects.get(aufgabe=self.task, ausfuehrer=self.worker)
        # Check if assignment for worker_2 was created
        try:
            Zuteilung.objects.get(aufgabe=self.task, ausfuehrer=self.worker_2)
        except Zuteilung.DoesNotExist:
            self.fail(
                f"Zuteilung not found for task {self.task} and user {self.worker_2}."
            )

        # Check if notifications are pending
        self.worker.refresh_from_db()
        self.assertTrue(self.worker.mitglied.zuteilungBenachrichtigungNoetig)
        self.worker_2.refresh_from_db()
        self.assertTrue(self.worker_2.mitglied.zuteilungBenachrichtigungNoetig)

    def test_quick_assignment_no_change(self):
        """Test quick assignment feature - no change to assigned user."""
        # Ensure assignment exists
        Zuteilung.objects.get_or_create(aufgabe=self.task, ausfuehrer=self.worker)
        # Ensure no notification is pending
        self.worker.mitglied.zuteilungBenachrichtigungNoetig = False
        self.worker.mitglied.save()

        # Test updating task with quick assignment
        self.client.force_login(self.user)
        # Prepare data to post
        post_data = self.post_data.copy()
        post_data["schnellzuweisung"] = str(self.worker.id)
        response = self.client.post(
            reverse("arbeitsplan-aufgabenEdit", kwargs={"pk": self.task.id}),
            post_data,
        )
        self.assertEqual(response.status_code, 302)

        # Check if assignment still exists
        try:
            Zuteilung.objects.get(aufgabe=self.task, ausfuehrer=self.worker)
        except Zuteilung.DoesNotExist:
            self.fail(
                f"Zuteilung not found for task {self.task} and user {self.worker}."
            )

        # Check if no notification is pending (no change - no notification)
        self.worker.refresh_from_db()
        self.assertFalse(self.worker.mitglied.zuteilungBenachrichtigungNoetig)


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
            reverse(
                "arbeitsplan-stundenplaeneEdit", kwargs={"aufgabeid": self.task.id}
            ),
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
