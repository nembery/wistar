"""wistar URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf.urls import include, url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^topologies/', include('topologies.urls', namespace="topologies")),
    url(r'^images/', include('images.urls', namespace="images")),
    url(r'^ajax/', include('ajax.urls', namespace="ajax")),
    url(r'^webConsole/', include('webConsole.urls', namespace="webConsole")),
    # url(r'^scripts/', include('scripts.urls', namespace="scripts")),
    url(r'^api/', include('api.urls', namespace="api")),
    url(r'^proxy/', include('proxy.urls', namespace="proxy")),
]