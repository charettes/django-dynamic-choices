from django.forms.models import ModelForm
from dynamic_admin.forms.fields import DynamicModelChoiceField,\
    DynamicModelMultipleChoiceField
from django.db.models.fields.related import ManyToManyField

def dynamic_model_form_factory(model_form_cls):
    class cls(model_form_cls):
        def __init__(self, *args, **kwargs):
            super(cls, self).__init__(*args, **kwargs)
            
            # Fetch initial data for initial
            data = self.initial.copy()
            
            # Update data if it's avaible
            for field in self.fields.iterkeys():
                raw_value = self._raw_value(field)
                if raw_value:
                    data[field] = raw_value
    
            # Bind instances to dynamic fields
            for field in self.fields.itervalues():
                if isinstance(field, DynamicModelChoiceField):
                    field.set_choice_data(self.instance, data)
    cls.__name__ = "Dynamic%s" % model_form_cls.__name__
    return cls

DynamicModelForm = dynamic_model_form_factory(ModelForm)
                