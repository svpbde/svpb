from django.urls import re_path
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

import mitglieder.forms
from svpb.activeTest import active_and_login_required

import mitglieder.views

urlpatterns = [
    re_path(r'^$',
        active_and_login_required(TemplateView.as_view(template_name="mitgliederHome.html")),
        name="mitgliederHome"),

    re_path(r'^home/',
        active_and_login_required(TemplateView.as_view(template_name="mitgliederHome.html")),
        name="mitgliederHome"),

    # url (r'^accounts/login/', login),
    re_path(r'^activate/',
         login_required(mitglieder.views.ActivateView.as_view()),
         name="activate"),

    # to edit my own account:
    re_path(r'^edit/',
        active_and_login_required(mitglieder.views.AccountEdit.as_view()),
        name="accountEdit"),

    # to edit other people:
    re_path(r'^editOther/(?P<id>\d+)/',
        active_and_login_required(mitglieder.views.AccountOtherEdit.as_view()),
        name="accountOtherEdit"),

    re_path(r'^delete/(?P<pk>\d+)/',
        active_and_login_required(mitglieder.views.AccountDelete.as_view()),
        name="accountDelete"),

    re_path(r'^add/',
        active_and_login_required(mitglieder.views.AccountAdd.as_view()),
        name="accountAdd"
        ),

    re_path(r'^list/',
        active_and_login_required(mitglieder.views.AccountList.as_view()),
        name="accountList"
        ),

    re_path(r'^filteredList/',
        active_and_login_required(mitglieder.views.FilteredMemberList.as_view()),
        name="accountFilteredList"
        ),

    re_path(r'^inaktiveReset/',
        active_and_login_required(mitglieder.views.AccountInactiveReset.as_view()),
        name="accountInactiveReset"
        ),

    re_path(r'^letters.pdf',
        active_and_login_required(mitglieder.views.AccountLetters.as_view()),
        name="accountLetters"
        ),

    # sammlung aller Mitglieder
    re_path(r'^mitgliederexcel.xlsx',
        active_and_login_required(mitglieder.views.MitgliederExcel.as_view()),
        name="mitgliedExcel"
        ),

   ]
