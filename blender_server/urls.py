from django.conf.urls import patterns, url, include
from rest_framework import routers
from api import views
from django.conf.urls.static import static
from django.conf import settings

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browseable API.
urlpatterns = patterns('',
    url(r'^', include(router.urls)),
    url(r'^render/', include('api.urls')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)