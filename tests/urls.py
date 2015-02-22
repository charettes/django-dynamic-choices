from __future__ import absolute_import

from . import admin

try:
    from django.conf.urls import include, url
except ImportError:
    from django.conf.urls.defaults import include, url

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
]
