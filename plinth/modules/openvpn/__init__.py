# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure OpenVPN server.
"""

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.firewall.components import Firewall
from plinth.utils import format_lazy

from .manifest import backup, clients  # noqa, pylint: disable=unused-import

version = 4

managed_services = ['openvpn-server@freedombox']

managed_packages = ['openvpn', 'easy-rsa']

_description = [
    format_lazy(
        _('Virtual Private Network (VPN) is a technique for securely '
          'connecting two devices in order to access resources of a '
          'private network.  While you are away from home, you can connect '
          'to your {box_name} in order to join your home network and '
          'access private/internal services provided by {box_name}. '
          'You can also access the rest of the Internet via {box_name} '
          'for added security and anonymity.'), box_name=_(cfg.box_name))
]

port_forwarding_info = [('UDP', 1194)]

app = None


class OpenVPNApp(app_module.App):
    """FreedomBox app for OpenVPN."""

    app_id = 'openvpn'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=version,
                               name=_('OpenVPN'), icon_filename='openvpn',
                               short_description=_('Virtual Private Network'),
                               description=_description, manual_page='OpenVPN',
                               clients=clients)
        self.add(info)

        menu_item = menu.Menu('menu-openvpn', info.name,
                              info.short_description, info.icon_filename,
                              'openvpn:index', parent_url_name='apps')
        self.add(menu_item)

        download_profile = \
            format_lazy(_('<a class="btn btn-primary btn-sm" href="{link}">'
                          'Download Profile</a>'),
                        link=reverse_lazy('openvpn:profile'))
        shortcut = frontpage.Shortcut(
            'shortcut-openvpn', info.name,
            short_description=info.short_description, icon=info.icon_filename,
            description=info.description + [download_profile],
            configure_url=reverse_lazy('openvpn:index'), login_required=True)
        self.add(shortcut)

        firewall = Firewall('firewall-openvpn', info.name, ports=['openvpn'],
                            is_external=True)
        self.add(firewall)

        daemon = Daemon('daemon-openvpn', managed_services[0],
                        listen_ports=[(1194, 'udp4'), (1194, 'udp6')])
        self.add(daemon)


def init():
    """Initialize the OpenVPN module."""
    global app
    app = OpenVPNApp()

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled() \
       and is_setup():
        app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'openvpn', ['upgrade'])
    if app.is_enabled() and is_setup():
        helper.call('post', app.enable)


def is_setup():
    """Return whether the service is running."""
    return actions.superuser_run('openvpn', ['is-setup']).strip() == 'true'
