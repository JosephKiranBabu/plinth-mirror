# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure a firewall.
"""

import contextlib
import logging

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import cfg, menu
from plinth.daemon import Daemon
from plinth.utils import Version, format_lazy, import_from_gi

from .manifest import backup  # noqa, pylint: disable=unused-import

gio = import_from_gi('Gio', '2.0')
glib = import_from_gi('GLib', '2.0')

version = 2

is_essential = True

managed_packages = ['firewalld', 'nftables']

managed_services = ['firewalld']

_description = [
    format_lazy(
        _('Firewall is a security system that controls the incoming and '
          'outgoing network traffic on your {box_name}. Keeping a '
          'firewall enabled and properly configured reduces risk of '
          'security threat from the Internet.'), box_name=cfg.box_name)
]

_port_details = {}

app = None

logger = logging.getLogger(__name__)

_DBUS_NAME = 'org.fedoraproject.FirewallD1'
_FIREWALLD_OBJECT = '/org/fedoraproject/FirewallD1'
_FIREWALLD_INTERFACE = 'org.fedoraproject.FirewallD1'
_ZONE_INTERFACE = 'org.fedoraproject.FirewallD1.zone'
_CONFIG_OBJECT = '/org/fedoraproject/FirewallD1/config'
_CONFIG_INTERFACE = 'org.fedoraproject.FirewallD1.config'
_CONFIG_SERVICE_INTERFACE = 'org.fedoraproject.FirewallD1.config.service'
_CONFIG_ZONE_INTERFACE = 'org.fedoraproject.FirewallD1.config.zone'


class FirewallApp(app_module.App):
    """FreedomBox app for Firewall."""

    app_id = 'firewall'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=version,
                               is_essential=is_essential, name=_('Firewall'),
                               icon='fa-shield', description=_description,
                               manual_page='Firewall')
        self.add(info)

        menu_item = menu.Menu('menu-firewall', info.name, None, info.icon,
                              'firewall:index', parent_url_name='system')
        self.add(menu_item)

        daemon = Daemon('daemon-firewall', managed_services[0])
        self.add(daemon)


def init():
    """Initailze firewall module"""
    global app
    app = FirewallApp()
    app.set_enabled(True)


def _run_setup():
    """Run firewalld setup."""
    _run(['setup'], superuser=True)
    add_service('http', 'external')
    add_service('http', 'internal')
    add_service('https', 'external')
    add_service('https', 'internal')
    add_service('dns', 'internal')
    add_service('dhcp', 'internal')


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    _run_setup()


def force_upgrade(helper, packages):
    """Force upgrade firewalld to resolve conffile prompts."""
    if 'firewalld' not in packages:
        return False

    # firewalld 0.6.x -> 0.7.x, 0.6.x -> 0.8.x, 0.7.x -> 0.8.x
    package = packages['firewalld']
    if Version(package['current_version']) >= Version('0.8') or \
       Version(package['new_version']) < Version('0.7'):
        return False

    helper.install(['firewalld'], force_configuration='new')
    _run_setup()
    return True


def _get_dbus_proxy(object, interface):
    """Return a DBusProxy for a given firewalld object and interface."""
    connection = gio.bus_get_sync(gio.BusType.SYSTEM)
    return gio.DBusProxy.new_sync(connection, gio.DBusProxyFlags.NONE, None,
                                  _DBUS_NAME, object, interface)


@contextlib.contextmanager
def ignore_dbus_error(dbus_error=None, service_error=None):
    try:
        yield
    except glib.Error as exception:
        parts = exception.message.split(':')
        if parts[0] != 'GDBus.Error':
            raise

        if (dbus_error and parts[1].strip() == 'org.freedesktop.DBus.Error.' +
                dbus_error):
            logger.error('Firewalld is not running.')
            pass
        elif (service_error and parts[2].strip() == service_error):
            logger.warning('Ignoring firewall exception: %s', service_error)
            pass
        else:
            raise


def get_enabled_status():
    """Return whether firewall is enabled"""
    output = _run(['get-status'], superuser=True)
    if not output:
        return False
    else:
        return output.split()[0] == 'running'


def get_enabled_services(zone):
    """Return the status of various services currently enabled"""
    with ignore_dbus_error(dbus_error='ServiceUnknown'):
        zone_proxy = _get_dbus_proxy(_FIREWALLD_OBJECT, _ZONE_INTERFACE)
        return zone_proxy.getServices('(s)', zone)

    return []  # When firewalld is not running


def get_port_details(service_port):
    """Return the port types and numbers for a service port"""
    try:
        return _port_details[service_port]
    except KeyError:
        config = _get_dbus_proxy(_CONFIG_OBJECT, _CONFIG_INTERFACE)
        try:
            service_path = config.getServiceByName('(s)', service_port)
        except glib.Error:
            return []  # Don't cache the error result

        service = _get_dbus_proxy(service_path, _CONFIG_SERVICE_INTERFACE)
        _port_details[service_port] = service.getPorts()
        return _port_details[service_port]


def get_interfaces(zone):
    """Return the list of interfaces in a zone."""
    with ignore_dbus_error(dbus_error='ServiceUnknown'):
        zone_proxy = _get_dbus_proxy(_FIREWALLD_OBJECT, _ZONE_INTERFACE)
        return zone_proxy.getInterfaces('(s)', zone)

    return []  # When firewalld is not running


def add_service(port, zone):
    """Enable a service in firewall"""
    with ignore_dbus_error(dbus_error='ServiceUnknown'):
        zone_proxy = _get_dbus_proxy(_FIREWALLD_OBJECT, _ZONE_INTERFACE)
        with ignore_dbus_error(service_error='ALREADY_ENABLED'):
            zone_proxy.addService('(ssi)', zone, port, 0)

        config = _get_dbus_proxy(_CONFIG_OBJECT, _CONFIG_INTERFACE)
        zone_path = config.getZoneByName('(s)', zone)
        config_zone = _get_dbus_proxy(zone_path, _CONFIG_ZONE_INTERFACE)
        with ignore_dbus_error(service_error='ALREADY_ENABLED'):
            config_zone.addService('(s)', port)


def remove_service(port, zone):
    """Remove a service in firewall"""
    with ignore_dbus_error(dbus_error='ServiceUnknown'):
        zone_proxy = _get_dbus_proxy(_FIREWALLD_OBJECT, _ZONE_INTERFACE)
        with ignore_dbus_error(service_error='NOT_ENABLED'):
            zone_proxy.removeService('(ss)', zone, port)

        config = _get_dbus_proxy(_CONFIG_OBJECT, _CONFIG_INTERFACE)
        zone_path = config.getZoneByName('(s)', zone)
        config_zone = _get_dbus_proxy(zone_path, _CONFIG_ZONE_INTERFACE)
        with ignore_dbus_error(service_error='NOT_ENABLED'):
            config_zone.removeService('(s)', port)


def _run(arguments, superuser=False):
    """Run an given command and raise exception if there was an error"""
    command = 'firewall'

    if superuser:
        return actions.superuser_run(command, arguments)
    else:
        return actions.run(command, arguments)
