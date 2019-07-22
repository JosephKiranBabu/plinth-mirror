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
Django forms for sharing app.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from plinth.modules import sharing
from plinth.modules.users.forms import get_group_choices


class AddShareForm(forms.Form):
    """Form to add a new share."""

    name = forms.RegexField(
        label=_('Name of the share'), strip=True, regex=r'^[a-z0-9]+$',
        help_text=_(
            'A lowercase alpha-numeric string that uniquely identifies a '
            'share. Example: <em>media</em>.'))

    path = forms.CharField(
        label=_('Path to share'), strip=True, help_text=_(
            'Disk path to a folder on this server that you intend to share.'))

    is_public = forms.BooleanField(
        label=_('Public share'), required=False, help_text=_(
            'Make files in this folder available to anyone with the link.'))

    groups = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple, required=False,
        label=_('User groups that can read the files in the share'),
        help_text=_(
            'Users of the selected user groups will be able to read the '
            'files in the share.'))

    def __init__(self, *args, **kwargs):
        """Initialize the form with extra request argument."""
        super().__init__(*args, **kwargs)
        self.fields['groups'].choices = get_group_choices()
        self.fields['name'].widget.attrs.update({'autofocus': 'autofocus'})

    def clean_name(self):
        """Check if the name is valid."""
        name = self.cleaned_data['name']
        if 'name' in self.initial and name == self.initial['name']:
            return name

        if any((share for share in sharing.list_shares()
                if name == share['name'])):
            raise ValidationError(_('A share with this name already exists.'))

        return name

    def clean(self):
        """Check that at least one group is added for non-public shares."""
        super(AddShareForm, self).clean()
        is_public = self.cleaned_data.get('is_public')
        groups = self.cleaned_data.get('groups')
        if not is_public and not groups:
            raise forms.ValidationError(
                _('Shares should be either public or shared with at least one group'
                  ))
