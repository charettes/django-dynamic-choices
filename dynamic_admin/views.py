import simplejson

from django.contrib.admin.util import unquote
from django.template.defaultfilters import escape
from django.utils.encoding import force_unicode
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.http import HttpResponseNotFound, HttpResponse, Http404,\
    HttpResponseBadRequest
from django.db.models.loading import get_model
from django.contrib import admin
from django.core.exceptions import ValidationError

from __init__ import DynamicAdmin
from forms.fields import DynamicModelChoiceField

def get_dynamic_choices_from_form(form):
    fields = {}
    for name, field in form.fields.iteritems():
        if isinstance(field, DynamicModelChoiceField):
            fields[name] = list(field.widget.choices)
    return fields

@login_required
def dynamic_form(request, app, model, object_id=None):
    model_cls = get_model(app, model)
    if model_cls is None:
        return HttpResponseNotFound("Cannot find model %s.%s" % (app, model))
    if model_cls in admin.site._registry:
        model_admin = admin.site._registry[model_cls]
        if isinstance(model_admin, DynamicAdmin):
            opts = model_cls._meta
            if object_id is not None:
                obj = model_admin.get_object(request, unquote(object_id))
                if obj is None:
                    raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {'name': force_unicode(opts.verbose_name), 'key': escape(object_id)})
            else:
                obj = model_cls()

            form = model_admin.get_form(request)(request.GET, instance=obj)
            fields = get_dynamic_choices_from_form(form)
                    
            inlines = {}
            for formset in model_admin.get_formsets(request, obj):
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
        else:
            return HttpResponseNotFound("Model %s.%s's admin is not a subclass of DynamicAdmin" % (app, model))
    else:
        return HttpResponseNotFound("Model %s.%s is not registered to the admin" % (app, model))