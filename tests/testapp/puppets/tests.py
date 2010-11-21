from django.core.exceptions import ValidationError
from django.db.models.query import EmptyQuerySet
from django.test import TestCase
from django.test.client import Client

from dynamic_choices.forms import DynamicModelForm
from dynamic_choices.forms.fields import DynamicModelMultipleChoiceField,\
    DynamicModelChoiceField

from models import Master, Puppet, ALIGNMENT_EVIL, ALIGNMENT_GOOD

class DynamicForeignKeyTest(TestCase):
    
    def setUp(self):
        self.good_master = Master.objects.get(alignment=ALIGNMENT_GOOD)
        
    def test_valid_value(self):
        puppet = Puppet(master=self.good_master, alignment=ALIGNMENT_GOOD)
        puppet.full_clean()
        
    def test_invalid_value(self):
        puppet = Puppet(master=self.good_master, alignment=ALIGNMENT_EVIL)
        self.failUnlessRaises(ValidationError, puppet.full_clean)
        
class DynamicAdminTest(TestCase):
    
    fixtures = ['dynamic_admin_test']
    
    def setUp(self):
        self.client = Client()
        self.client.login(username='superuser', password='sudo')
    
    def assertChoices(self, queryset, field, msg=None):
        self.assertEqual(list(queryset), list(field.widget.choices.queryset), msg)
            
    def assertEmptyChoices(self, field, msg=None):
        return self.assertChoices(EmptyQuerySet(), field, msg=msg)
    
    def test_GET_add(self):
        response = self.client.get('/admin/puppets/puppet/add/', follow=True)
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
        response = self.client.get('/admin/puppets/puppet/add/', {'alignment': alignment}, follow=True)
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
        response = self.client.post('/admin/puppets/puppet/add/', {
                                                                   'alignment': alignment,
                                                                   'master': 1,
                                                                   'friends': [1],
                                                                   'enemy_set-TOTAL_FORMS': 3,
                                                                   'enemy_set-INITIAL_FORMS': 0
                                                                   })
        
        self.assertEqual(302, response.status_code, 'Failed to validate')
    
    # Attempt to save an empty enemy inline
    # and make sure because_of has correct choices
    def test_POST_add_because_of(self):
        alignment = ALIGNMENT_GOOD
        response = self.client.post('/admin/puppets/puppet/add/', {
                                                                   'alignment': alignment,
                                                                   'master': 1,
                                                                   'friends': [1],
                                                                   'enemy_set-TOTAL_FORMS': 3,
                                                                   'enemy_set-INITIAL_FORMS': 0,
                                                                   'enemy_set-0-enemy': 2
                                                                   })
        
        self.assertNotEqual(302, response.status_code, 'Empty inline should not validate')
        self.assertChoices(Master.objects.filter(alignment=Puppet.objects.get(id=2).alignment),
                           response.context['inline_admin_formsets'][0].formset.forms[0].fields['because_of'],
                           'Since enemy is specified because_of choices must have the same alignment')
        self.assertEmptyChoices(response.context['inline_admin_formsets'][0].formset.forms[1].fields['because_of'],
                                'Enemy is only specified for the first inline, second one because_of should be empty')
        
    #TODO: Add test_(GET & POST)_edit testcases
        