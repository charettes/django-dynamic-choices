from django.db.models.query import QuerySet

class DynamicChoicesQueryset(QuerySet):
        
    def filter_for_instance(self, instance, data):
        return self._field._invoke_choices_callback(instance, self, data)

def dynamic_queryset_factory(queryset, field):
    
    clone = queryset._clone(DynamicChoicesQueryset)
    clone._field = field
    
    return clone