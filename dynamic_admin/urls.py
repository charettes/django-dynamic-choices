from django.conf.urls.defaults import patterns, url
from views import dynamic_form

urlpatterns = patterns('',
    url(r'^(?P<app>\w+)/(?P<model>\w+)/(?P<object_id>\w+)?', dynamic_form),
)