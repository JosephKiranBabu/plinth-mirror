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
Views for the backups app.
"""

from datetime import date
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import FormView, TemplateView
from urllib.parse import unquote

from plinth.modules import backups

from .forms import CreateArchiveForm, ExportArchiveForm


class IndexView(TemplateView):
    """View to show list of archives."""
    template_name = 'backups.html'

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = backups.name
        context['description'] = backups.description
        context['info'] = backups.get_info()
        context['archives'] = backups.list_archives()
        context['exports'] = backups.get_export_files()
        return context


class CreateArchiveView(SuccessMessageMixin, FormView):
    """View to create a new archive."""
    form_class = CreateArchiveForm
    prefix = 'backups'
    template_name = 'backups_form.html'
    success_url = reverse_lazy('backups:index')
    success_message = _('Archive created.')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create Archive')
        return context

    def get_initial(self):
        """Return the initial data to use for forms on this view."""
        initial = super().get_initial()
        initial['name'] = 'FreedomBox_backup_' + str(date.today())
        return initial

    def form_valid(self, form):
        """Create the archive on valid form submission."""
        backups.create_archive(form.cleaned_data['name'],
                               form.cleaned_data['selected_apps'])
        return super().form_valid(form)


class DeleteArchiveView(SuccessMessageMixin, TemplateView):
    """View to delete an archive."""
    template_name = 'backups_delete.html'

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Delete Archive')
        context['archive'] = backups.get_archive(self.kwargs['name'])
        if context['archive'] is None:
            raise Http404

        return context

    def post(self, request, name):
        """Delete the archive."""
        backups.delete_archive(name)
        messages.success(request, _('Archive deleted.'))
        return redirect(reverse_lazy('backups:index'))


class ExportArchiveView(SuccessMessageMixin, FormView):
    """View to export an archive."""
    form_class = ExportArchiveForm
    prefix = 'backups'
    template_name = 'backups_form.html'
    success_url = reverse_lazy('backups:index')
    success_message = _('Archive exported.')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Export Archive')
        context['archive'] = backups.get_archive(self.kwargs['name'])
        if context['archive'] is None:
            raise Http404

        return context

    def form_valid(self, form):
        """Create the archive on valid form submission."""
        backups.export_archive(self.kwargs['name'],
                               form.cleaned_data['disk'])
        return super().form_valid(form)


class RestoreView(SuccessMessageMixin, TemplateView):
    """View to restore files from an exported archive."""
    template_name = 'backups_restore.html'

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Restore from backup')
        context['label'] = unquote(self.kwargs['label'])
        context['name'] = self.kwargs['name']
        return context

    def post(self, request, label, name):
        """Restore files from the archive on valid form submission."""
        backups.restore_exported(label, name)
        messages.success(request, _('Restored data from backup.'))
        return redirect(reverse_lazy('backups:index'))
