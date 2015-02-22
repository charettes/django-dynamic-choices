from __future__ import absolute_import

from django.conf.urls.defaults import include

from . import admin

urlpatterns = [
    (r'^admin/', include(admin.site.urls)),
]
