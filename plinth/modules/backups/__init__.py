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
import os
import re

import paramiko
from django.utils.text import get_valid_filename
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import cfg, menu
from plinth.utils import format_lazy

from . import api

version = 2

managed_packages = ['borgbackup', 'sshfs']

name = _('Backups')

description = [
    _('Backups allows creating and managing backup archives.'),
]

manual_page = 'Backups'

MANIFESTS_FOLDER = '/var/lib/plinth/backups-manifests/'
ROOT_REPOSITORY = '/var/lib/freedombox/borgbackup'
ROOT_REPOSITORY_NAME = format_lazy(
    _('{box_name} storage'), box_name=cfg.box_name)
ROOT_REPOSITORY_UUID = 'root'
# session variable name that stores when a backup file should be deleted
SESSION_PATH_VARIABLE = 'fbx-backups-upload-path'

app = None


class BackupsApp(app_module.App):
    """FreedomBox app for backup and restore."""

    app_id = 'backups'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-backups', name, None, 'fa-files-o',
                              'backups:index', parent_url_name='system')
        self.add(menu_item)


def init():
    """Intialize the module."""
    global app
    app = BackupsApp()

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
        app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'backups',
                ['setup', '--path', ROOT_REPOSITORY])
    helper.call('post', app.enable)


def _backup_handler(packet, encryption_passphrase=None):
    """Performs backup operation on packet."""
    if not os.path.exists(MANIFESTS_FOLDER):
        os.makedirs(MANIFESTS_FOLDER)

    manifest_path = os.path.join(MANIFESTS_FOLDER,
                                 get_valid_filename(packet.path) + '.json')
    manifests = {
        'apps': [{
            'name': app.name,
            'version': app.app.version,
            'backup': app.manifest
        } for app in packet.apps]
    }
    with open(manifest_path, 'w') as manifest_file:
        json.dump(manifests, manifest_file)

    paths = packet.directories + packet.files
    paths.append(manifest_path)
    arguments = ['create-archive', '--path', packet.path, '--paths'] + paths
    if encryption_passphrase:
        arguments += ['--encryption-passphrase', encryption_passphrase]
    actions.superuser_run('backups', arguments)


def get_exported_archive_apps(path):
    """Get list of apps included in exported archive file."""
    arguments = ['get-exported-archive-apps', '--path', path]
    output = actions.superuser_run('backups', arguments)
    return output.splitlines()


def _restore_exported_archive_handler(packet, encryption_passphrase=None):
    """Perform restore operation on packet."""
    locations = {'directories': packet.directories, 'files': packet.files}
    locations_data = json.dumps(locations)
    actions.superuser_run('backups',
                          ['restore-exported-archive', '--path', packet.path],
                          input=locations_data.encode())


def restore_archive_handler(packet, encryption_passphrase=None):
    """Perform restore operation on packet."""
    locations = {'directories': packet.directories, 'files': packet.files}
    locations_data = json.dumps(locations)
    arguments = [
        'restore-archive', '--path', packet.path, '--destination', '/'
    ]
    if encryption_passphrase:
        arguments += ['--encryption-passphrase', encryption_passphrase]
    actions.superuser_run('backups', arguments, input=locations_data.encode())


def restore_from_upload(path, apps=None):
    """Restore files from an uploaded .tar.gz backup file"""
    api.restore_apps(_restore_exported_archive_handler, app_names=apps,
                     create_subvolume=False, backup_file=path)


def is_ssh_hostkey_verified(hostname):
    """Check whether SSH Hostkey has already been verified.
    hostname: Domain name or IP address of the host
    """
    known_hosts_path = cfg.known_hosts
    if not os.path.exists(known_hosts_path):
        return False

    known_hosts = paramiko.hostkeys.HostKeys(known_hosts_path)
    host_keys = known_hosts.lookup(hostname)
    return host_keys is not None


def split_path(path):
    """Splits the given path into username, hostname, directory.

    Network interface information is kept in the hostname if provided.
    e.g. fe80::2078:6c26:498a:1fa5%wlp1s0
    """
    return re.findall(r'^(.*)@([^/]*):(.*)$', path)[0]
