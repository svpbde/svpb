"""Settings for local development with sqlite."""
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
TEMPLATE_DEBUG = DEBUG

# Make this unique, and don't share it with anybody.
SECRET_KEY = '26w5_t=fcjff6vk9$ee(03xa&+1c($ot1ixg)p-f(%v#ad$dqy'

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost'
    ]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'svpb.sq',
        # The following settings are not used with sqlite3:
        'USER': 'UserPlaceholder',
        'PASSWORD': 'PasswordPlaceholder',
        'HOST': '127.0.0.1',
        'PORT': '',  # Set to empty string for default.
    }
}

# email settings:
EMAIL_HOST = ''
EMAIL_PORT = 465
DEFAULT_FROM_EMAIL = 'test@example.com'
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True

# Use console mail backend for local testing and debugging
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Mail addresses to send notifications to
EMAIL_NOTIFICATION_BOARD = ['vorstand@example.com', ]
EMAIL_NOTIFICATION_BOATS = ['boote@example.com', ]

# XSendfile interface
# Development backend should never be used in production!
SENDFILE_BACKEND = 'django_sendfile.backends.development'
