import inspect

from django.core import exceptions
from django.core.exceptions import FieldError
from django.db.models import ForeignKey, ManyToManyField, OneToOneField
from django.db.models.base import Model
from django.db.models.fields import FieldDoesNotExist, Field
from django.db.models.fields.related import add_lazy_relation
from django.db.models.sql.constants import LOOKUP_SEP
from django.db.models.signals import class_prepared
from django.forms.models import model_to_dict

from dynamic_choices.db.query import dynamic_queryset_factory, unionize_querysets
from dynamic_choices.forms.fields import (DynamicModelChoiceField,
    DynamicModelMultipleChoiceField)

class DynamicChoicesField(object):
    
    def __init__(self, *args, **kwargs):
        super(DynamicChoicesField, self).__init__(*args, **kwargs)
        # Hack to bypass non iterable choices validation
        if isinstance(self._choices, basestring) or callable(self._choices):
            self._choices_callback = self._choices
            self._choices = []
        else:
            self._choices_callback = None
        self._choices_relationships = None
    
    def contribute_to_class(self, cls, name):
        super(DynamicChoicesField, self).contribute_to_class(cls, name)
        
        if self._choices_callback is not None:
            class_prepared.connect(self.__validate_definition,
                                   sender=cls)
    
    def __validate_definition(self, *args, **kwargs):
        def error(message):
            raise FieldError("%s: %s: %s" % (self.related.model._meta, self.name, message))

        original_choices_callback = self._choices_callback

        # The choices we're defined by a string
        # therefore it should be a cls method
        if isinstance(self._choices_callback, basestring):
            callback = getattr(self.related.model, self._choices_callback, None)
            if not callable(callback):
                error('Cannot find method specified by choices.')
            args_length = 2 # Since the callback is a method we must emulate the 'self'
            self._choices_callback = callback
        else:
            args_length = 1 # It's a callable, it needs no reference to model instance
        
        spec = inspect.getargspec(self._choices_callback)
        
        # Make sure the callback has the correct number or arg
        if spec.defaults is not None:
            spec_defaults_len = len(spec.defaults)
            args_length += spec_defaults_len
            self._choices_relationships = spec.args[-spec_defaults_len:]
        else:
            self._choices_relationships = []
        
        if len(spec.args) != args_length:
            error('Specified choices callback must accept only a single arg')
        
        self._choices_callback_field_descriptors = {}
        
        # We make sure field descriptors are valid
        for descriptor in self._choices_relationships:
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
                        try:
                            meta = field.rel.to._meta
                        except AttributeError:
                            # The model hasn't been loaded yet
                            # so we must stop here and start over
                            # when it is loaded.
                            if isinstance(field.rel.to, basestring):
                                self._choices_callback = original_choices_callback
                                return add_lazy_relation(field.model, field,
                                                         field.rel.to,
                                                         self.__validate_definition)
                            else:
                                raise
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
    
    @property
    def has_choices_callback(self):
        return callable(self._choices_callback)
    
    @property
    def choices_relationships(self):
        return self._choices_relationships
    
    def _invoke_choices_callback(self, model_instance, qs, data):
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
                # We're going to try to lookup every step of the descriptor.
                # We first try field1, then field1__field2, etc..
                # When there's a match we start over with fieldmatch and set the lookup data
                # to the matched value.
                field_name = "%s"
                for field in fields:
                    field_name = field_name % field.name
                    if field_name in lookup_data:
                        value = lookup_data[field_name]
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
                                field_name = "%s"
                            step += 1
                    elif step != depth:
                        field_name = "%s%s%s" % (field_name, LOOKUP_SEP, '%s')
            
            # We reached descriptors depth
            if step == depth:
                if isinstance(value, list) and \
                    not isinstance(field, ManyToManyField):
                    value = value[0] # Make sure we've got a scalar if its not a m2m
                # Attempt to cast value, if failed we don't assign since it's invalid
                try:
                    values[descriptor] = field.to_python(value)
                except:
                    pass
        
        return self._choices_callback(*args, **values)

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
            defaults.update(kwargs)
        else:
            defaults = kwargs
            
        return self.__super().formfield(self, **defaults)

class DynamicChoicesForeignKeyMixin(DynamicChoicesField):
    
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
            
            dcqs = self._invoke_choices_callback(model_instance, qs, data)
            # If a tuple is provided we must build
            # a new Queryset by combining group's ones
            if isinstance(dcqs, tuple):
                qs = qs and unionize_querysets(q[1] for q in dcqs)
            else:
                qs = dcqs
            
            if not qs.exists():
                raise exceptions.ValidationError(self.error_messages['invalid'] % {
                    'model': self.rel.to._meta.verbose_name, 'pk': value})
        else:
            super(DynamicChoicesForeignKey, self).validate(value, model_instance)

class DynamicChoicesForeignKey(DynamicChoicesForeignKeyMixin, ForeignKey):

    form_class = DynamicModelChoiceField

class DynamicChoicesOneToOneField(DynamicChoicesForeignKeyMixin, OneToOneField):
    
    form_class = DynamicModelChoiceField

class DynamicChoicesManyToManyField(DynamicChoicesField, ManyToManyField):
    
    form_class = DynamicModelMultipleChoiceField
    
try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ['^dynamic_choices\.db\.models'])
except ImportError:
    pass
    