from __future__ import absolute_import

from django.conf.urls.defaults import include, url

from . import admin

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
]
