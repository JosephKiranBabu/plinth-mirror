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

# XXX: Enable tests when repro module is enabled again.
@apps @sip @backups @sso @skip
Feature: Repro SIP Server
  Make audio and video calls.

Background:
  Given I'm a logged in user
  Given the repro application is installed

Scenario: Enable repro application
  Given the repro application is disabled
  When I enable the repro application
  Then the repro service should be running

Scenario: Backup and restore repro
  Given the repro application is enabled
  And repro has been configured
  When I create a backup of the repro app data
  And I delete the repro configuration
  And I restore the repro app data backup
  Then the repro configuration should be restored

Scenario: Disable repro application
  Given the repro application is enabled
  When I disable the repro application
  Then the repro service should not be running
