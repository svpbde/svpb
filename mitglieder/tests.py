"""Tests of mitglieder administration"""
from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings

from mitglieder import views


class MitgliederTest(TestCase):
    fixtures = [
        "arbeitsplan/fixtures/members.json",
        "arbeitsplan/fixtures/taskgroups.json",
        "arbeitsplan/fixtures/tasks.json",
        "mitglieder/fixtures/groups.json",
        "mitglieder/fixtures/po.json",
        "mitglieder/fixtures/user.json",
    ]
    # In fixtures, all users should have this password
    plainpassword = "Test"
    # "Strong" password passing password validation
    strongpassword = "CZmndjtH3Kyo"
    superuser = "Superuser"
    board = "Vorstand"
    teamleader = "Teamleiter"
    member = "Mitglied"
    users = [superuser, board, teamleader, member]

    def login_user(self, user, password=None):
        cl = Client()
        response = cl.post(
            "/login/",
            {"username": user, "password": password or self.plainpassword},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        return cl, response

    def test_login_works(self):
        for user in self.users:
            cl, response = self.login_user(user)
            self.assertNotIn("login", response.request["PATH_INFO"])

    @override_settings(JAHRESENDE=True)
    def test_login_works_year_end(self):
        # Test blocked users
        for user in [self.member, self.teamleader]:
            cl, response = self.login_user(user, self.plainpassword)
            self.assertContains(
                response,
                "Derzeit ist eine Anmeldung nur für Vorstände möglich.",
            )
        # Test allowed users
        for user in [self.superuser, self.board]:
            cl, response = self.login_user(user, self.plainpassword)
            self.assertNotContains(
                response,
                "Derzeit ist eine Anmeldung nur für Vorstände möglich.",
            )

    def test_wrong_password_fails(self):
        for user in self.users:
            cl, response = self.login_user(user, "xxx")
            self.assertIn("login", response.request["PATH_INFO"])

    def test_add_user(self):
        cl, response = self.login_user(self.superuser)
        response = cl.get("/accounts/add/")
        response = cl.post(
            "/accounts/add/",
            {
                "firstname": "Peter",
                "lastname": "Pan",
                "email": "peter@pan.com",
                "mitgliedsnummer": "666666",
                "geburtsdatum": "01.01.2000",
                "strasse": "Testweg",
                "gender": "M",
                "plz": "12345",
                "ort": "Teststadt",
                "status": "Er",
                "arbeitslast": "12",
            },
            follow=True,
        )

        # Assert the main conditions
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, views.AccountAdd.success_url + "/")
        # TODO: check the success URLs in the various views;
        # they probably should all take a trailing slash

        # Get message from context and check that expected text is there
        message = list(response.context["messages"])[0]
        self.assertEqual(message.tags, "success")
        self.assertIn("erfolgreich angelegt", message.message)

        # Activate user to allow login
        peter = User.objects.get(username="666666")
        peter.is_active = True
        peter.save()

        # Try to get the new password link, check for redirect loop
        cl2 = Client()
        response = cl2.post(
            "/password_reset/",
            {"email": peter.email},
            follow=False,
        )
        self.assertEqual(response.status_code, 302)

        token = response.context[0]['token']
        uid = response.context[0]['uid']
        redirect_response = cl2.get(f"/reset/{uid}/{token}/", follow=True)
        redirect_url = f"/reset/{uid}/set-password/"
        self.assertRedirects(
            redirect_response, redirect_url, fetch_redirect_response=True
        )
        # Reset the old password
        response = cl2.post(
            redirect_url,
            {
                "new_password1": self.strongpassword,
                "new_password2": self.strongpassword,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        # Try to login with the new password
        cl3, response = self.login_user(peter.username, password=self.strongpassword)
        self.assertNotIn("login", response.request["PATH_INFO"])

    def test_profile_incomplete(self):
        cl, response = self.login_user(self.superuser)
        self.assertNotIn("login", response.request["PATH_INFO"])

        message = list(response.context["messages"])[0]
        self.assertEqual(message.tags, "warning")
        self.assertContains(response, "Profilangaben sind unvoll")

        # Add a phone number, and then log out and log in again
        response = cl.get("/accounts/edit/")
        form = response.context["form"]
        data = form.initial
        data["festnetz"] = "030 12312345"
        # Note: all fields must have values, else validation
        # throws up errors and the form is not redirected
        data["mobil"] = ""

        response = cl.post("/accounts/edit/", data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual("/", response.request["PATH_INFO"])

        # Note the use of lambda, to make sure the expression
        # that raises the error is passed to assertRaises!
        self.assertRaises(
            KeyError,
            lambda: response.context["form"].errors,
        )

        # Did we get plausible data back?
        su = User.objects.get(username=self.superuser)
        self.assertIsNotNone(su.mitglied.festnetz)

        # Log back in again
        cl2, response = self.login_user(self.superuser)
        # We should end up on home
        self.assertEqual("/home/", response.request["PATH_INFO"])
        # There must be no message on the home page:
        self.assertListEqual([], list(response.context["messages"]))

    def test_change_password(self):
        cl, response = self.login_user(self.superuser)
        self.assertNotIn("login", response.request["PATH_INFO"])

        # Initiate password change
        response = cl.get("/password_change/")
        form = response.context["form"]
        data = form.initial
        data["old_password"] = self.plainpassword
        data["new_password1"] = self.strongpassword
        data["new_password2"] = data["new_password1"]

        # Actually change password
        response = cl.post("/password_change/", data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual("/password_change/done/", response.request["PATH_INFO"])
        self.assertContains(response, "Dein Passwort wurde erfolgreich")

        # Test login with new password
        cl, response = self.login_user(
            self.superuser, self.strongpassword
        )
        self.assertNotIn("login", response.request["PATH_INFO"])
