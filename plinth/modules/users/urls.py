#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
URLs for the Users module
"""

from axes.decorators import axes_dispatch
from django.conf.urls import url
from django.urls import reverse_lazy
from stronghold.decorators import public

from plinth.modules.sso.views import SSOLoginView, SSOLogoutView
from plinth.utils import non_admin_view

from . import views

urlpatterns = [
    url(r'^sys/users/$', views.UserList.as_view(), name='index'),
    url(r'^sys/users/create/$', views.UserCreate.as_view(), name='create'),
    url(r'^sys/users/(?P<slug>[\w.@+-]+)/edit/$',
        non_admin_view(views.UserUpdate.as_view()), name='edit'),
    url(r'^sys/users/(?P<slug>[\w.@+-]+)/delete/$', views.UserDelete.as_view(),
        name='delete'),
    url(r'^sys/users/(?P<slug>[\w.@+-]+)/change_password/$',
        non_admin_view(views.UserChangePassword.as_view()),
        name='change_password'),

    # Authnz is handled by SSO

    # XXX: Use axes authentication backend and middleware instead of
    # axes_dispatch after axes 5.x becomes available in Debian stable.
    url(r'^accounts/login/$', public(axes_dispatch(SSOLoginView.as_view())),
        name='login'),
    url(r'^accounts/logout/$', non_admin_view(SSOLogoutView.as_view()),
        {'next_page': reverse_lazy('index')}, name='logout'),
    url(r'^users/firstboot/$', public(views.FirstBootView.as_view()),
        name='firstboot'),
]
