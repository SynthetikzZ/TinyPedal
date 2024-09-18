#  TinyPedal is an open-source overlay application for racing simulation.
#  Copyright (C) 2022-2024 TinyPedal developers, see contributors.md file
#
#  This file is part of TinyPedal.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Tray icon
"""

from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QSystemTrayIcon, QMenu

from ..const import APP_NAME, VERSION, APP_ICON
from .menu import OverlayMenu


class TrayIcon(QSystemTrayIcon):
    """System tray icon

    Activate overlay widgets via system tray icon.
    """

    def __init__(self, master, config: object):
        super().__init__()
        self.cfg = config
        self.master = master

        # Config tray icon
        self.setIcon(QIcon(APP_ICON))
        self.setToolTip(f"{APP_NAME} v{VERSION}")
        self.activated.connect(self.show_config_via_doubleclick)

        # Create tray menu
        menu = QMenu()

        # Loaded preset name
        self.loaded_preset = QAction("", self)
        self.loaded_preset.setDisabled(True)
        menu.addAction(self.loaded_preset)
        menu.addSeparator()

        # Overlay menu
        OverlayMenu(self.master, menu)
        menu.addSeparator()

        # Config
        app_config = QAction("Config", self)
        app_config.triggered.connect(self.show_config)
        menu.addAction(app_config)
        menu.addSeparator()

        # Quit
        app_quit = QAction("Quit", self)
        app_quit.triggered.connect(self.master.quit_app)
        menu.addAction(app_quit)

        self.setContextMenu(menu)
        menu.aboutToShow.connect(self.refresh_menu)

    def show_config(self):
        """Show config window"""
        self.master.showNormal()
        self.master.activateWindow()

    def show_config_via_doubleclick(self, active_reason):
        """Show config window via doubleclick"""
        if active_reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_config()

    def refresh_menu(self):
        """Refresh menu"""
        self.loaded_preset.setText(
            self.format_preset_name(self.cfg.filename.last_setting))

    @staticmethod
    def format_preset_name(filename: str) -> str:
        """Format preset name"""
        loaded_preset = filename[:-5]
        if len(loaded_preset) > 16:
            loaded_preset = f"{loaded_preset[:16]}..."
        return loaded_preset
