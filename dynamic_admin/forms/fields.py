from django.forms.models import ModelChoiceField, ModelMultipleChoiceField
from dynamic_admin.db.query import DynamicChoicesQueryset

class DynamicModelChoiceField(ModelChoiceField):
    
    def __init__(self, *args, **kwargs):
        self._instance = None
        self._data = {}
        super(DynamicModelChoiceField, self).__init__(*args, **kwargs)

    def _get_queryset(self):
        return self._queryset

    def _set_queryset(self, queryset):
        self._original_queryset = queryset
        if self._instance and isinstance(queryset, DynamicChoicesQueryset):
            self._queryset = queryset.filter_for_instance(self._instance, self._data)
        else:
            self._queryset = queryset
        self.widget.choices = self.choices

    queryset = property(_get_queryset, _set_queryset)
    
    def set_choice_data(self, instance, data):
        self._instance = instance
        self._data = data
        self.queryset = self._original_queryset

class DynamicModelMultipleChoiceField(DynamicModelChoiceField, ModelMultipleChoiceField):
    pass
