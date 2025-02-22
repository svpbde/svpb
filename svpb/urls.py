from django.conf import settings
from django.urls import include, re_path, path
from django.conf.urls.static import static
from django.views.generic import RedirectView, TemplateView
from django.contrib.auth import views as auth_views

from django.contrib import admin

import arbeitsplan.views
from mitglieder.forms import SVPBPasswordChangeForm
import mitglieder.views
import svpb.views
from svpb.forms import SVPBAuthenticationForm

from .activeTest import active_and_login_required


admin.autodiscover()


urlpatterns = [

    re_path(r'^$',
        TemplateView.as_view(
            template_name="main.html",
            extra_context={"year_end": settings.JAHRESENDE},
        ),
        name="main",
        ),

    re_path(r'^home/$',
        TemplateView.as_view(
            template_name="main.html",
            extra_context={"year_end": settings.JAHRESENDE},
        ),
        name="mainHome",
        ),

    re_path(r'^keinVorstand/$',
        TemplateView.as_view(template_name='keinVorstand.html'),
        name="keinVorstand",
        ),

    re_path(r'^arbeitsplan/', include('arbeitsplan.urls')),

    re_path(r'^accounts/', include('mitglieder.urls')),

    re_path(r'^boote/', include('boote.urls')),

    re_path(r'^about$',
        TemplateView.as_view(template_name="about.html"),
        name="about",
        ),

    re_path(r'^dsgvo$',
        TemplateView.as_view(template_name="datenschutzerklaerung.html"),
        name="about",
        ),

    # Redirect admin login to our custom login
    path("svpb-admin/login/", RedirectView.as_view(pattern_name="login")),
    # Move admin to non-default URL to hide it from bots
    re_path(r"^svpb-admin/", admin.site.urls),

    path(
        'login/',
        auth_views.LoginView.as_view(
            authentication_form=SVPBAuthenticationForm,
            extra_context={"year_end": settings.JAHRESENDE},
        ),
        name="login"
    ),

    re_path(r'^logout/', svpb.views.logout_view),

    # media for manual intergration:
    re_path(r'^manual/',
        active_and_login_required(arbeitsplan.views.MediaChecks.as_view()),
        name="MediaCheck",
        ),

    # Impersonation of other users:
    re_path(r'^impersonate/liste/$',
        active_and_login_required(mitglieder.views.ImpersonateListe.as_view()),
        name="arbeitsplan-impersonateListe",
        ),
    re_path(r'^impersonate/', include('impersonate.urls')),

    # django select2, see: https://github.com/codingjoe/django-select2
    re_path(r'^select2/', include('django_select2.urls')),

    # Include specific django auth views for password change
    path(
        "password_change/",
        auth_views.PasswordChangeView.as_view(form_class=SVPBPasswordChangeForm),
        name="password_change"
    ),
    path(
        "password_change/done/",
        auth_views.PasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
    # Include specific django auth views for password reset
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(),
        name="password_reset"
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]

if settings.DEBUG:
    # See https://docs.djangoproject.com/en/4.2/howto/static-files/#serving-uploaded-files-in-development
    # Check for debug is already included in static.
    # But we should include a check if we are in the VM, were we want to use nginx despite debug being true
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
