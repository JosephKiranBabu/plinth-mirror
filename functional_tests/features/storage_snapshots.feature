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

@system @snapshots
Feature: Storage Snapshots
  Run storage snapshots application - Snapper.

Background:
  Given I'm a logged in user
  Given the snapshot application is installed

Scenario: Create a snapshot
  Given the list of snapshots is empty
  When I manually create a snapshot
  Then there should be 1 snapshot in the list

Scenario: Configure snapshots
  Given snapshots are configured with timeline snapshots disabled, software snapshots disabled, hourly limit 10, daily limit 3, weekly limit 2, monthly limit 2, yearly limit 0, delete old software snapshots 15
  When I configure snapshots with timeline snapshots enabled, software snapshots enabled, hourly limit 3, daily limit 2, weekly limit 1, monthly limit 1, yearly limit 1, delete old software snapshots 2
  Then snapshots should be configured with timeline snapshots enabled, software snapshots enabled, hourly limit 3, daily limit 2, weekly limit 1, monthly limit 1, yearly limit 1, delete old software snapshots 2
