#!/usr/bin/python

from setuptools import setup, find_packages

setup(
    name='django-dynamic-choices',
    version='0.1',
    description='Django admin fk and m2m dynamic choices by providing callback support',
    long_description='Provide fk and m2m dynamic choices and react to django.contrib.admin edit/add view interaction to update those choices',
    url='https://github.com/charettes/django-dynamic-choices',
    author='Simon Charette',
    author_email='charette.s@gmail.com',
    install_requires=[
        'Django>=1.2',
    ],
    packages=find_packages(exclude=['testapp']),
    include_package_data=True
)
