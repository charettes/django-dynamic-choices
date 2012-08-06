from contextlib import contextmanager
import json
import os

import django
from django import forms
from django.conf import settings
from django.core.exceptions import (FieldError, ImproperlyConfigured,
    ValidationError)
from django.core.urlresolvers import reverse
from django.db.models import Model
from django.test import TestCase
from django.test.client import Client

from dynamic_choices.admin import DynamicAdmin
from dynamic_choices.db.models import DynamicChoicesForeignKey
from dynamic_choices.forms import DynamicModelForm
from dynamic_choices.forms.fields import (DynamicModelMultipleChoiceField,
    DynamicModelChoiceField)

from .admin import PuppetAdmin
from .models import Master, Puppet, ALIGNMENT_EVIL, ALIGNMENT_GOOD


MODULE_PATH = os.path.abspath(os.path.dirname(__file__))

class DynamicForeignKeyTest(TestCase):
    fixtures = ('dynamic_choices_test_data',)

    def setUp(self):
        self.good_master = Master.objects.get(alignment=ALIGNMENT_GOOD)

    def test_valid_value(self):
        puppet = Puppet(master=self.good_master, alignment=ALIGNMENT_GOOD)
        puppet.full_clean()

    def test_invalid_value(self):
        puppet = Puppet(master=self.good_master, alignment=ALIGNMENT_EVIL)
        self.failUnlessRaises(ValidationError, puppet.full_clean)


class DynamicOneToOneField(TestCase):
    fixtures = ('dynamic_choices_test_data',)

    def setUp(self):
        self.good_puppet = Puppet.objects.get(alignment=ALIGNMENT_GOOD)
        self.evil_puppet = Puppet.objects.get(alignment=ALIGNMENT_EVIL)

    def test_valid_value(self):
        self.evil_puppet.secret_lover = self.good_puppet
        self.evil_puppet.full_clean()
        self.evil_puppet.save()
        self.assertEqual(self.good_puppet.secretly_loves_me,
                         self.evil_puppet)
        self.good_puppet.secret_lover = self.evil_puppet
        self.good_puppet.full_clean()

    def test_invalid_value(self):
        self.evil_puppet.secret_lover = self.good_puppet
        self.evil_puppet.save()
        # narcissus style
        self.good_puppet.secret_lover = self.good_puppet
        self.failUnlessRaises(ValidationError, self.good_puppet.full_clean,
                              """Since the evil puppet secretly loves the good puppet
                              the good puppet can only secretly love the bad puppet.""")


class ImproperlyConfiguredAmin(TestCase):
    if django.VERSION[0:2] <= (1, 3):
        @contextmanager
        def settings(self, **kwargs):
            original = {}
            try:
                for key, value in kwargs.iteritems():
                    original[key] = getattr(settings, key)
                    setattr(settings, key, value)
                yield
            finally:
                for key, value in original.iteritems():
                    setattr(settings, key, value)

    def test_change_form_template_override(self):
        """
        Make sure ImproperlyConfigured exceptions are raised when a
        `DynamicAdmin` subclass defines a `change_form_template` which do not
        extends `admin/dynamic_choices/change_form.html`.
        """
        TEMPLATE_LOADERS = (
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        )
        TEMPLATE_DIRS = (
            os.path.join(MODULE_PATH, 'templates'),
        )
        with self.settings(TEMPLATE_LOADERS=TEMPLATE_LOADERS,
                           TEMPLATE_DIRS=TEMPLATE_DIRS):
            with self.assertRaises(ImproperlyConfigured):
                type('ChangeFormDoNotExtends', (DynamicAdmin,),
                     {'change_form_template': 'dynamic_choices_tests/do_not_extends_change_form.html'})
            try:
                type('ChangeFormExtends', (DynamicAdmin,),
                     {'change_form_template': 'dynamic_choices_tests/extends_change_form.html'})
            except ImproperlyConfigured:
                self.fail('Overriding the `change_form_template` on a '
                          '`DynamicAdmin` subclass should work when the '
                          'specified template extends "admin/dynamic_choices/change_form.html"')
            try:
                type('ChangeFormExtendsChild', (DynamicAdmin,),
                     {'change_form_template': 'dynamic_choices_tests/extends_change_form_twice.html'})
            except ImproperlyConfigured:
                self.fail('Overriding the `change_form_template` on a '
                          '`DynamicAdmin` subclass should work when the '
                          'specified template extends "admin/dynamic_choices/change_form.html" '
                          'indirectly.')


class AdminTest(TestCase):
    urls = 'dynamic_choices.tests.urls'
    fixtures = ('dynamic_choices_test_data', 'dynamic_choices_admin_test_data')

    def setUp(self):
        self.client = Client()
        self.client.login(username='superuser', password='sudo')


class DynamicAdminFormTest(AdminTest):
    def assertChoices(self, queryset, field, msg=None):
        self.assertEqual(list(queryset), list(field.widget.choices.queryset), msg)

    def assertEmptyChoices(self, field, msg=None):
        return self.assertChoices((), field, msg=msg)

    def test_GET_add(self):
        response = self.client.get('/admin/dynamic_choices/puppet/add/', follow=True)
        adminform = response.context['adminform']
        form = adminform.form
        enemies_inline = response.context['inline_admin_formsets'][0]
        fields = form.fields
        self.assertEqual(200, response.status_code, 'Cannot display add page')
        self.assertIsInstance(form, DynamicModelForm, 'Form is not an instance of DynamicModelForm')
        self.assertIsInstance(fields['master'], DynamicModelChoiceField,
                              'Field master is not an instance of DynamicChoicesField')
        self.assertIsInstance(fields['friends'], DynamicModelMultipleChoiceField,
                              'Field friends is not an instance of DynamicModelMultipleChoiceField')
        self.assertEmptyChoices(fields['master'], 'Since no alignment is defined master choices should be empty')
        self.assertEmptyChoices(fields['friends'], 'Since no alignment is defined friends choices should be empty')
        enemies_inline_form = enemies_inline.opts.form
        self.assertTrue(issubclass(enemies_inline_form, DynamicModelForm) or \
                        enemies_inline_form.__name__ == "Dynamic%s" % enemies_inline_form.__base__.__name__,
                        'Inline form is not a subclass of DynamicModelForm')
        for form in enemies_inline.formset.forms:
            fields = form.fields
            self.assertEmptyChoices(fields['enemy'], 'Since no alignment is defined enemy choices should be empty')
            self.assertEmptyChoices(fields['because_of'], 'Since no enemy is defined because_of choices should be empty')

    def test_GET_add_with_defined_alignment(self):
        alignment = ALIGNMENT_GOOD
        response = self.client.get('/admin/dynamic_choices/puppet/add/',
                                   {'alignment': alignment}, follow=True)
        self.assertEqual(200, response.status_code, 'Cannot display add page')
        adminform = response.context['adminform']
        form = adminform.form
        enemies_inline = response.context['inline_admin_formsets'][0]
        fields = form.fields
        self.assertIsInstance(form, DynamicModelForm, 'Form is not an instance of DynamicModelForm')
        self.assertIsInstance(fields['master'], DynamicModelChoiceField,
                              'Field master is not an instance of DynamicChoicesField')
        self.assertIsInstance(fields['friends'], DynamicModelMultipleChoiceField,
                              'Field friends is not an instance of DynamicModelMultipleChoiceField')
        self.assertChoices(Master.objects.filter(alignment=alignment), fields['master'],
                           "Since puppet alignment is 'Good' only 'Good' master are valid choices for master field")
        self.assertChoices(Puppet.objects.filter(alignment=alignment), fields['friends'],
                           "Since puppet alignment is 'Good' only 'Good' puppets are valid choices for friends field")
        enemies_inline_form = enemies_inline.opts.form
        self.assertTrue(issubclass(enemies_inline_form, DynamicModelForm) or \
                        enemies_inline_form.__name__ == "Dynamic%s" % enemies_inline_form.__base__.__name__,
                        'Inline form is not a subclass of DynamicModelForm')
        for form in enemies_inline.formset.forms:
            fields = form.fields
            self.assertChoices(Puppet.objects.exclude(alignment=alignment), fields['enemy'], 
                               "Since puppet alignment is 'Good' only not 'Good' puppets are valid choices for enemy field")
            self.assertEmptyChoices(fields['because_of'], 'Since no enemy is defined because_of choices should be empty')

    def test_POST_add(self):
        alignment = ALIGNMENT_GOOD
        data = {
            'alignment': alignment,
            'master': 1,
            'friends': [1],
            'enemy_set-TOTAL_FORMS': 3,
            'enemy_set-INITIAL_FORMS': 0
        }
        response = self.client.post('/admin/dynamic_choices/puppet/add/', data)
        self.assertEqual(302, response.status_code, 'Failed to validate')

    # Attempt to save an empty enemy inline
    # and make sure because_of has correct choices
    def test_POST_add_because_of(self):
        alignment = ALIGNMENT_GOOD
        data = {
            'alignment': alignment,
            'master': 1,
            'friends': [1],
            'enemy_set-TOTAL_FORMS': 3,
            'enemy_set-INITIAL_FORMS': 0,
            'enemy_set-0-enemy': 2
        }
        response = self.client.post('/admin/dynamic_choices/puppet/add/', data)
        self.assertNotEqual(302, response.status_code, 'Empty inline should not validate')
        self.assertChoices(Master.objects.filter(alignment=Puppet.objects.get(id=2).alignment),
                           response.context['inline_admin_formsets'][0].formset.forms[0].fields['because_of'],
                           'Since enemy is specified because_of choices must have the same alignment')
        self.assertEmptyChoices(response.context['inline_admin_formsets'][0].formset.forms[1].fields['because_of'],
                                'Enemy is only specified for the first inline, second one because_of should be empty')

    #TODO: Add test_(GET & POST)_edit testcases

    def test_user_defined_forms(self):
        self.assertTrue(issubclass(PuppetAdmin.form, DynamicModelForm),
                        'User defined forms should be subclassed from DynamicModelForm by metaclass')
        self.assertTrue(issubclass(PuppetAdmin.inlines[0].form, DynamicModelForm),
                        'User defined inline forms should be subclassed from DynamicModelForm by dynamic_inline_factory')


class AdminChoicesTest(AdminTest):
    def _get_choices(self, data=None):
        default = {
            'enemy_set-TOTAL_FORMS': 0,
            'enemy_set-INITIAL_FORMS': 0,
        }
        if data:
            default.update(data)
        return self.client.get('/admin/dynamic_choices/puppet/1/choices/',
                               default)

    def test_medias_presence(self):
        """Make sure extra js files are present in the response"""
        response = self.client.get('/admin/dynamic_choices/puppet/1/')
        self.assertIn('js/dynamic-choices.js', response.content)
        self.assertIn('js/dynamic-choices-admin.js', response.content)

    def test_fk_as_empty_string(self):
        """Make sure fk specified as empty string are parsed correctly"""
        data = {'alignment': ''}
        response = self._get_choices(data)
        self.assertEquals(200, response.status_code,
                          'Empty string fk shouldn\'t be cast as int')

    def test_empty_string_value_overrides_default(self):
        """Make sure specified empty string overrides instance field"""
        data = {
            'DYNAMIC_CHOICES_FIELDS': 'enemy_set-0-because_of',
            'enemy_set-0-id': 1,
            'enemy_set-0-enemy': '',
            'enemy_set-TOTAL_FORMS': 3,
            'enemy_set-INITIAL_FORMS': 1
        }
        response = self._get_choices(data)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['enemy_set-0-because_of']['value'],
                         [['', '---------']])

    def test_empty_form(self):
        """Make sure data is provided for an empty form"""
        data = {
            'DYNAMIC_CHOICES_FIELDS': 'enemy_set-__prefix__-enemy',
            'alignment': 1
        }
        response = self._get_choices(data)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['enemy_set-__prefix__-enemy']['value'],
                         [
                           ['', '---------'],
                           ['Evil', [[2, 'Evil puppet (2)'],]],
                           ['Neutral', []],
                          ])


class DefinitionValidationTest(TestCase):
    def test_method_definition(self):
        with self.assertRaises(FieldError):
            class MissingChoicesCallbackModel(Model):
                field = DynamicChoicesForeignKey('self',
                                                 choices='missing_method')
        try:
            class CallableChoicesCallbackModel(Model):
                field = DynamicChoicesForeignKey('self', choices=lambda qs: qs)
        except FieldError:
            self.fail('Defining a callable choices should work')
