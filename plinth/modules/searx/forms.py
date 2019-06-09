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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
"""
Django form for configuring Searx.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _

from plinth.forms import ServiceForm


class SearxForm(ServiceForm):
    """Searx configuration form."""
    safe_search = forms.ChoiceField(
        label=_('Safe Search'), help_text=_(
            'Select the default family filter to apply to your search results.'
        ), choices=((0, _('None')), (1, _('Moderate')), (2, _('Strict'))))

    public_access = forms.BooleanField(
        label=_('Allow Public Access'), help_text=_(
            'Allow this application to be used by anyone who can reach it.'),
        required=False)
