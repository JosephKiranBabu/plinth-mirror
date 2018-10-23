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

@essential @upgrades @system
Feature: Software Upgrades
  Configure automatic software upgrades

Background:
  Given I'm a logged in user

Scenario: Enable automatic upgrades
  Given automatic upgrades are disabled
  When I enable automatic upgrades
  Then automatic upgrades should be enabled

Scenario: Disable automatic upgrades
  Given automatic upgrades are enabled
  When I disable automatic upgrades
  Then automatic upgrades should be disabled
