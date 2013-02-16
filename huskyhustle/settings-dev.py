# Django settings for huskyhustle project.
import base64

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Your Name', 'you@example.com'),
)

MANAGERS = ADMINS

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_PASSWORD = base64.b64decode('')
EMAIL_HOST_USER = 'you@example.com'
EMAIL_SUBJECT_PREFIX = 'HH: '
EMAIL_USE_TLS = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'huskyhustle/husky-hustle.db',  # Or path to database file if using sqlite3.
        'USER': '',                             # Not used with sqlite3.
        'PASSWORD': '',                         # Not used with sqlite3.
        'HOST': '',                             # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                             # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Los_Angeles'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 2

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = 'huskyhustle/husky/static'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
STATIC_URL = '/static/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '*nzo2z3hdye73y%+l473v_pt46il#g$+4mp)6^#8-n)v8vp)jf'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    # 'django_mobile.loader.Loader',
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    # 'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.request',
    # 'django_mobile.context_processors.flavour',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # 'django_mobile.middleware.MobileDetectionMiddleware',
    # 'django_mobile.middleware.SetFlavourMiddleware',
)

MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'

ROOT_URLCONF = 'huskyhustle.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

#AUTH_USER_MODEL = 'huskyhustle.Parent'
#AUTH_PROFILE_MODULE = 'huskyhustle.Parent'

# days before activation expires
ACCOUNT_ACTIVATION_DAYS = 7

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'socialregistration.contrib.twitter.auth.TwitterAuth',
    'socialregistration.contrib.facebook.auth.FacebookAuth',
    # 'socialregistration.contrib.facebook.auth.InstagramAuth',
    'socialregistration.contrib.openid.auth.OpenIDAuth',
)

FACEBOOK_APP_ID = ''
FACEBOOK_SECRET_KEY = ''
FACEBOOK_REQUEST_PERMISSIONS = ''

TWITTER_CONSUMER_KEY = ''
TWITTER_CONSUMER_SECRET_KEY = ''
TWITTER_REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
TWITTER_ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
TWITTER_AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'

INSTAGRAM_APP_ID = ''
INSTAGRAM_SECRET_KEY = ''

SOCIALREGISTRATION_USE_HTTPS = False
SOCIALREGISTRATION_GENERATE_USERNAME = False

BITLY_LOGIN = ''
BITLY_APIKEY = ''

PAYPAL_PAYPAL_CERT = 'certs/paypal_cert.pem'
PAYPAL_PRIVATE_KEY = 'certs/private_key.pem'
PAYPAL_PUBLIC_KEY = 'certs/public_key.pem'
PAYPAL_IPN_URL = 'https://www.sandbox.paypal.com/cgi-bin/webscr'
PAYPAL_CERT_ID = base64.b64decode('')
PAYPAL_BUS_ID = base64.b64decode('')

PICASA_STORAGE_OPTIONS = {
    'email': 'you@example.com',
    'source': 'example',
    'password': base64.b64decode(''),
    'userid': 'exampleid',
    'cache': True
}

CACHE_BACKEND = "locmem://?timeout=30&max_entries=400"

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'socialregistration',
    'socialregistration.contrib.facebook',
    'socialregistration.contrib.twitter',
    # 'socialregistration.contrib.instagram',
    'socialregistration.contrib.openid',
    'djangorestframework',
    # 'django_mobile',
    'registration',
    'picasa',
    'husky',
)
