#!/usr/bin/env python
from __future__ import unicode_literals

import argparse
import sys

from django.conf import settings


SETTINGS = {
    'SECRET_KEY': 'secret',
    'INSTALLED_APPS': (
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.sites',
        'django.contrib.admin',
        'dynamic_choices',
    ),
    'DATABASES': {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    },
    'ROOT_URLCONF': 'dynamic_choices.tests.urls',
}

def main(verbosity, failfast, test_labels):
    if not test_labels:
        test_labels = ('dynamic_choices',)
    settings.configure(**SETTINGS)
    from django.test.utils import get_runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=verbosity, interactive=False, failfast=failfast)
    failures = test_runner.run_tests(test_labels)
    sys.exit(failures)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--failfast', action='store_true', default=False,
                        dest='failfast')
    parser.add_argument('--verbosity', default=1)
    parser.add_argument('test_labels', nargs='*')
    args = parser.parse_args()
    main(args.verbosity, args.failfast, args.test_labels)
