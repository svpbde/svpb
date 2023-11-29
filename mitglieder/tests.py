"""Tests of mitglieder administration
"""
from django.contrib.auth.models import User
from django.test import Client, TestCase

from pprint import pprint as pp

from mitglieder import views


class MitgliederTest(TestCase):
    fixtures = [
        'arbeitsplan/fixtures/members.json',
        'arbeitsplan/fixtures/taskgroups.json',
        'arbeitsplan/fixtures/tasks.json',
        'mitglieder/fixtures/groups.json',
        'mitglieder/fixtures/po.json',
        'mitglieder/fixtures/user.json'
    ]
    plainpassword = "Test"
    superuser = "Superuser"

    def login_user(self, user, password=None):
        cl = Client()

        response = cl.post(
            '/login/',
            {'username': user,
             'password': password or self.plainpassword},
            follow=True,
            )

        # pp(response)
        # pp(response.status_code)
        # pp(response.redirect_chain)
        # print "----"
        # print "Content:"
        # pp(response.content)
        # print "----"
        # print "Context:"
        # pp(len(response.context))
        # pp(response.context)
        # print "-----"
        # print "messages:"
        # pp([m.message for m in list(response.context['messages'])])

        self.assertTrue(response.status_code == 200)

        return cl, response

    def test_login_works(self):
        cl, response = self.login_user(self.superuser)

        # print "analysing context:"
        # pp(response.request)
        # print "----"
        # pp(response.context[-1])
        # pp([m.message for m in list(response.context['messages'])])

        self.assertTrue('login' not in response.request['PATH_INFO'])

    def test_wrong_password_fails(self):
        cl, response = self.login_user(self.superuser, "xxx")
        self.assertFalse('login' not in response.request['PATH_INFO'])

    def test_add_user(self):

        print("adding user")

        cl, response = self.login_user(self.superuser)

        # print "adding"

        response = cl.get(
                '/accounts/add/')

        # print "response after get:"
        pp(response)

        response = cl.post(
            '/accounts/add/',
            {'firstname': 'Peter',
             'lastname': 'Pan',
             'email': 'peter@pan.com',
             'mitgliedsnummer': '666666',
             'geburtsdatum': '01.01.2000',
             'strasse': 'Testweg',
             'gender': 'M',
             'plz': '12345',
             'ort': 'Teststadt',
             'status': "Er",
             'arbeitslast': '12',
             },
            follow=True,
        )

        # assert the main conditions:
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response,
                             views.AccountAdd.success_url + '/')
        # TODO: check the success URLs in the various views;
        # they probably should all take a trailing slash

        # get message from context and check that expected text is there
        message = list(response.context['messages'])[0]
        self.assertEqual(message.tags, "success")
        self.assertTrue("erfolgreich angelegt" in message.message)

        # self.assertFormError(response,)
        print("response after post:")
        pp(response)
        pp(response.status_code)

        # Activate user to allow login
        peter = User.objects.get(username="666666")
        peter.is_active = True
        peter.save()

        # try to get the new password link:
        # check: does this have a redirect loop?
        cl2 = Client()
        response = cl2.post(
            '/reset/recover/',
            {'username_or_email': '666666'},
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        pp(response.context)

        from django.core.mail import outbox
        sentmail = outbox[0]
        # sentmail should be an instance ov django.core.mail.message.EmailMultiAlternatives
        body = sentmail.body

        # grab the reset URL out of the mail body.
        # we exploit the fact that the URL sits on a separate page
        import re
        url = re.search('/reset/reset/.*/', body)
        url = url.group(0)

        # and sent the new password there:
        response = cl2.post(url,
                            {'password1': self.plainpassword,
                             'password2': self.plainpassword,},
                            follow=True)

        self.assertEqual(response.status_code, 200)

        # and now try to login with the new password
        cl3, response = self.login_user('666666')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('login' not in response.request['PATH_INFO'])

    def test_profile_incomplete(self):
        cl, response = self.login_user(self.superuser)
        self.assertEqual(response.status_code, 200)

        message = list(response.context['messages'])[0]

        self.assertEqual(message.tags, "warning")

        self.assertContains(response,
                            "Profilangaben sind unvoll")

        # Add a phone number , and then log out and login again
        response = cl.get("/accounts/edit/")

        form = response.context['form']

        data = form.initial
        data['festnetz'] = "030 12312345"
        # Note: all fields must have values, else validation
        # throws up errors and the form is not redirected
        data['mobil'] = ""

        response = cl.post('/accounts/edit/',
                            data,
                           follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual("/", response.request['PATH_INFO'])

        # Note: the use of lambda, to make sure the expression
        # that raises the error is passed to assertRaises!
        self.assertRaises(KeyError,
                          lambda: response.context['form'].errors,
                          )

        # did we get plausible data back?
        su = User.objects.first()
        self.assertIsNotNone(su.mitglied.festnetz)

        # log back in again; now the error should be gone
        cl2, response = self.login_user(self.superuser)
        self.assertEqual(response.status_code, 200)

        # we should end up on home:
        self.assertEqual("/", response.request['PATH_INFO'])

        # there must be no message on the home page:
        pp(response.context['messages'])
        pp(list(response.context['messages']))
        self.assertListEqual([], list(response.context['messages']))
        # self.assertRaises(KeyError,
        #                   lambda: response.context['messages'])

    def test_change_password(self):
        cl, response = self.login_user(self.superuser)
        self.assertEqual(response.status_code, 200)

        response = cl.get("/password/change/")

        form = response.context['form']

        data = form.initial
        data['pw1'] = self.plainpassword + self.plainpassword
        data['pw2'] = data['pw1']

        response = cl.post("/password/change/",
                           data,
                           follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual("/", response.request['PATH_INFO'])

        self.assertContains(response,
                            "Ihr Passwort wurde erfolgreich")

        cl, response = self.login_user(self.superuser,
                                       self.plainpassword + self.plainpassword)
        self.assertEqual(response.status_code, 200)
