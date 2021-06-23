#
# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
#
# Copyright (c) 2015 Juniper Networks, Inc.
# All rights reserved.
#
# Use is subject to license terms.
#
# Licensed under the Apache License, Version 2.0 (the ?License?); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at http://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from django.conf.urls import include, url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^topologies/', include('topologies.urls', namespace="topologies")),
    url(r'^images/', include('images.urls', namespace="images")),
    url(r'^ajax/', include('ajax.urls', namespace="ajax")),
    url(r'^webConsole/', include('webConsole.urls', namespace="webConsole")),
    url(r'^scripts/', include('scripts.urls', namespace="scripts")),
    url(r'^api/', include('api.urls', namespace="api")),
    url(r'^proxy/', include('proxy.urls', namespace="proxy")),
]
