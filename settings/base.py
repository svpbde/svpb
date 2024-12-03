"""Base Django settings for svpb project."""
from pathlib import Path

from django.contrib.messages import constants as messages


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

ADMINS = [
    # ('Your Name', 'your_email@example.com'),
]
MANAGERS = ADMINS

JAHRESSTUNDEN = 12
JAHRESENDE = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django_extensions',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    # 'django_admin_bootstrapped.bootstrap3',
    # 'django_admin_bootstrapped',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'django_tables2',
    'crispy_bootstrap5',
    'crispy_forms',
    'impersonate',
    'post_office',
    'django_sendfile',
    'django_select2',
    'fontawesomefree',
    # svpb apps
    'arbeitsplan',
    'boote',
    'mitglieder',
    'svpb',
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'impersonate.middleware.ImpersonateMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'svpb.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'svpb.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            ],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': True,
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
                'svpb.context_processors.global_settings'
            ],
        },
    },
]

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/
TIME_ZONE = 'Europe/Berlin'
LANGUAGE_CODE = 'de'
SITE_ID = 1
USE_I18N = True
USE_L10N = True
USE_TZ = True
PHONENUMBER_DEFAULT_REGION = "DE"

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'
LOGIN_URL = '/login/'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/
STATIC_URL = '/static/'
SENDFILE_URL = '/sendfile/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = BASE_DIR / 'www' / 'static'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = BASE_DIR / 'www' / 'media'
SENDFILE_ROOT = BASE_DIR / 'www' / 'sendfile'

# Additional locations of static files
STATICFILES_DIRS = [
    BASE_DIR / 'site_static'
]

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# for select2:
SELECT2_CSS = [
    # Use select2 included with django-admin (django-select2 default)
    "admin/css/vendor/select2/select2.min.css",
    # Include bootstrap theme AFTER select2
    "select2-bootstrap/select2-bootstrap-5-theme.min.css"
]
SELECT2_THEME = "bootstrap-5"

IMPERSONATE = {
    'REDIRECT_URL': '/',
    'CUSTOM_ALLOW': 'settings.base.user_is_vorstand',
}

# Set bootstrap5 as default layout for all tables generated by django-tables2
DJANGO_TABLES2_TEMPLATE = "django_tables2/bootstrap5.html"
DJANGO_TABLES2_TABLE_ATTRS = {
    "class": "table table-hover table-striped border",
    "style": "width: auto;",
    "thead": {
        "class": "sticky-top",
    },
}

# Customize message tags for usage with bootstrap alerts
# See https://docs.djangoproject.com/en/5.0/ref/contrib/messages/#message-tags
MESSAGE_TAGS = {
    messages.DEBUG: "secondary",
    messages.ERROR: "danger",
}


def user_is_vorstand(request):
    return request.user.groups.filter(name="Vorstand")
