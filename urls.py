from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # Example:
    (r'^kwippyfb/', include('kwippyfb.fbapp.urls')),

    # Uncomment this for admin:
#     (r'^admin/', include('django.contrib.admin.urls')),
)
