from django.db import models
from django.contrib import admin
from django.forms.models import _get_foreign_key, model_to_dict
from django.forms.widgets import MediaDefiningClass
from django.utils.functional import update_wrapper
from django.contrib.admin.util import unquote
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponseBadRequest, HttpResponse
from django.template.defaultfilters import escape
from django.utils import simplejson
from django.utils.encoding import force_unicode

from ..forms import DynamicModelForm, dynamic_model_form_factory
from ..forms.fields import DynamicModelChoiceField

def dynamic_fieldset_factory(fieldset_cls, initial):
    class cls(fieldset_cls):
        def _construct_forms(self):
            "Append initial data for every single form"
            store = getattr(self, 'initial', None)
            if store is None:
                store = []
                setattr(self, 'initial', store)
            for i in xrange(self.total_form_count()):
                try:
                    actual = store[i]
                    actual.update(initial)
                except (ValueError, IndexError):
                    store.insert(i, initial)
            return super(cls, self)._construct_forms()
    cls.__name__ = "Dynamic%s" % fieldset_cls.__name__
    return cls

def dynamic_inline_factory(inline_cls):
    "Make sure the inline has a dynamic form"
    form_cls = getattr(inline_cls, 'form', None)
    if form_cls is None:
        form_cls = DynamicModelForm
    elif issubclass(form_cls, DynamicModelForm):
        return inline_cls
    else:
        form_cls = dynamic_model_form_factory(form_cls)
    
    class cls(inline_cls):
        form = form_cls
    cls.__name__ = "Dynamic%s" % inline_cls
    return cls

class DynamicAdminBase(MediaDefiningClass):
    "Metaclass that ensure form and inlines are dynamic"
    def __new__(cls, name, bases, attrs):
        # If there's already a form defined we make sure to subclass it
        if 'form' in attrs:
            attrs['form'] = dynamic_model_form_factory(attrs['form'])
        else:
            attrs['form'] = DynamicModelForm
        
        # If there's some inlines defined we make sure that their form is dynamic
        # see dynamic_inline_factory
        if 'inlines' in attrs:
            attrs['inlines'] = [dynamic_inline_factory(inline_cls) for inline_cls in attrs['inlines']]
        
        return super(DynamicAdminBase, cls).__new__(cls, name, bases, attrs)

class DynamicAdmin(admin.ModelAdmin):
    
    __metaclass__ = DynamicAdminBase
    
    def get_urls(self):
        # Inspired by
        # https://github.com/django-extensions/django-extensions/blob/master/django_extensions/admin/__init__.py
        from django.conf.urls.defaults import patterns, url

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.module_name

        urlpatterns = patterns('',
            url(r'choices/(?:(?P<object_id>\w+)/)?(inline/(?P<inline_prefix>[\w_]+)-(?P<inline_index>\d+)/)?$',
                wrap(self.dynamic_choices),
                name='%s_%s_dynamic_admin' % info),
        ) + super(DynamicAdmin, self).get_urls()

        return urlpatterns
    
    def dynamic_choices(self, request, object_id='', inline_prefix=None, inline_index=None):

        def get_dynamic_choices_from_form(form):
            fields = {}
            for name, field in form.fields.iteritems():
                if isinstance(field, DynamicModelChoiceField):
                    fields[name] = list(field.widget.choices)
            return fields
        
        opts = self.model._meta
        obj = self.get_object(request, object_id)
        # Make sure the specified object exists
        if object_id is not None and obj is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {
                          'name': force_unicode(opts.verbose_name), 'key': escape(object_id)})
        
        inlines = {}
        for formset in self.get_formsets(request, obj):
            inline_forms = []
            prefix = formset.get_default_prefix()
            try:
                forms = formset(request.GET, instance=obj).forms
            except ValidationError:
                return HttpResponseBadRequest("Missing %s ManagementForm data" % prefix)
            for form in forms:
                inline_forms.append(get_dynamic_choices_from_form(form))
            
            inlines[prefix] = inline_forms
        
        if inline_prefix is not None:
            found = False
            for formset in self.get_formsets(request, obj):
                prefix = formset.get_default_prefix()
                if inline_prefix == formset.get_default_prefix():
                    found = True
                    try:
                        forms = formset(request.GET, instance=obj).forms
                        try:
                            form = forms[int(inline_index)]
                            data = get_dynamic_choices_from_form(form)
                        except (IndexError, ValueError):
                            raise Http404("%s inline of index %s doesn't exist" % (inline_prefix, inline_index))
                    except ValidationError:
                        return HttpResponseBadRequest("Missing %s ManagementForm data" % prefix)
            if not found:
                raise Http404('Inline with prefix %s does not exist' % inline_prefix)
        else:
            form = self.get_form(request)(request.GET, instance=obj)
            fields = get_dynamic_choices_from_form(form)
            
            inlines = {}
            for formset in self.get_formsets(request, obj):
                inline_forms = []
                prefix = formset.get_default_prefix()
                try:
                    forms = formset(request.GET, instance=obj).forms
                except ValidationError:
                    return HttpResponseBadRequest("Missing %s ManagementForm data" % prefix)
                for form in forms:
                    inline_forms.append(get_dynamic_choices_from_form(form))
                
                inlines[prefix] = inline_forms
            
            data = {'fields': fields, 'inlines': inlines}
        return HttpResponse(simplejson.dumps(data), mimetype='application/json')
    
    # Make sure to pass request data to fieldsets
    # so they can use it to define choices
    def get_formsets(self, request, obj=None):
        initial = {}
        model = self.model
        opts = model._meta
        data = getattr(request, request.method).items()
        # Make sure to collect parent model data
        # and provide it to fieldsets in the form of
        # parent__field
        for k, v in data:
            if v:
                try:
                    f = opts.get_field(k)
                except models.FieldDoesNotExist:
                    continue
                if isinstance(f, models.ManyToManyField):
                    initial[k] = v.split(",")
                else:
                    initial[k] = v
        # If an object is provided it has data priority
        if obj is not None:
            initial.update(model_to_dict(obj))
        for fieldset, inline in zip(super(DynamicAdmin, self).get_formsets(request, obj), self.inline_instances):
            fk = _get_foreign_key(self.model, inline.model, fk_name=inline.fk_name).name
            fk_initial = dict(('%s__%s' % (fk, k),v) for k, v in initial.iteritems())
            # If we must provide additional data
            # we must wrap the fieldset in a subclass
            # because passing 'initial' key argument is intercepted
            # and not provided to subclasses by BaseInlineFormSet.__init__
            if len(initial):
                cls = dynamic_fieldset_factory(fieldset, fk_initial)
            else:
                cls = fieldset
            yield cls
