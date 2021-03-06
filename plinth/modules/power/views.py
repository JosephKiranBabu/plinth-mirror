# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for power module.
"""

from django.forms import Form
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse

from plinth import actions
from plinth.modules import power


def index(request):
    """Serve power controls page."""
    return TemplateResponse(
        request, 'power.html', {
            'title': power.app.info.name,
            'app_info': power.app.info,
            'pkg_manager_is_busy': _is_pkg_manager_busy()
        })


def restart(request):
    """Serve start confirmation page."""
    form = None

    if request.method == 'POST':
        actions.superuser_run('power', ['restart'], run_in_background=True)
        return redirect(reverse('apps'))
    else:
        form = Form(prefix='power')

    return TemplateResponse(
        request, 'power_restart.html', {
            'title': power.app.info.name,
            'form': form,
            'manual_page': power.app.info.manual_page,
            'pkg_manager_is_busy': _is_pkg_manager_busy()
        })


def shutdown(request):
    """Serve shutdown confirmation page."""
    form = None

    if request.method == 'POST':
        actions.superuser_run('power', ['shutdown'], run_in_background=True)
        return redirect(reverse('apps'))
    else:
        form = Form(prefix='power')

    return TemplateResponse(
        request, 'power_shutdown.html', {
            'title': power.app.info.name,
            'form': form,
            'manual_page': power.app.info.manual_page,
            'pkg_manager_is_busy': _is_pkg_manager_busy()
        })


def _is_pkg_manager_busy():
    """Return whether a package manager is running."""
    try:
        actions.superuser_run('packages', ['is-package-manager-busy'])
        return True
    except actions.ActionError:
        return False
