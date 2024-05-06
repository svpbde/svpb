from django.urls import re_path
from django.views.generic import TemplateView

from svpb.activeTest import active_and_login_required

import boote.views

# place app url patterns here

urlpatterns = [
    # BOOTS 
    re_path(r'boots_liste/$',
         active_and_login_required(boote.views.boot_liste),
         name="boote-liste",
    ),
    re_path(r'^boot/(?P<boot_pk>[0-9]+)/$',
         active_and_login_required(boote.views.boot_detail),
         name="boot-detail",
    ),
    # MY BOAT
    re_path(r'^boot/edit/(?P<boot_pk>[0-9]+)/$',
         active_and_login_required(boote.views.boot_edit),
         name="boot-edit",
    ),
    re_path(r'^boot/edit/$',
         active_and_login_required(boote.views.boot_edit_list),
         name="boot-edit-list",
    ),
    re_path(r'^boot/edit/new/$',
         active_and_login_required(boote.views.boot_edit_new),
         name="boot-edit-new",
    ),
    # BOAT ISSUE
    re_path(r'^boot_fix_issue/(?P<issue_pk>[0-9]+)/$',
         active_and_login_required(boote.views.boot_fix_issue),
         name="booking-remove",
    ),
    re_path(r'^boot_issues/(?P<boot_pk>[0-9]+)/$',
         active_and_login_required(boote.views.boot_issues),
         name="boot-issues",
    ),
    re_path(r'^boot_issues/all/$',
         active_and_login_required(boote.views.boot_issues_all),
         name="boot-issues-all",
    ),
                       
    # BOOKING 
    re_path(r'^booking/overview/$',
         active_and_login_required(boote.views.booking_overview),
         name="booking-overview",
    ),
    re_path(r'^booking/today/$',
         active_and_login_required(boote.views.booking_today),
         name="booking-today",
    ),
    re_path(r'^booking/today/public/$',
         boote.views.booking_today_public,
         name="booking-today-public",
    ),
    re_path(r'^booking/training/public/$',
         boote.views.booking_training_public,
         name="booking-today-public",
    ),      
    re_path(r'^booking/boot/(?P<boot_pk>[0-9]+)/$',
         active_and_login_required(boote.views.booking_boot),
         name="booking-boot",
    ),
    
    re_path(r'^booking/priority/$',
         active_and_login_required(boote.views.booking_priority_boot_list),
         name="priority-booking-boot-list",
    ),
       
    re_path(r'^booking/priority/new/$',
         active_and_login_required(boote.views.booking_priority_boot_new),
         name="priority-booking-boot-new",
    ),
                                        
    re_path(r'^booking/all/$',
         active_and_login_required(boote.views.booking_all),
         name="booking-all",
    ),
    re_path(r'^booking/my_bookings/$',
         active_and_login_required(boote.views.booking_my_bookings),
         name="booking-my-bookings",
    ),
    re_path(r'^booking_remove/(?P<booking_pk>[0-9]+)/$',
         active_and_login_required(boote.views.booking_remove),
         name="booking-remove",
    ),
    

    # OTHER 
    re_path(r'^$',
        active_and_login_required(TemplateView.as_view(template_name="booteHome.html")),
        name="booteHome"),

    re_path(r'^home/',
        active_and_login_required(TemplateView.as_view(template_name="booteHome.html")),
        name="booteHome",
    ),
]
