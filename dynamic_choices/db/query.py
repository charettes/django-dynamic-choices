from itertools import chain

from django.db.models.query import EmptyQuerySet, QuerySet


class CompositeQuerySet(object):
    """
    A queryset like object composed of multiple querysets
    """
    
    def __init__(self, querysets):
        self._querysets = tuple(querysets)
        self.model = self.querysets[0].model
        assert all(qs.model == self.model for qs in self.querysets[1:]), \
            'All querysets must be of the same model'
    
    @property
    def querysets(self):
        return self._querysets
    
    def __iter__(self):
        return chain(*self.querysets)
    
    def get(self, *args, **kwargs):
        for qs in self.querysets:
            try:
                obj = qs.get(*args, **kwargs)
            except self.model.DoesNotExist:
                pass
            else:
                return obj
        raise self.model.DoesNotExist
    
    def _compose(self, method, *args, **kwargs):
        return self.__class__(getattr(qs, method)(*args, **kwargs)
                                for qs in self.querysets)
    
    def filter(self, *args, **kwargs):
        return self._compose('filter', *args, **kwargs)
    
    def distinct(self):
        return self._compose('distinct')
    
    def exists(self):
        return any(qs.exists() for qs in self.querysets)

class EmptyDynamicChoicesQuerySet(EmptyQuerySet):
    
    def filter_for_instance(self):
        return self

class DynamicChoicesQuerySet(QuerySet):
    
    def _clone(self, *args, **kwargs):
        clone = super(DynamicChoicesQuerySet, self)._clone(*args, **kwargs)
        clone._field = self._field
        return clone
        
    def filter_for_instance(self, instance, data):
        return self._field._invoke_choices_callback(instance, self, data)
    
    def none(self):
        return self._clone(klass=EmptyDynamicChoicesQuerySet)

def dynamic_queryset_factory(queryset, field):
    
    clone = queryset._clone(DynamicChoicesQuerySet)
    clone._field = field
    
    return clone
