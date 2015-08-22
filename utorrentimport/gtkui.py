#
# gtkui.py
#
# Copyright (C) 2009 Laharah <laharah22+deluge@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

import gtk

from deluge.log import LOG as log
from deluge.ui.client import client
from deluge.plugins.pluginbase import GtkPluginBase
import deluge.component as component
import deluge.common
from twisted.internet import defer

from core import DEFAULT_PREFS
from common import get_resource


class GtkUI(GtkPluginBase):
    def enable(self):
        self.glade = gtk.glade.XML(get_resource("config.glade"))

        component.get("Preferences").add_page("uTorrentImport", self.glade.get_widget("prefs_box"))
        component.get("PluginManager").register_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").register_hook("on_show_prefs", self.on_show_prefs)

    def disable(self):
        component.get("Preferences").remove_page("uTorrentImport")
        component.get("PluginManager").deregister_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").deregister_hook("on_show_prefs", self.on_show_prefs)

    def on_apply_prefs(self):
        log.debug("applying prefs for uTorrentImport")
        self.config.update(self.gather_settings())
        client.utorrentimport.set_config(self.config)

    @defer.inlineCallbacks
    def on_show_prefs(self):
        self.use_wine_mappings = self.glade.get_widget('use_wine_mappings')
        self.recheck_all = self.glade.get_widget('recheck_all')
        self.resume_dat_entry = self.glade.get_widget('resume_dat_entry')
        log.debug("showing utorrentimport prefs")
        self.config = yield client.utorrentimport.get_config()
        log.debug('got config: {0}'.format(self.config))
        self.populate_config(self.config)
        signal_dictionary = {'on_import_button_clicked': self.on_import_button_clicked}

        self.glade.signal_autoconnect(signal_dictionary)
        log.debug('utorrentimport: signals hooked!')
        if not self.config['previous_resume_dat_path']:
            default_resume = yield client.utorrentimport.get_default_resume_path()
            log.debug('utorrentimport: got resume.dat path!')
            if default_resume:
                self.resume_dat_entry.set_text(default_resume)

    @defer.inlineCallbacks
    def on_import_button_clicked(self, button):
        self.toggle_button(button)
        settings = self.gather_settings()
        log.debug('sending import command...')
        result = yield client.utorrentimport.begin_import(
            settings['previous_resume_dat_path'],
            use_wine_mappings=settings['use_wine_mappings'],
            recheck_all=settings['recheck_all'])
        log.debug('recieved result! {0}'.format(result))
        self.toggle_button(button)

    def toggle_button(self, button):
        if button.get_sensitive():
            button.set_sensitive(False)
        else:
            button.set_sensitive(True)

    def populate_config(self, config):
        """callback for on show_prefs"""
        self.use_wine_mappings.set_active(config['use_wine_mappings'])
        self.recheck_all.set_active(config['recheck_all'])
        self.resume_dat_entry.set_text(config['previous_resume_dat_path'])

    def gather_settings(self):
        return {
            'use_wine_mappings': self.use_wine_mappings.get_active(),
            'recheck_all': self.recheck_all.get_active(),
            'previous_resume_dat_path': self.resume_dat_entry.get_text()
        }
