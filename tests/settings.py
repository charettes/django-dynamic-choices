from __future__ import unicode_literals

from django.conf.global_settings import TEST_RUNNER

DEBUG = True

SECRET_KEY = 'not-anymore'

TIME_ZONE = 'America/Chicago'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

SITE_ID = 1

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'dynamic_choices',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'tests.urls'

if not TEST_RUNNER.endswith('DiscoverRunner'):
    TEST_RUNNER = str('discover_runner.DiscoverRunner')
