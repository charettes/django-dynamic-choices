import operator

from django.db.models.query import EmptyQuerySet, QuerySet


class EmptyDynamicChoicesQueryset(EmptyQuerySet):
    
    def filter_for_instance(self):
        return self

class DynamicChoicesQueryset(QuerySet):
    
    def _clone(self, *args, **kwargs):
        clone = super(DynamicChoicesQueryset, self)._clone(*args, **kwargs)
        clone._field = self._field
        return clone
        
    def filter_for_instance(self, instance, data):
        return self._field._invoke_choices_callback(instance, self, data)
    
    def none(self):
        return self._clone(klass=EmptyDynamicChoicesQueryset)

def dynamic_queryset_factory(queryset, field):
    
    clone = queryset._clone(DynamicChoicesQueryset)
    clone._field = field
    
    return clone

def unionize_querysets(querysets):
    """
    Combine querysets in a way that results
    from every queryset in joined together
    """
    return reduce(operator.or_, querysets)
