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
FreedomBox app to configure name services.
"""

import logging

from django.utils.translation import ugettext_lazy as _

from plinth import app as app_module
from plinth import cfg, menu
from plinth.signals import domain_added, domain_removed
from plinth.utils import format_lazy

from .manifest import backup

SERVICES = (
    ('http', _('HTTP'), 80),
    ('https', _('HTTPS'), 443),
    ('ssh', _('SSH'), 22),
)

version = 1

is_essential = True

name = _('Name Services')

domain_types = {}
domains = {}

logger = logging.getLogger(__name__)

manual_page = 'NameServices'

description = [
    format_lazy(
        _('Name Services provides an overview of the ways {box_name} can be '
          'reached from the public Internet: domain name, Tor hidden service, '
          'and Pagekite. For each type of name, it is shown whether the HTTP, '
          'HTTPS, and SSH services are enabled or disabled for incoming '
          'connections through the given name.'), box_name=(cfg.box_name))
]

app = None


class NamesApp(app_module.App):
    """FreedomBox app for names."""

    app_id = 'names'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-names', name, None, 'fa-tags',
                              'names:index', parent_url_name='system')
        self.add(menu_item)


def init():
    """Initialize the names module."""
    global app
    app = NamesApp()
    app.set_enabled(True)

    domain_added.connect(on_domain_added)
    domain_removed.connect(on_domain_removed)


def on_domain_added(sender, domain_type, name='', description='',
                    services=None, **kwargs):
    """Add domain to global list."""
    if not domain_type:
        return

    domain_types[domain_type] = description

    if not name:
        return
    if not services:
        services = []

    if domain_type not in domains:
        # new domain_type
        domains[domain_type] = {}
    domains[domain_type][name] = services
    logger.info('Added domain %s of type %s with services %s', name,
                domain_type, str(services))


def on_domain_removed(sender, domain_type, name='', **kwargs):
    """Remove domain from global list."""
    if domain_type in domains:
        if name == '':  # remove all domains of this type
            domains[domain_type] = {}
            logger.info('Removed all domains of type %s', domain_type)
        elif name in domains[domain_type]:
            del domains[domain_type][name]
            logger.info('Removed domain %s of type %s', name, domain_type)


def get_domain_types():
    """Get list of domain_types."""
    return list(domain_types.keys())


def get_description(domain_type):
    """Get description of a domain_type, if available."""
    if domain_type in domain_types:
        return domain_types[domain_type]
    else:
        return domain_type


def get_domain(domain_type):
    """
    Get domain of type domain_type.

    This function is meant for use with single-domain domain_types. If there is
    more than one domain, any one of the domains may be returned.
    """
    if domain_type in domains and len(domains[domain_type]) > 0:
        return list(domains[domain_type].keys())[0]
    else:
        return None


def get_enabled_services(domain_type, domain):
    """Get list of enabled services for a domain."""
    try:
        return domains[domain_type][domain]
    except KeyError:
        # domain_type or domain not registered
        return []


def get_services_status(domain_type, domain):
    """Get list of whether each service is enabled for a domain."""
    enabled = get_enabled_services(domain_type, domain)
    return [service[0] in enabled for service in SERVICES]
