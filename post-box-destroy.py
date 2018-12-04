#!/usr/bin/python3
# -*- mode: python -*-
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
Cleanup actions to be run when a vagrant box is destroyed.
"""

import os

# Drop Plinth database
try:
    os.remove('data/var/lib/plinth/plinth.sqlite3')
except OSError:
    pass

# Truncate status.log
with open('data/var/log/plinth/status.log', 'w') as status_log:
    status_log.truncate()

# Truncate access.log
with open('data/var/log/plinth/access.log', 'w') as access_log:
    access_log.truncate()