# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure ikiwiki.
"""

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.modules.apache.components import Webserver
from plinth.modules.firewall.components import Firewall
from plinth.modules.users import register_group
from plinth.utils import format_lazy

from .manifest import backup, clients  # noqa, pylint: disable=unused-import

version = 1

managed_packages = [
    'ikiwiki', 'libdigest-sha-perl', 'libxml-writer-perl', 'xapian-omega',
    'libsearch-xapian-perl', 'libimage-magick-perl'
]

_description = [
    _('ikiwiki is a simple wiki and blog application. It supports '
      'several lightweight markup languages, including Markdown, and '
      'common blogging functionality such as comments and RSS feeds.'),
    format_lazy(
        _('Only {box_name} users in the <b>admin</b> group can <i>create</i> '
          'and <i>manage</i> blogs and wikis, but any user in the <b>wiki</b> '
          'group can <i>edit</i> existing ones. In the <a href="{users_url}">'
          'User Configuration</a> you can change these '
          'permissions or add new users.'), box_name=_(cfg.box_name),
        users_url=reverse_lazy('users:index'))
]

group = ('wiki', _('View and edit wiki applications'))

app = None


class IkiwikiApp(app_module.App):
    """FreedomBox app for Ikiwiki."""

    app_id = 'ikiwiki'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=version,
                               name=_('ikiwiki'), icon_filename='ikiwiki',
                               short_description=_('Wiki and Blog'),
                               description=_description, manual_page='Ikiwiki',
                               clients=clients)
        self.add(info)

        menu_item = menu.Menu('menu-ikiwiki', info.name,
                              info.short_description, info.icon_filename,
                              'ikiwiki:index', parent_url_name='apps')
        self.add(menu_item)

        self.refresh_sites()

        firewall = Firewall('firewall-ikiwiki', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-ikiwiki', 'ikiwiki-plinth',
                              urls=['https://{host}/ikiwiki'])
        self.add(webserver)

    def add_shortcut(self, site, title):
        """Add an ikiwiki shortcut to frontpage."""
        shortcut = frontpage.Shortcut('shortcut-ikiwiki-' + site, title,
                                      icon=self.info.icon_filename,
                                      url='/ikiwiki/' + site,
                                      clients=self.info.clients)
        self.add(shortcut)
        return shortcut

    def remove_shortcut(self, site):
        """Remove an ikiwiki shortcut from frontpage."""
        component = self.remove('shortcut-ikiwiki-' + site)
        component.remove()  # Remove from global list.

    def refresh_sites(self):
        """Refresh blog and wiki list"""
        sites = actions.run('ikiwiki', ['get-sites']).split('\n')
        sites = [name.split(' ', 1) for name in sites if name != '']

        for site in sites:
            if not 'shortcut-ikiwiki-' + site[0] in self.components:
                self.add_shortcut(site[0], site[1])

        return sites


def init():
    """Initialize the ikiwiki module."""
    global app
    app = IkiwikiApp()
    register_group(group)

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
        app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'ikiwiki', ['setup'])
    helper.call('post', app.enable)
