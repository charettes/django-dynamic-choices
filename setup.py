#!/usr/bin/env python
from setuptools import setup, find_packages

from dynamic_choices import VERSION


github_url = 'https://github.com/charettes/django-dynamic-choices'
long_desc = '''
%s

%s
''' % (open('README.rst').read(), open('CHANGELOG').read())

setup(
    name='django-dynamic-choices',
    version='.'.join(str(v) for v in VERSION),
    description='Django admin fk and m2m dynamic choices by providing callback support',
    long_description=long_desc,
    url=github_url,
    author='Simon Charette',
    author_email='charette.s+django-dynamic-choices@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords=['django admin choices dynamic'],
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=['Django>=1.4,<1.8'],
    include_package_data=True,
)
