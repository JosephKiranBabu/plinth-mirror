# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import ugettext_lazy as _

from plinth.modules.backups.api import validate as validate_backup
from plinth.clients import validate, store_url

clients = validate([
    {
        'name': _('vlc'),
        'platforms': [
            {
                'type': 'package',
                'os': 'gnu-linux',
                'format': 'deb',
                'name': 'vlc',
            },
            {
                'type': 'package',
                'os': 'gnu-linux',
                'format': 'rpm',
                'name': 'vlc',
            },
            {
                'type': 'download',
                'os': 'windows',
                'url': 'https://www.videolan.org/vlc/download-windows.html',
            },
            {
                'type': 'download',
                'os': 'macos',
                'url': 'https://www.videolan.org/vlc/download-macosx.html',
            },
            {
                'type': 'store',
                'os': 'android',
                'store_name': 'google-play',
                'url': store_url('google-play', 'org.videolan.vlc')
            },
            {
                'type': 'store',
                'os': 'android',
                'store_name': 'f-droid',
                'url': store_url('f-droid', 'org.videolan.vlc')
            },
        ]
    },
    {
        'name': _('kodi'),
        'platforms': [
            {
                'type': 'package',
                'os': 'gnu-linux',
                'format': 'deb',
                'name': 'kodi',
            },
            {
                'type': 'package',
                'os': 'gnu-linux',
                'format': 'rpm',
                'name': 'kodi',
            },
            {
                'type': 'download',
                'os': 'windows',
                'url': 'http://kodi.tv/download/',
            },
            {
                'type': 'download',
                'os': 'macos',
                'url': 'http://kodi.tv/download/',
            },
            {
                'type': 'store',
                'os': 'android',
                'store_name': 'google-play',
                'url': store_url('google-play', 'org.xbmc.kodi')
            },
            {
                'type': 'store',
                'os': 'android',
                'store_name': 'f-droid',
                'url': store_url('f-droid', 'org.xbmc.kodi')
            },
        ]
    },
    {
        'name': _('yaacc'),
        'platforms': [
            {
                'type': 'store',
                'os': 'android',
                'store_name': 'f-droid',
                'url': store_url('f-droid', 'de.yaacc')
            },
        ]
    },
    {
        'name': _('totem'),
        'platforms': [
            {
                'type': 'package',
                'os': 'gnu-linux',
                'format': 'deb',
                'name': 'totem',
            },
            {
                'type': 'package',
                'os': 'gnu-linux',
                'format': 'rpm',
                'name': 'totem',
            },
        ]
    },
])

# TODO: get all media directories from config file
# for now hard code default media folder.
backup = validate_backup({
    'data': {
        'directories': ['/var/lib/minidlna']
    }
})
