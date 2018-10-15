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

import os
import time

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from support import application, config, interface, system
from support.service import eventually, wait_for_page_update

# unlisted sites just use '/' + site_name as url
site_url = {
    'wiki': '/ikiwiki',
    'jsxc': '/plinth/apps/jsxc/jsxc/',
    'cockpit': '/_cockpit/'
}


def get_site_url(site_name):
    url = '/' + site_name
    if site_name in site_url:
        url = site_url[site_name]
    return url


def is_available(browser, site_name):
    browser.visit(config['DEFAULT']['url'] + get_site_url(site_name))
    time.sleep(3)
    browser.reload()
    return '404' not in browser.title


def access_url(browser, site_name):
    browser.visit(config['DEFAULT']['url'] + get_site_url(site_name))


def verify_coquelicot_upload_password(browser, password):
    browser.visit(config['DEFAULT']['url'] + '/coquelicot')
    # ensure the password form is scrolled into view
    browser.execute_script('window.scrollTo(100, 0)')
    browser.find_by_id('upload_password').fill(password)
    actions = ActionChains(browser.driver)
    actions.send_keys(Keys.RETURN)
    actions.perform()
    assert eventually(browser.is_element_present_by_css,
                      args=['div[style*="display: none;"]'])


def upload_file_to_coquelicot(browser, file_path, password):
    """Upload a local file from disk to coquelicot."""
    verify_coquelicot_upload_password(browser, password)
    browser.attach_file('file', file_path)
    interface.submit(browser)
    assert eventually(browser.is_element_present_by_css,
                      args=['#content .url'])
    url_textarea = browser.find_by_css('#content .url textarea').first
    return url_textarea.value


def verify_mediawiki_create_account_link(browser):
    browser.visit(config['DEFAULT']['url'] + '/mediawiki')
    assert eventually(browser.is_element_present_by_id,
                      args=['pt-createaccount'])


def verify_mediawiki_no_create_account_link(browser):
    browser.visit(config['DEFAULT']['url'] + '/mediawiki')
    assert eventually(browser.is_element_not_present_by_id,
                      args=['pt-createaccount'])


def verify_mediawiki_anonymous_reads_edits_link(browser):
    browser.visit(config['DEFAULT']['url'] + '/mediawiki')
    assert eventually(browser.is_element_present_by_id, args=['ca-nstab-main'])


def verify_mediawiki_no_anonymous_reads_edits_link(browser):
    browser.visit(config['DEFAULT']['url'] + '/mediawiki')
    assert eventually(browser.is_element_not_present_by_id,
                      args=['ca-nstab-main'])
    assert eventually(browser.is_element_present_by_id,
                      args=['ca-nstab-special'])


def _login_to_mediawiki(browser, username, password):
    browser.visit(config['DEFAULT']['url'] + '/mediawiki')
    browser.find_by_id('pt-login').click()
    browser.find_by_id('wpName1').fill(username)
    browser.find_by_id('wpPassword1').fill(password)
    with wait_for_page_update(browser):
        browser.find_by_id('wpLoginAttempt').click()


def login_to_mediawiki_with_credentials(browser, username, password):
    _login_to_mediawiki(browser, username, password)
    # Had to put it in the same step because sessions don't
    # persist between steps
    assert eventually(browser.is_element_present_by_id, args=['t-upload'])


def upload_image_mediawiki(browser, username, password, image):
    """Upload an image to MediaWiki. Idempotent."""
    browser.visit(config['DEFAULT']['url'] + '/mediawiki')
    _login_to_mediawiki(browser, username, password)

    # Upload file
    browser.visit(config['DEFAULT']['url'] + '/mediawiki/Special:Upload')
    file_path = os.path.realpath('../static/themes/default/img/' + image)
    browser.attach_file('wpUploadFile', file_path)
    interface.submit(browser, element=browser.find_by_name('wpUpload')[0])


def get_number_of_uploaded_images_in_mediawiki(browser):
    browser.visit(config['DEFAULT']['url'] + '/mediawiki/Special:ListFiles')
    return len(browser.find_by_css('.TablePager_col_img_timestamp'))


def get_uploaded_image_in_mediawiki(browser, image):
    browser.visit(config['DEFAULT']['url'] + '/mediawiki/Special:ListFiles')
    elements = browser.find_link_by_partial_href(image)
    return elements[0].value


def mediawiki_delete_main_page(browser):
    """Delete the mediawiki main page."""
    _login_to_mediawiki(browser, 'admin', 'whatever123')
    browser.visit(
        '{}/mediawiki/index.php?title=Main_Page&action=delete'.format(
            interface.default_url))
    with wait_for_page_update(browser):
        browser.find_by_id('wpConfirmB').first.click()


def mediawiki_has_main_page(browser):
    """Check if mediawiki main page exists."""
    return eventually(_mediawiki_has_main_page, [browser])


def _mediawiki_has_main_page(browser):
    """Check if mediawiki main page exists."""
    browser.visit('{}/mediawiki/Main_Page'.format(interface.default_url))
    content = browser.find_by_id('mw-content-text').first
    return 'This page has been deleted.' not in content.text


def repro_configure(browser):
    """Configure repro."""
    browser.visit(
        '{}/repro/domains.html?domainUri=freedombox.local&domainTlsPort='
        '&action=Add'.format(interface.default_url))


def repro_delete_config(browser):
    """Delete the repro config."""
    browser.visit('{}/repro/domains.html?domainUri=&domainTlsPort='
                  '&action=Remove&remove.freedombox.local=on'.format(
                      interface.default_url))


def repro_is_configured(browser):
    """Check whether repro is configured."""
    return eventually(_repro_is_configured, [browser])


def _repro_is_configured(browser):
    """Check whether repro is configured."""
    browser.visit('{}/repro/domains.html'.format(interface.default_url))
    remove = browser.find_by_name('remove.freedombox.local')
    return bool(remove)


def jsxc_login(browser):
    """Login to JSXC."""
    access_url(browser, 'jsxc')
    browser.find_by_id('jsxc-username').fill(config['DEFAULT']['username'])
    browser.find_by_id('jsxc-password').fill(config['DEFAULT']['password'])
    browser.find_by_id('jsxc-submit').click()
    relogin = browser.find_by_text('relogin')
    if relogin:
        relogin.first.click()
        browser.find_by_id('jsxc_username').fill(config['DEFAULT']['username'])
        browser.find_by_id('jsxc_password').fill(config['DEFAULT']['password'])
        browser.find_by_text('Connect').first.click()


def jsxc_add_contact(browser):
    """Add a contact to JSXC user's roster."""
    system.set_domain_name(browser, 'localhost')
    application.install(browser, 'jsxc')
    jsxc_login(browser)
    new = browser.find_by_text('new contact')
    if new:  # roster is empty
        new.first.click()
        browser.find_by_id('jsxc_username').fill('alice@localhost')
        browser.find_by_text('Add').first.click()


def jsxc_delete_contact(browser):
    """Delete the contact from JSXC user's roster."""
    jsxc_login(browser)
    browser.find_by_css('div.jsxc_more').first.click()
    browser.find_by_text('delete contact').first.click()
    browser.find_by_text('Remove').first.click()


def jsxc_has_contact(browser):
    """Check whether the contact is in JSXC user's roster."""
    jsxc_login(browser)
    contact = browser.find_by_text('alice@localhost')
    return bool(contact)


def transmission_remove_all_torrents(browser):
    """Remove all torrents from transmission."""
    browser.visit(config['DEFAULT']['url'] + '/transmission')
    while True:
        torrents = browser.find_by_css('#torrent_list .torrent')
        if not torrents:
            break

        torrents.first.click()
        eventually(browser.is_element_not_present_by_css,
                   args=['#toolbar-remove.disabled'])
        browser.click_link_by_id('toolbar-remove')
        eventually(browser.is_element_not_present_by_css,
                   args=['#dialog-container[style="display: none;"]'])
        browser.click_link_by_id('dialog_confirm_button')
        eventually(browser.is_element_present_by_css,
                   args=['#toolbar-remove.disabled'])


def transmission_upload_sample_torrent(browser):
    """Upload a sample torrent into transmission."""
    browser.visit(config['DEFAULT']['url'] + '/transmission')
    file_path = os.path.join(
        os.path.dirname(__file__), '..', 'data', 'sample.torrent')
    browser.click_link_by_id('toolbar-open')
    eventually(browser.is_element_not_present_by_css,
               args=['#upload-container[style="display: none;"]'])
    browser.attach_file('torrent_files[]', [file_path])
    browser.click_link_by_id('upload_confirm_button')
    eventually(browser.is_element_present_by_css,
               args=['#torrent_list .torrent'])


def transmission_get_number_of_torrents(browser):
    """Return the number torrents currently in transmission."""
    browser.visit(config['DEFAULT']['url'] + '/transmission')
    return len(browser.find_by_css('#torrent_list .torrent'))


def _deluge_get_active_window_title(browser):
    """Return the title of the currently active window in Deluge."""
    return browser.evaluate_script(
        'Ext.WindowMgr.getActive() ? Ext.WindowMgr.getActive().title : null')


def _deluge_ensure_logged_in(browser):
    """Ensure that password dialog is answered and we can interact."""
    url = config['DEFAULT']['url'] + '/deluge'
    if browser.url != url:
        browser.visit(url)
        time.sleep(1)  # Wait for Ext.js application in initialize

    if _deluge_get_active_window_title(browser) != 'Login':
        return

    browser.find_by_id('_password').first.fill('deluge')
    _deluge_click_active_window_button(browser, 'Login')

    assert eventually(
        lambda: _deluge_get_active_window_title(browser) != 'Login')
    eventually(browser.is_element_not_present_by_css,
               args=['#add.x-item-disabled'], timeout=0.3)


def _deluge_open_connection_manager(browser):
    """Open the connection manager dialog if not already open."""
    title = 'Connection Manager'
    if _deluge_get_active_window_title(browser) == title:
        return

    browser.find_by_css('button.x-deluge-connection-manager').first.click()
    eventually(lambda: _deluge_get_active_window_title(browser) == title)


def _deluge_ensure_daemon_started(browser):
    """Start the deluge daemon if it is not started."""
    _deluge_open_connection_manager(browser)

    browser.find_by_xpath('//em[text()="127.0.0.1:58846"]').first.click()

    if browser.is_element_present_by_xpath('//button[text()="Stop Daemon"]'):
        return

    browser.find_by_xpath('//button[text()="Start Daemon"]').first.click()

    assert eventually(browser.is_element_present_by_xpath,
                      args=['//button[text()="Stop Daemon"]'])


def _deluge_ensure_connected(browser):
    """Type the connection password if required and start Deluge daemon."""
    _deluge_ensure_logged_in(browser)

    # If the add button is enabled, we are already connected
    if not browser.is_element_present_by_css('#add.x-item-disabled'):
        return

    _deluge_ensure_daemon_started(browser)

    if browser.is_element_present_by_xpath('//button[text()="Disconnect"]'):
        _deluge_click_active_window_button(browser, 'Close')
    else:
        _deluge_click_active_window_button(browser, 'Connect')

    assert eventually(browser.is_element_not_present_by_css,
                      args=['#add.x-item-disabled'])


def deluge_remove_all_torrents(browser):
    """Remove all torrents from deluge."""
    _deluge_ensure_connected(browser)

    while browser.find_by_css('#torrentGrid .torrent-name'):
        browser.find_by_css('#torrentGrid .torrent-name').first.click()

        # Click remove toolbar button
        browser.find_by_id('remove').first.click()

        # Remove window shows up
        assert eventually(
            lambda: _deluge_get_active_window_title(browser) == 'Remove Torrent'
        )

        _deluge_click_active_window_button(browser, 'Remove With Data')

        # Remove window disappears
        assert eventually(lambda: not _deluge_get_active_window_title(browser))


def _deluge_get_active_window_id(browser):
    """Return the ID of the currently active window."""
    return browser.evaluate_script('Ext.WindowMgr.getActive().id')


def _deluge_click_active_window_button(browser, button_text):
    """Click an action button in the active window."""
    browser.execute_script('''
        active_window = Ext.WindowMgr.getActive();
        active_window.buttons.forEach(function (button) {{
            if (button.text == "{button_text}")
                button.btnEl.dom.click()
        }})'''.format(button_text=button_text))


def deluge_upload_sample_torrent(browser):
    """Upload a sample torrent into deluge."""
    _deluge_ensure_connected(browser)

    number_of_torrents = _deluge_get_number_of_torrents(browser)

    # Click add toolbar button
    browser.find_by_id('add').first.click()

    # Add window appears
    eventually(
        lambda: _deluge_get_active_window_title(browser) == 'Add Torrents')

    browser.find_by_css('button.x-deluge-add-file').first.click()

    # Add from file window appears
    eventually(
        lambda: _deluge_get_active_window_title(browser) == 'Add from File')

    # Attach file
    file_path = os.path.join(
        os.path.dirname(__file__), '..', 'data', 'sample.torrent')
    browser.attach_file('file', file_path)

    # Click Add
    _deluge_click_active_window_button(browser, 'Add')

    eventually(
        lambda: _deluge_get_active_window_title(browser) == 'Add Torrents')

    # Click Add
    time.sleep(1)
    _deluge_click_active_window_button(browser, 'Add')

    eventually(
        lambda: _deluge_get_number_of_torrents(browser) > number_of_torrents)


def _deluge_get_number_of_torrents(browser):
    """Return the number torrents currently in deluge."""
    return len(browser.find_by_css('#torrentGrid .torrent-name'))


def deluge_get_number_of_torrents(browser):
    """Return the number torrents currently in deluge."""
    _deluge_ensure_connected(browser)

    return _deluge_get_number_of_torrents(browser)
