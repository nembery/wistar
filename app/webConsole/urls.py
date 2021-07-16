

from django.conf.urls import url

from webConsole import views

app_name = 'webConsole'

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^(?P<port>\d+)$', views.console, name='console'),
]
