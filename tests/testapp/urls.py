from django.conf.urls.defaults import patterns, include

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    
     (r'^admin/', include(admin.site.urls)),
     
#     (r'^dynamic_admin/', include(dynamic_admin.urls))
     
)
