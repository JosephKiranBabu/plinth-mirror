# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for service discovery.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import cfg, menu
from plinth.daemon import Daemon
from plinth.modules.config import get_hostname
from plinth.modules.firewall.components import Firewall
from plinth.modules.names.components import DomainType
from plinth.signals import domain_added, domain_removed, post_hostname_change
from plinth.utils import format_lazy
from plinth.views import AppView

from .manifest import backup  # noqa, pylint: disable=unused-import

# pylint: disable=C0103

version = 1

is_essential = True

managed_services = ['avahi-daemon']

managed_packages = ['avahi-daemon', 'avahi-utils']

_description = [
    format_lazy(
        _('Service discovery allows other devices on the network to '
          'discover your {box_name} and services running on it.  It '
          'also allows {box_name} to discover other devices and '
          'services running on your local network.  Service discovery is '
          'not essential and works only on internal networks.  It may be '
          'disabled to improve security especially when connecting to a '
          'hostile local network.'), box_name=_(cfg.box_name))
]

manual_page = 'ServiceDiscovery'

app = None


class AvahiApp(app_module.App):
    """FreedomBox app for Avahi."""

    app_id = 'avahi'

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=version,
                               name=_('Service Discovery'), icon='fa-compass',
                               description=_description,
                               manual_page='ServiceDiscovery')
        self.add(info)

        menu_item = menu.Menu('menu-avahi', info.name, None, info.icon,
                              'avahi:index', parent_url_name='system')
        self.add(menu_item)

        domain_type = DomainType('domain-type-local',
                                 _('Local Network Domain'), 'config:index',
                                 can_have_certificate=False)
        self.add(domain_type)

        firewall = Firewall('firewall-avahi', info.name, ports=['mdns'],
                            is_external=False)
        self.add(firewall)

        daemon = Daemon('daemon-avahi', managed_services[0])
        self.add(daemon)


def init():
    """Initialize the service discovery module."""
    global app
    app = AvahiApp()
    if app.is_enabled():
        domain_added.send_robust(sender='avahi',
                                 domain_type='domain-type-local',
                                 name=get_hostname() + '.local',
                                 services='__all__')
        app.set_enabled(True)

    post_hostname_change.connect(on_post_hostname_change)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    # Reload avahi-daemon now that first-run does not reboot. After performing
    # FreedomBox Service (Plinth) package installation, new Avahi files will be
    # available and require restart.
    helper.call('post', actions.superuser_run, 'service',
                ['reload', 'avahi-daemon'])


def on_post_hostname_change(sender, old_hostname, new_hostname, **kwargs):
    """Update .local domain after hostname change."""
    del sender  # Unused
    del kwargs  # Unused

    domain_removed.send_robust(sender='avahi', domain_type='domain-type-local',
                               name=old_hostname + '.local')
    domain_added.send_robust(sender='avahi', domain_type='domain-type-local',
                             name=new_hostname + '.local', services='__all__')


class AvahiAppView(AppView):
    app_id = 'avahi'
