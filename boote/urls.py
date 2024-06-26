from django.conf.urls import url
from django.views.generic import TemplateView

from svpb.activeTest import active_and_login_required

import boote.views

# place app url patterns here

urlpatterns = [
    # BOOTS
    url(
        r"boots_liste/$",
        active_and_login_required(boote.views.boot_liste),
        name="boote-liste",
    ),
    url(
        r"^boot/(?P<boot_pk>[0-9]+)/$",
        active_and_login_required(boote.views.boot_detail),
        name="boot-detail",
    ),
    # MY BOAT
    url(
        r"^boot/edit/(?P<boot_pk>[0-9]+)/$",
        active_and_login_required(boote.views.boot_edit),
        name="boot-edit",
    ),
    url(
        r"^boot/edit/$",
        active_and_login_required(boote.views.boot_edit_list),
        name="boot-edit-list",
    ),
    url(
        r"^boot/edit/new/$",
        active_and_login_required(boote.views.boot_edit_new),
        name="boot-edit-new",
    ),
    # BOAT ISSUE
    url(
        r"^boot_fix_issue/(?P<issue_pk>[0-9]+)/$",
        active_and_login_required(boote.views.boot_fix_issue),
        name="booking-remove",
    ),
    url(
        r"^boot_issues/(?P<boot_pk>[0-9]+)/$",
        active_and_login_required(boote.views.boot_issues),
        name="boot-issues",
    ),
    url(
        r"^boot_issues/all/$",
        active_and_login_required(boote.views.boot_issues_all),
        name="boot-issues-all",
    ),
    # BOOKING
    url(
        r"^booking/overview/$",
        active_and_login_required(boote.views.booking_overview),
        name="booking-overview",
    ),
    url(
        r"^booking/today/$",
        active_and_login_required(boote.views.booking_today),
        name="booking-today",
    ),
    url(
        r"^booking/today/public/$",
        boote.views.booking_today_public,
        name="booking-today-public",
    ),
    url(
        r"^booking/training/public/$",
        boote.views.booking_training_public,
        name="booking-today-public",
    ),
    url(
        r"^booking/boot/(?P<boot_pk>[0-9]+)/$",
        active_and_login_required(boote.views.booking_boot),
        name="booking-boot",
    ),
    url(
        r"^booking/priority/$",
        active_and_login_required(boote.views.booking_priority_boot_list),
        name="priority-booking-boot-list",
    ),
    url(
        r"^booking/priority/new/$",
        active_and_login_required(boote.views.booking_priority_boot_new),
        name="priority-booking-boot-new",
    ),
    url(
        r"^booking/all/$",
        active_and_login_required(boote.views.booking_all),
        name="booking-all",
    ),
    url(
        r"^booking/my_bookings/$",
        active_and_login_required(boote.views.booking_my_bookings),
        name="booking-my-bookings",
    ),
    url(
        r"^booking_remove/(?P<booking_pk>[0-9]+)/$",
        active_and_login_required(boote.views.booking_remove),
        name="booking-remove",
    ),
    # OTHER
    url(
        r"^$",
        active_and_login_required(TemplateView.as_view(template_name="booteHome.html")),
        name="booteHome",
    ),
    url(
        r"^home/",
        active_and_login_required(TemplateView.as_view(template_name="booteHome.html")),
        name="booteHome",
    ),
]
