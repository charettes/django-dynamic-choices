from __future__ import unicode_literals

from django.core.exceptions import FieldError, ValidationError
from django.db.models import Model
from django.test import SimpleTestCase, TestCase

from dynamic_choices.db.models import DynamicChoicesForeignKey

from .models import ALIGNMENT_EVIL, ALIGNMENT_GOOD, Enemy, Master, Puppet


class DefinitionValidationTest(SimpleTestCase):
    def test_missing_method(self):
        with self.assertRaises(FieldError):
            class MissingChoicesCallbackModel(Model):
                field = DynamicChoicesForeignKey('self', choices='missing_method')

                class Meta:
                    app_label = 'dynamic_choices'

    def test_callable(self):
        class CallableChoicesCallbackModel(Model):
            field = DynamicChoicesForeignKey('self', choices=lambda qs: qs)

            class Meta:
                app_label = 'dynamic_choices'


class DynamicForeignKeyTests(TestCase):
    def setUp(self):
        self.good_master = Master.objects.create(alignment=ALIGNMENT_GOOD)
        self.evil_master = Master.objects.create(alignment=ALIGNMENT_EVIL)

    def test_valid_value(self):
        good_puppet = Puppet(master=self.good_master, alignment=ALIGNMENT_GOOD)
        good_puppet.full_clean()
        good_puppet.save()
        evil_puppet = Puppet(master=self.evil_master, alignment=ALIGNMENT_EVIL)
        evil_puppet.full_clean()
        evil_puppet.save()
        enemy = Enemy(puppet=evil_puppet, enemy=good_puppet, because_of=self.good_master)
        enemy.full_clean(exclude=['since'])

    def test_invalid_value(self):
        puppet = Puppet(master=self.good_master, alignment=ALIGNMENT_EVIL)
        self.assertRaises(ValidationError, puppet.full_clean)


class DynamicOneToOneFieldTests(TestCase):
    fixtures = ['dynamic_choices_test_data']

    def setUp(self):
        self.good_puppet = Puppet.objects.get(alignment=ALIGNMENT_GOOD)
        self.evil_puppet = Puppet.objects.get(alignment=ALIGNMENT_EVIL)

    def test_valid_value(self):
        self.evil_puppet.secret_lover = self.good_puppet
        self.evil_puppet.full_clean()
        self.evil_puppet.save()
        self.assertEqual(self.good_puppet.secretly_loves_me, self.evil_puppet)
        self.good_puppet.secret_lover = self.evil_puppet
        self.good_puppet.full_clean()

    def test_invalid_value(self):
        self.evil_puppet.secret_lover = self.good_puppet
        self.evil_puppet.save()
        self.good_puppet.secret_lover = self.good_puppet
        self.assertRaises(
            ValidationError, self.good_puppet.full_clean,
            "Since the evil puppet secretly loves the good puppet the good puppet can only secretly love the bad one."
        )
