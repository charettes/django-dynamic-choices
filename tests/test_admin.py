from __future__ import unicode_literals

import json
import os

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase
from django.test.client import Client
from django.test.utils import override_settings
from django.utils.encoding import force_text

from dynamic_choices.admin import DynamicAdmin
from dynamic_choices.forms import DynamicModelForm
from dynamic_choices.forms.fields import (
    DynamicModelChoiceField, DynamicModelMultipleChoiceField,
)

from .admin import PuppetAdmin
from .models import ALIGNMENT_GOOD, Master, Puppet

MODULE_PATH = os.path.abspath(os.path.dirname(__file__))


@override_settings(
    TEMPLATE_LOADERS=[
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ],
    TEMPLATE_DIRS=[os.path.join(MODULE_PATH, 'templates')],
)
class ChangeFormTemplateTests(SimpleTestCase):
    template_attr = 'change_form_template'

    def test_doesnt_extend_change_form(self):
        expected_message = (
            "Make sure DoesntExtend.%s template extends "
            "'admin/dynamic_choices/change_form.html' in order to enable DynamicAdmin"
        ) % self.template_attr
        with self.assertRaisesMessage(ImproperlyConfigured, expected_message):
            type(str('DoesntExtend'), (DynamicAdmin,), {
                self.template_attr: 'dynamic_choices_tests/do_not_extends_change_form.html'
            })

    def test_extends_directly(self):
        type(str('ExtendsDirectly'), (DynamicAdmin,), {
            self.template_attr: 'dynamic_choices_tests/extends_change_form.html'
        })

    def test_extends_change_from_through_child(self):
        type(str('ExtendsThroughChild'), (DynamicAdmin,), {
            self.template_attr: 'dynamic_choices_tests/extends_change_form_twice.html'
        })


class AddFormTemplateTests(ChangeFormTemplateTests):
    template_attr = 'add_form_template'


class AdminTestBase(TestCase):
    fixtures = ['dynamic_choices_test_data', 'dynamic_choices_admin_test_data']

    def setUp(self):
        self.client = Client()
        self.client.login(username='superuser', password='sudo')


class DynamicAdminFormTests(AdminTestBase):

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
        self.assertTrue(issubclass(enemies_inline_form, DynamicModelForm) or
                        enemies_inline_form.__name__ == "Dynamic%s" % enemies_inline_form.__base__.__name__,
                        'Inline form is not a subclass of DynamicModelForm')
        for form in enemies_inline.formset.forms:
            fields = form.fields
            self.assertEmptyChoices(fields['enemy'], 'Since no alignment is defined enemy choices should be empty')
            self.assertEmptyChoices(
                fields['because_of'], 'Since no enemy is defined because_of choices should be empty')

    def test_GET_add_with_defined_alignment(self):
        alignment = ALIGNMENT_GOOD
        response = self.client.get('/admin/dynamic_choices/puppet/add/', {'alignment': alignment}, follow=True)
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
        self.assertTrue(issubclass(enemies_inline_form, DynamicModelForm) or
                        enemies_inline_form.__name__ == "Dynamic%s" % enemies_inline_form.__base__.__name__,
                        'Inline form is not a subclass of DynamicModelForm')
        for form in enemies_inline.formset.forms:
            fields = form.fields
            self.assertChoices(
                Puppet.objects.exclude(alignment=alignment), fields['enemy'],
                "Since puppet alignment is 'Good' only not 'Good' puppets are valid choices for enemy field"
            )
            self.assertEmptyChoices(
                fields['because_of'], 'Since no enemy is defined because_of choices should be empty')

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

    # TODO: Add test_(GET & POST)_edit testcases

    def test_user_defined_forms(self):
        self.assertTrue(issubclass(PuppetAdmin.form, DynamicModelForm),
                        'User defined forms should be subclassed from DynamicModelForm by metaclass')
        self.assertTrue(
            issubclass(PuppetAdmin.inlines[0].form, DynamicModelForm),
            'User defined inline forms should be subclassed from DynamicModelForm by dynamic_inline_factory'
        )


class AdminChoicesTests(AdminTestBase):

    def _get_choices(self, data=None):
        default = {
            'enemy_set-TOTAL_FORMS': 0,
            'enemy_set-INITIAL_FORMS': 0,
        }
        if data:
            default.update(data)
        return self.client.get('/admin/dynamic_choices/puppet/1/choices/', default)

    def test_medias_presence(self):
        """Make sure extra js files are present in the response"""
        response = self.client.get('/admin/dynamic_choices/puppet/1/')
        self.assertContains(response, 'js/dynamic-choices.js')
        self.assertContains(response, 'js/dynamic-choices-admin.js')

    def test_fk_as_empty_string(self):
        """Make sure fk specified as empty string are parsed correctly"""
        data = {'alignment': ''}
        response = self._get_choices(data)
        self.assertEqual(200, response.status_code, "Empty string fk shouldn't be cast as int")

    def test_empty_string_value_overrides_default(self):
        """Make sure specified empty string overrides instance field"""
        data = {
            'DYNAMIC_CHOICES_FIELDS': 'enemy_set-0-because_of',
            'enemy_set-0-id': 1,
            'enemy_set-0-enemy': '',
            'enemy_set-TOTAL_FORMS': 3,
            'enemy_set-INITIAL_FORMS': 1,
        }
        response = self._get_choices(data)
        self.assertEqual(response.status_code, 200)
        data = json.loads(force_text(response.content))
        self.assertEqual(data['enemy_set-0-because_of']['value'], [['', '---------']])

    def test_empty_form(self):
        """Make sure data is provided for an empty form"""
        data = {
            'DYNAMIC_CHOICES_FIELDS': 'enemy_set-__prefix__-enemy',
            'alignment': 1,
        }
        response = self._get_choices(data)
        self.assertEqual(response.status_code, 200)
        data = json.loads(force_text(response.content))
        self.assertEqual(data['enemy_set-__prefix__-enemy']['value'], [
            ['', '---------'],
            ['Evil', [[2, 'Evil puppet (2)'], ]],
            ['Neutral', []],
        ])
