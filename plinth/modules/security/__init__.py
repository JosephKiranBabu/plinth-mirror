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
FreedomBox app for security configuration.
"""

import subprocess
from collections import defaultdict

import requests
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import menu, module_loader

from .manifest import backup  # noqa, pylint: disable=unused-import

version = 6

is_essential = True

name = _('Security')

managed_packages = ['fail2ban', 'debsecan']

managed_services = ['fail2ban']

manual_page = 'Security'

ACCESS_CONF_FILE = '/etc/security/access.d/50freedombox.conf'
ACCESS_CONF_FILE_OLD = '/etc/security/access.conf'
ACCESS_CONF_SNIPPET = '-:ALL EXCEPT root fbx plinth (admin) (sudo):ALL'
OLD_ACCESS_CONF_SNIPPET = '-:ALL EXCEPT root fbx (admin) (sudo):ALL'
ACCESS_CONF_SNIPPETS = [OLD_ACCESS_CONF_SNIPPET, ACCESS_CONF_SNIPPET]

app = None


class SecurityApp(app_module.App):
    """FreedomBox app for security."""

    app_id = 'security'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-security', name, None, 'fa-lock',
                              'security:index', parent_url_name='system')
        self.add(menu_item)


def init():
    """Initialize the module"""
    global app
    app = SecurityApp()
    app.set_enabled(True)


def setup(helper, old_version=None):
    """Install the required packages"""
    helper.install(managed_packages)
    setup_fail2ban()

    # Migrate to new config file.
    enabled = get_restricted_access_enabled()
    set_restricted_access(False)
    if enabled:
        set_restricted_access(True)


def setup_fail2ban():
    actions.superuser_run('service', ['unmask', 'fail2ban'])
    actions.superuser_run('service', ['enable', 'fail2ban'])
    actions.superuser_run('service', ['reload', 'fail2ban'])


def get_restricted_access_enabled():
    """Return whether restricted access is enabled"""
    with open(ACCESS_CONF_FILE_OLD, 'r') as conffile:
        if any(line.strip() in ACCESS_CONF_SNIPPETS
               for line in conffile.readlines()):
            return True

    try:
        with open(ACCESS_CONF_FILE, 'r') as conffile:
            return any(line.strip() in ACCESS_CONF_SNIPPETS
                       for line in conffile.readlines())
    except FileNotFoundError:
        return False


def set_restricted_access(enabled):
    """Enable or disable restricted access"""
    action = 'disable-restricted-access'
    if enabled:
        action = 'enable-restricted-access'

    actions.superuser_run('security', [action])


def get_apps_report():
    """Return a security report for each app"""
    lines = subprocess.check_output(['debsecan']).decode().split('\n')
    cves = defaultdict(set)
    for line in lines:
        if line:
            (label, package, *_) = line.split()
            cves[label].add(package)

    try:
        past_cves = requests.get(
            'https://security-tracker.debian.org/tracker/data/json').json()
    except Exception:
        past_cves = None

    apps = {
        'freedombox': {
            'name': 'freedombox',
            'packages': {'freedombox'},
            'vulns': 0,
            'past_vulns': 0 if past_cves else None,
        }
    }
    if past_cves and 'freedombox' in past_cves:
        apps['freedombox']['past_vulns'] = len(past_cves['freedombox'])

    for module_name, module in module_loader.loaded_modules.items():
        try:
            packages = module.managed_packages
        except AttributeError:
            continue  # app has no managed packages

        try:
            services = module.managed_services
        except AttributeError:
            services = None

        # filter out apps not setup yet
        if module.setup_helper.get_state() == 'needs-setup':
            continue

        apps[module_name] = {
            'name': module_name,
            'packages': set(packages),
            'vulns': 0,
            'past_vulns': 0 if past_cves else None,
            'sandboxed': None,
        }

        for package in packages:
            if past_cves and package in past_cves:
                apps[module_name]['past_vulns'] += len(past_cves[package])

        if services:
            apps[module_name]['sandboxed'] = False
            for service in services:
                if _get_service_is_sandboxed(service):
                    apps[module_name]['sandboxed'] = True

    for cve_packages in cves.values():
        for app_ in apps.values():
            if cve_packages & app_['packages']:
                app_['vulns'] += 1

    return apps


def _get_service_is_sandboxed(service):
    """Return whether service is sandboxed."""
    lines = subprocess.check_output([
        'systemctl',
        'show',
        service,
        '--property=ProtectSystem',
        '--property=ProtectHome',
        '--property=PrivateTmp',
        '--property=PrivateDevices',
        '--property=PrivateNetwork',
        '--property=PrivateUsers',
        '--property=PrivateMounts',
    ]).decode().strip().split('\n')
    pairs = [line.partition('=')[::2] for line in lines]
    properties = {name: value for name, value in pairs}
    if properties['ProtectSystem'] in ['yes', 'full', 'strict']:
        return True

    if properties['ProtectHome'] in ['yes', 'read-only', 'tmpfs']:
        return True

    for name in [
            'PrivateTmp', 'PrivateDevices', 'PrivateNetwork', 'PrivateUsers',
            'PrivateMounts'
    ]:
        if properties[name] == 'yes':
            return True

    return False
