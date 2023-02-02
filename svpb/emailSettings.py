# email settings:
EMAIL_HOST = ''
EMAIL_PORT = 465

DEFAULT_FROM_EMAIL = "test@test.com"
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = "XXX"
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True

# Use console mail backend for local testing and debugging
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Use the standard django SMTP backend for production
# Note that in addition to the standard django backend, post_office is used for
# mass mailings (is explicitly imported where needed).
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
