from __future__ import absolute_import

from django.conf.urls.defaults import include, patterns

from . import admin


urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
)