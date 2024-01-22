"""Tests of arbeitsplan app"""
from django.core import mail
from django.core.management import call_command
from django.test import Client, TestCase

from arbeitsplan.models import Mitglied


class SimpleTest(TestCase):
    fixtures = [
        'arbeitsplan/fixtures/members.json',
        'arbeitsplan/fixtures/taskgroups.json',
        'arbeitsplan/fixtures/tasks.json',
        'mitglieder/fixtures/groups.json',
        'mitglieder/fixtures/po.json',
        'mitglieder/fixtures/user.json'
    ]
    # In fixtures, all users should have this password
    plainpassword = "Test"
    superuser = "Superuser"

    def login_user(self, user):
        cl = Client()
        response = cl.post(
            '/login/',
            {'username': user,
             'password': self.plainpassword},
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
        response = cl.get('/arbeitsplan/leistungenBearbeiten/z=me/')
        self.assertEqual(response.status_code, 200)

        # and with some qualifiers:
        response = cl.get('/arbeitsplan/leistungenBearbeiten/z=me/?last_name=&first_name=&aufgabengruppe=3&von=&bis=&status=OF&status=RU&filter=Filter+anwenden')
        self.assertEqual(response.status_code, 200)

    def test_zuteilung_email(self):
        """do the zuteilung emails look right?"""
        # Make sure there is at least a single user with a zuteilung_noetig true
        u = Mitglied.objects.get(mitgliedsnummer="00003")
        u.zuteilungBenachrichtigungNoetig = True
        u.save()

        cl, response = self.login_user(self.superuser)

        response = cl.get("/arbeitsplan/benachrichtigen/zuteilung/",
                          follow=True)
        self.assertEqual(response.status_code, 200)
        # the user's email must appear in the response page:
        self.assertContains(response, u.user.email, html=False)

        # let's generate the email
        response = cl.post("/arbeitsplan/benachrichtigen/zuteilung/",
                           {'eintragen': 'Benachrichtigungen eintragen',
                            'sendit_4': 'on',
                            'ergaenzung': 'ergaenzungtest',
                            'anmerkung_4': 'anmerkungtest'},
                           follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

        # and actually send it off:
        call_command("send_queued_mail")
        self.assertEqual(len(mail.outbox), 1)
        print(mail.outbox[0])
