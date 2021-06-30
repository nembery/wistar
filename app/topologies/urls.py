
from django.conf.urls import url

from topologies import views

app_name = 'topologies'

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^edit/$', views.edit, name='edit'),
    url(r'^new/$', views.new, name='new'),
    url(r'^create/$', views.create, name='create'),
    url(r'^export/(?P<topo_id>\d+)/$', views.export_topology, name='exportTopology'),
    url(r'^import/$', views.import_topology, name='importTopology'),
    url(r'^error/$', views.error, name='error'),
    url(r'^clone/(?P<topo_id>\d+)/$', views.clone, name='clone'),
    url(r'^delete/(?P<topology_id>\d+)/$', views.delete, name='delete'),
    url(r'^(?P<topo_id>\d+)/$', views.detail, name='detail'),
    url(r'^launch/(?P<topology_id>\d+)$', views.launch, name='launch'),
    url(r'^parent/(?P<domain_name>[^/]+)$', views.parent, name='parent'),
    url(r'^exportHeat/(?P<topology_id>\d+)$', views.export_as_heat_template, name='exportHeat'),
    url(r'^addInstanceForm/$', views.add_instance_form, name='add_instance_form'),

]
