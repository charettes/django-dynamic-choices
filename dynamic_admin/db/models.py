import inspect

from django.db.models import ForeignKey, ManyToManyField
from django.core import exceptions
from dynamic_admin.db.query import dynamic_queryset_factory
from django.forms.models import model_to_dict
from django.db.models.base import Model
from django.db.models.fields import FieldDoesNotExist, Field
from django.core.management.validation import ModelErrorCollection
from django.db.models.sql.constants import LOOKUP_SEP
from django.core.exceptions import FieldError

from dynamic_admin.forms.fields import DynamicModelChoiceField,\
    DynamicModelMultipleChoiceField

class DynamicChoicesField(object):
    
    def __init__(self, *args, **kwargs):
        super(DynamicChoicesField, self).__init__(*args, **kwargs)
        # Hack to bypass non iterable choices validation
        if isinstance(self._choices, basestring) or callable(self._choices):
            self._choices_callback = self._choices
            self._choices = []
        else:
            self._choices_callback = None
        self._validated_definition = False
    
    def _has_choices_callback(self):
        return callable(self._choices_callback)
    has_choices_callback = property(_has_choices_callback)
    
    def _invoke_choices_callback(self, model_instance, qs, data):
        if not self._validated_definition:
            self.validate_definition()
        
        args = [qs]
        # Make sure we pass the instance if the callback is a class method
        if inspect.ismethod(self._choices_callback):
            args.insert(0, model_instance)
        
        values = {}
        for descriptor, fields in self._choices_callback_field_descriptors.items():
            depth = len(fields)
            step = 1
            lookup_data = data
            value = None
            
            # Direct lookup
            # foo__bar in data
            if descriptor in data:
                value = data[descriptor]
                step = depth
                field = fields[-1]
            else:
                for field in fields:
                    # Field name lookup
                    # foo
                    if field.name in lookup_data:
                        value = lookup_data[field.name]
                        if step != depth:
                            if isinstance(field, ManyToManyField):
                                # We cannot lookup in m2m, it must be the final step
                                break
                            elif isinstance(value, list):
                                value = value[0] # Make sure we've got a scalar
                            if isinstance(field, ForeignKey):
                                if not isinstance(value, Model):
                                    try:
                                        value = field.rel.to.objects.get(pk=value)
                                    except Exception:
                                        # Invalid object
                                        break
                                lookup_data = model_to_dict(value)
                            step += 1
                    else:
                        break
            
            # We reached descriptors depth
            if step == depth:
                if isinstance(value, list) and \
                    not isinstance(field, ManyToManyField):
                    value = value[0] # Make sure we've got a scalar if its not a m2m
                values[descriptor] = value
        
        return self._choices_callback(*args, **values)
    
    # This method should only be called once, on get_validation_errors.
    # Since there's no way to provide errors to that method it's called on first
    # _invoke_choices_callback call.
    def validate_definition(self):
        # Mark this method as called
        self._validated_definition = True
        
        if self.has_choices_callback:
            def error(message):
                raise FieldError("%s: %s: %s" % (self.related.model._meta, self.name, message))
            
            self._choices_callback_field_descriptors = {}
            spec = inspect.getargspec(self._choices_callback)
            
            # We make sure field descriptors are valid
            for descriptor in spec.args[-len(spec.defaults):]:
                lookups = descriptor.split(LOOKUP_SEP)
                meta = self.related.model._meta
                depth = len(lookups)
                step = 1
                fields = []
                for lookup in lookups:
                    try:
                        field = meta.get_field(lookup)
                        # The field is a foreign key to another model
                        if isinstance(field, ForeignKey):
                            meta = field.rel.to._meta
                            step += 1
                        # We cannot go deeper if it's not a model
                        elif step != depth:
                            error('Invalid descriptor "%s", "%s" is not a ForeignKey to a model' % (
                                   LOOKUP_SEP.join(lookups), LOOKUP_SEP.join(lookups[:step])))
                        fields.append(field)
                    except FieldDoesNotExist:
                        # Lookup failed, suggest alternatives
                        depth_descriptor = LOOKUP_SEP.join(descriptor[:step - 1])
                        if depth_descriptor:
                            depth_descriptor += LOOKUP_SEP
                        choice_descriptors = [(depth_descriptor + name) for name in meta.get_all_field_names()]
                        error('Invalid descriptor "%s", choices are %s' % (
                              LOOKUP_SEP.join(descriptor), ', '.join(choice_descriptors)))
                
                self._choices_callback_field_descriptors[descriptor] = fields
    
    def contribute_to_class(self, cls, name):
        super(DynamicChoicesField, self).contribute_to_class(cls, name)
        
        if self._choices_callback:
            # Since there's no way of providing custom  model field validation
            # we attempt to mimic manage.py validate behavior
            error_collection = ModelErrorCollection()
            def error(message):
                error_collection.add(cls._meta, '"%s": %s' % (name, message))
            
            # The choices we're defined by a string
            # therefore it should be a cls method
            if isinstance(self._choices_callback, basestring):
                callback = getattr(cls, self._choices_callback, None)
                if not callable(callback):
                    error('Cannot find "%s.%s" method specified by choices.' % (cls.__name__, self._choices_callback))
                    return
                args_length = 2 # Since the callback is a method we must emulate the 'self'
                self._choices_callback = callback
            else:
                args_length = 1 # It's a callable, it needs no reference to model instance
            
            spec = inspect.getargspec(self._choices_callback)
            
            # Make sure the callback has the correct number or arg
            if (len(spec.args) - len(spec.defaults)) != args_length:
                error('Specified choices callback must accept only a single arg')
                return

    def __super(self):
        # Dirty hack to allow both DynamicChoicesForeignKey and DynamicChoicesManyToManyField
        # to inherit this behavior with multiple inheritance
        for base in self.__class__.__bases__:
            if issubclass(base, Field):
                self.__super = lambda : base #cache
                return base
        raise Exception('Subclasses must inherit from atleast one subclass of django.db.fields.Field')

    def formfield(self, **kwargs):
        if self.has_choices_callback:
            db = kwargs.pop('using', None)
            qs = self.rel.to._default_manager.using(db).complex_filter(self.rel.limit_choices_to)
            defaults = {
                'using': db,
                'form_class': self.form_class,
                'queryset': dynamic_queryset_factory(qs, self)
            }
        else:
            defaults = kwargs
            
        return self.__super().formfield(self, **defaults)

class DynamicChoicesForeignKey(DynamicChoicesField, ForeignKey):

    form_class = DynamicModelChoiceField

    def validate(self, value, model_instance):
        if self.has_choices_callback:
            if self.rel.parent_link:
                return
            if value is None:
                return
            
            data = model_to_dict(model_instance)
            for field in model_instance._meta.fields:
                try:
                    data[field.name] = getattr(model_instance, field.name)
                except field.rel.to.DoesNotExist:
                    pass
            if model_instance.id:
                for m2m in model_instance._meta.many_to_many:
                    data[m2m.name] = getattr(model_instance, m2m.name).all()
            
            qs = self.rel.to._default_manager.filter(**{self.rel.field_name:value})
            qs = qs.complex_filter(self.rel.limit_choices_to)
            qs = self._invoke_choices_callback(model_instance, qs, data)
            if not qs.exists():
                raise exceptions.ValidationError(self.error_messages['invalid'] % {
                    'model': self.rel.to._meta.verbose_name, 'pk': value})
        else:
            super(DynamicChoicesForeignKey, self).validate(value, model_instance)
            
class DynamicChoicesManyToManyField(DynamicChoicesField, ManyToManyField):
    
    form_class = DynamicModelMultipleChoiceField
    