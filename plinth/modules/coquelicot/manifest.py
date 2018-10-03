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

from django.utils.translation import ugettext_lazy as _

from plinth.clients import validate
from plinth.modules.backups.api import validate as validate_backups

clients = validate([{
    'name': _('coquelicot'),
    'platforms': [{
        'type': 'web',
        'url': '/coquelicot'
    }]
}])

backup = validate_backups({
    'data': {
        'directories': ['/var/lib/coquelicot']
    },
    'secrets': {
        'files': ['/etc/coquelicot/settings.yml']
    },
    'services': ['coquelicot']
})
