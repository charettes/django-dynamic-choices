
from django.forms.fields import ChoiceField
from django.forms.models import (ModelChoiceField, ModelChoiceIterator,
    ModelMultipleChoiceField)
    
from dynamic_choices.db.query import DynamicChoicesQueryset, unionize_querysets

class GroupedModelChoiceIterator(ModelChoiceIterator):
    def __init__(self, field):
        super(GroupedModelChoiceIterator, self).__init__(field)
        self.groups = field._groups
    
    def __iter__(self):
        if self.field.empty_label is not None:
            yield (u"", self.field.empty_label)
            
        #TODO: consider field.cache_choices
        
        for group in self.groups:
            label, qs = group
            yield (label, [self.choice(obj) for obj in qs])

    def __len__(self):
        return sum(len(group[1]) for group in self.groups)

class DynamicModelChoiceField(ModelChoiceField):
    
    def __init__(self, *args, **kwargs):
        self._instance = None
        self._data = {}
        self._groups = None
        super(DynamicModelChoiceField, self).__init__(*args, **kwargs)

    def _get_queryset(self):
        return self._queryset.distinct()

    def _set_queryset(self, queryset):
        self._original_queryset = queryset
        self._groups = None
        if self._instance and isinstance(queryset, DynamicChoicesQueryset):
            queryset = queryset.filter_for_instance(self._instance, self._data)
            if isinstance(queryset, tuple):
                self._groups = queryset
                queryset = unionize_querysets(q[1] for q in queryset)
        self._queryset = queryset
        self.widget.choices = self.choices

    queryset = property(_get_queryset, _set_queryset)
    
    def set_choice_data(self, instance, data):
        self._instance = instance
        self._data = data
        self.queryset = self._original_queryset
        
    def _get_choices(self):
        if isinstance(self._groups, tuple):
            return GroupedModelChoiceIterator(self)
        else:
            return super(DynamicModelChoiceField, self)._get_choices()

    choices = property(_get_choices, ChoiceField._set_choices)

class DynamicModelMultipleChoiceField(DynamicModelChoiceField, ModelMultipleChoiceField):
    pass
