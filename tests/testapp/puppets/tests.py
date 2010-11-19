from django.test import TestCase
from models import Master, Puppet, ALIGNMENT_EVIL, ALIGNMENT_GOOD
from django.core.exceptions import ValidationError

class DynamicForeignKeyTest(TestCase):
    
    def setUp(self):
        self.good_master = Master.objects.get(alignment=ALIGNMENT_GOOD)
        
    def test_valid_value(self):
        puppet = Puppet(master=self.good_master, alignment=ALIGNMENT_GOOD)
        puppet.full_clean()
        
    def test_invalid_value(self):
        puppet = Puppet(master=self.good_master, alignment=ALIGNMENT_EVIL)
        self.failUnlessRaises(ValidationError, puppet.full_clean)
