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
FreedomBox app to manage backup archives.
"""

import json

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth.menu import main_menu

version = 1

managed_packages = ['borgbackup']

name = _('Backups')

description = [_('Backups allows creating and managing backup archives.'), ]

service = None


def init():
    """Intialize the module."""
    menu = main_menu.get('system')
    menu.add_urlname(name, 'glyphicon-duplicate', 'backups:index')


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'backups', ['setup'])


def get_info():
    output = actions.superuser_run('backups', ['info'])
    return json.loads(output)


def list_archives():
    output = actions.superuser_run('backups', ['list'])
    return json.loads(output)['archives']


def get_archive(name):
    for archive in list_archives():
        if archive['name'] == name:
            return archive

    return None


def create_archive(name, path):
    actions.superuser_run('backups',
                          ['create', '--name', name, '--path', path])


def delete_archive(name):
    actions.superuser_run('backups', ['delete', '--name', name])


def extract_archive(name, destination):
    actions.superuser_run(
        'backups', ['extract', '--name', name, '--destination', destination])


def export_archive(name, filename):
    actions.superuser_run('backups',
                          ['export', '--name', name, '--filename', filename])