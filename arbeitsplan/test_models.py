"""Tests of arbeitsplan models."""

from django.contrib.auth.models import User
from django.test import TestCase

from arbeitsplan.models import Aufgabe, StundenZuteilung, Zuteilung


class StundenZuteilungTest(TestCase):
    """Tests for model StundenZuteilung."""

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
        self.user = User.objects.get(last_name="Mitglied")
        self.timetable_hour = 14

        # Ensure assignment exists
        self.assignment, _ = Zuteilung.objects.get_or_create(
            aufgabe=self.task, ausfuehrer=self.user
        )

    def test_timetable_assignment_save(self):
        """Test custom save method of StundenZuteilung."""
        # Ensure no notification is pending
        self.user.mitglied.zuteilungBenachrichtigungNoetig = False
        self.user.mitglied.save()

        # Test creation of timetable assignment
        timetable_assignment = StundenZuteilung(
            zuteilung=self.assignment, uhrzeit=self.timetable_hour
        )
        timetable_assignment.save()
        # Check if timetable_assignment was saved
        try:
            StundenZuteilung.objects.get(
                zuteilung=self.assignment, uhrzeit=self.timetable_hour
            )
        except StundenZuteilung.DoesNotExist:
            self.fail(
                f"StundenZuteilung not found for task {self.task} and user {self.user}."
            )
        # Check if notification is pending
        self.assertTrue(self.user.mitglied.zuteilungBenachrichtigungNoetig)

    def test_timetable_assignment_delete(self):
        """Test custom delete method of StundenZuteilung."""
        # Ensure timetable assignment exists
        timetable_assignment, _ = StundenZuteilung.objects.get_or_create(
            zuteilung=self.assignment, uhrzeit=self.timetable_hour
        )
        # Ensure no notification is pending
        self.user.mitglied.zuteilungBenachrichtigungNoetig = False
        self.user.mitglied.save()

        # Test deletion of timetable assignment
        timetable_assignment.delete()
        # Check if timetable assignment was deleted
        with self.assertRaises(StundenZuteilung.DoesNotExist):
            StundenZuteilung.objects.get(
                zuteilung=self.assignment, uhrzeit=self.timetable_hour
            )
        # Check if notification is pending
        self.assertTrue(self.user.mitglied.zuteilungBenachrichtigungNoetig)


class ZuteilungTests(TestCase):
    """Tests for model Zuteilung."""

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
        self.user = User.objects.get(last_name="Mitglied")

    def test_assignment_save(self):
        """Test custom save method of Zuteilung."""
        # Ensure no notification is pending
        self.user.mitglied.zuteilungBenachrichtigungNoetig = False
        self.user.mitglied.save()

        # Test saving of assignment
        assignment = Zuteilung(aufgabe=self.task, ausfuehrer=self.user)
        assignment.save()
        # Check if assignment was saved
        try:
            Zuteilung.objects.get(aufgabe=self.task, ausfuehrer=self.user)
        except Zuteilung.DoesNotExist:
            self.fail(f"Zuteilung not found for task {self.task} and user {self.user}.")
        # Check if notification is pending
        self.assertTrue(self.user.mitglied.zuteilungBenachrichtigungNoetig)

    def test_assignment_delete(self):
        """Test custom delete method of Zuteilung."""
        # Ensure assignment exists
        assignment, _ = Zuteilung.objects.get_or_create(
            aufgabe=self.task, ausfuehrer=self.user
        )
        # Ensure no notification is pending
        self.user.mitglied.zuteilungBenachrichtigungNoetig = False
        self.user.mitglied.save()

        # Test deletion of assignment
        assignment.delete()
        # Check if assignment was deleted
        with self.assertRaises(Zuteilung.DoesNotExist):
            Zuteilung.objects.get(aufgabe=self.task, ausfuehrer=self.user)
        # Check if notification is pending
        self.assertTrue(self.user.mitglied.zuteilungBenachrichtigungNoetig)
