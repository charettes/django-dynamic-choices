from __future__ import unicode_literals

from django.db.models.query import QuerySet
from django.forms.fields import ChoiceField
from django.forms.models import (
    ModelChoiceField, ModelChoiceIterator, ModelMultipleChoiceField,
)

from ..db.query import CompositeQuerySet, DynamicChoicesQuerySet


class GroupedModelChoiceIterator(ModelChoiceIterator):

    def __init__(self, field):
        super(GroupedModelChoiceIterator, self).__init__(field)
        self.groups = field._groups

    def __iter__(self):
        if self.field.empty_label is not None:
            yield ("", self.field.empty_label)

        for label, queryset in self.groups:
            yield (label, [self.choice(obj) for obj in queryset])

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
        if self._instance and isinstance(queryset, DynamicChoicesQuerySet):
            queryset = queryset.filter_for_instance(self._instance, self._data)
            if not isinstance(queryset, QuerySet):
                self._groups = queryset
                queryset = CompositeQuerySet(q[1] for q in queryset)
        self._queryset = queryset
        self.widget.choices = self.choices

    queryset = property(_get_queryset, _set_queryset)

    def set_choice_data(self, instance, data):
        self._instance = instance
        self._data = data
        self.queryset = self._original_queryset

    def _get_choices(self):
        if self._groups is None:
            return super(DynamicModelChoiceField, self)._get_choices()
        return GroupedModelChoiceIterator(self)

    choices = property(_get_choices, ChoiceField._set_choices)


class DynamicModelMultipleChoiceField(DynamicModelChoiceField, ModelMultipleChoiceField):
    pass
