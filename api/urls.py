from django.conf.urls import patterns, url

urlpatterns = patterns('api.views',
    url(r'^all/$', 'render_list'),
    url(r'^new/$', 'new_render'),
    url(r'^stop/$', 'stop_render'),
    url(r'^one/(?P<pk>[0-9]+)/$', 'render_detail'),
)