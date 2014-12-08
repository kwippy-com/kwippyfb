from django.conf.urls.defaults import *

urlpatterns = patterns('kwippyfb.fbapp.views',
    (r'^$', 'canvas'),
    # Define other pages you want to create here
    #(r'^callback/$', 'kwippyfb.fbapp.views.callback'),
    #(r'^add/$', 'fbsample.fbapp.views.add'),
    #(r'^remove/$', 'fbsample.fbapp.views.remove'),
    #(r'^refresh/$', 'fbsample.fbapp.views.refresh')
)

