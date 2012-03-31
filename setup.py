#!/usr/bin/python

from setuptools import setup, find_packages

from dynamic_choices import VERSION

github_url = 'https://github.com/charettes/django-dynamic-choices'
long_desc = '''
%s

%s
''' % (open('README').read(), open('CHANGELOG').read())

setup(
    name='django-dynamic-choices',
    version='.'.join(str(v) for v in VERSION),
    description='Django admin fk and m2m dynamic choices by providing callback support',
    long_description=long_desc,
    url=github_url,
    author='Simon Charette',
    author_email='charette.s@gmail.com',
    requires=[
        'django (>=1.3.1)'
    ],
    packages=find_packages(exclude=['testapp']),
    include_package_data=True,
    license='MIT License',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
