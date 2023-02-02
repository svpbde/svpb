# Django settings for svpb project.

import os
## let's find the root from where the server runs: 
APPLICATION_DIR = os.path.dirname( globals()[ '__file__' ] )

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

LOGIN_URL = "/login/"

OFFLINE = False
JAHRESENDE = False


# DEBUG = False
DEBUG = True

TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        # Use postgresql in production
        # 'ENGINE': 'django.db.backends.postgresql_psycopg2',
        # Use file-based db for local testing and debugging
        'ENGINE': 'django.db.backends.sqlite3',
        # Database name (for sqlite3 this is the file name)
        'NAME': 'svpb.sq',
        # The following settings are not used with sqlite3:
        'USER': 'UserPlaceholder',
        'PASSWORD': 'PasswordPlaceholder',
        'HOST': '127.0.0.1',
        'PORT': '',  # Set to empty string for default.
    }
}

# print(f"DATABASE: {DATABASES['default']['ENGINE']}")
    
# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [".svpb.de", "127.0.0.1", ".h00227.host-up.de"]

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/Berlin'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'de'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = os.path.join (APPLICATION_DIR, '..', 'media')


# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = 'media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = '/home/svpb/svpb/static'

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    # os.path.join (APPLICATION_DIR, '..', 'arbeitsplan', 'static'),
    os.path.join (APPLICATION_DIR, '..', 'boote', 'static'),
    os.path.join (APPLICATION_DIR, '..', 'templates'),
)


# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '26w5_t=fcjff6vk9$ee(03xa&+1c($ot1ixg)p-f(%v#ad$dqy'

# List of callables that know how to import templates from various sources.
# TEMPLATE_LOADERS = (
#    'django.template.loaders.filesystem.Loader',
#    'django.template.loaders.app_directories.Loader',
#    'django.template.loaders.eggs.Loader',
#)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth', 
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'svpb.context_processors.global_settings', 
    ) 


TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join (APPLICATION_DIR, '../templates'), 
    os.path.join (APPLICATION_DIR, 'templates'),
    os.path.join (APPLICATION_DIR, '../arbeitsplan/templates'),
    os.path.join (APPLICATION_DIR, '../mitglieder/templates'),
    os.path.join (APPLICATION_DIR, '../boote/templates'),
)

# New TEMPLATES as of Django 1.8, compare https://docs.djangoproject.com/en/1.8/ref/templates/upgrading/

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': TEMPLATE_DIRS, 
        'APP_DIRS': True,
        'OPTIONS': {
            'debug' : True,
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
            ],
        },
    },
]    
    
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'impersonate.middleware.ImpersonateMiddleware',
)

# as of Django 1.8: https://stackoverflow.com/questions/56923576/django-e-408-e-409-and-e-410-errors-on-runserver
MIDDLEWARE = MIDDLEWARE_CLASSES

    
IMPERSONATE_REDIRECT_URL = "/"

def user_is_vorstand(request):
    return request.user.groups.filter(name="Vorstand")
IMPERSONATE_CUSTOM_ALLOW = "svpb.settings.user_is_vorstand"


ROOT_URLCONF = 'svpb.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'svpb.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    ## 'django_admin_bootstrapped.bootstrap3',
    ## 'django_admin_bootstrapped',
    'django.contrib.admin',
    'django_extensions',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'django_tables2',
    'crispy_forms',
    'impersonate',
    'arbeitsplan',
    'boote',
    'post_office',
    'sendfile',
    'password_reset',
    'django_select2',
)

CRISPY_TEMPLATE_PACK = "bootstrap3"


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

#####################
# Own settings:

from django.contrib.messages import constants as message_constants
MESSAGE_TAGS = {message_constants.DEBUG: 'debug',
                message_constants.INFO: 'info',
                message_constants.SUCCESS: 'success',
                message_constants.WARNING: 'warning',
                message_constants.ERROR: 'danger',}

## Migration to Phyton3
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

#####
# XSendfilte interface
# this will only work with nginx, not in development setup - but that's not too important to test there

SENDFILE_BACKEND = "sendfile.backends.nginx"
SENDFILE_ROOT = os.path.join(STATIC_ROOT, "media/doc")
SENDFILE_URL = "/media/doc"


JAHRESSTUNDEN = 12

# for select2: 
SELECT2_BOOTSTRAP = False
AUTO_RENDER_SELECT2_STATICS = False


# for phonenumbers:
PHONENUMBER_DEFAULT_REGION = "DE"
