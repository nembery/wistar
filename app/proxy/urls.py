
from django.conf.urls import url

from proxy import views

app_name = 'proxy'

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^ip/$', views.proxies_for_ip, name='proxies_for_ip'),
    url(r'^launch/$', views.launch_proxy, name='launch_proxy'),
    url(r'^terminate/$', views.terminate_proxy, name='terminate_proxy'),
]
