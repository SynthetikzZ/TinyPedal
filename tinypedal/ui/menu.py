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
Menu
"""

import os

from PySide6.QtGui import QDesktopServices, QAction
from PySide6.QtWidgets import QMenu, QMessageBox

from ..const import PATH_DELTABEST, PATH_ENERGY, PATH_FUEL, PATH_SECTORBEST, PATH_TRACKMAP
from ..setting import cfg
from ..api_control import api
from ..overlay_control import octrl
from .about import About
from .config import FontConfig, UserConfig
from .log_info import LogInfo
from .fuel_calculator import FuelCalculator
from .heatmap_editor import HeatmapEditor
from .vehicle_brand_editor import VehicleBrandEditor
from .vehicle_class_editor import VehicleClassEditor


class OverlayMenu(QMenu):
    """Overlay menu, shared between main & tray menu"""

    def __init__(self, master, menu):
        super().__init__(master)
        self.master = master

        # Lock overlay
        self.overlay_lock = QAction("Lock overlay", self)
        self.overlay_lock.setCheckable(True)
        self.overlay_lock.setChecked(cfg.overlay["fixed_position"])
        self.overlay_lock.triggered.connect(self.is_locked)
        menu.addAction(self.overlay_lock)

        # Auto hide
        self.overlay_hide = QAction("Auto hide", self)
        self.overlay_hide.setCheckable(True)
        self.overlay_hide.setChecked(cfg.overlay["auto_hide"])
        self.overlay_hide.triggered.connect(self.is_hidden)
        menu.addAction(self.overlay_hide)

        # Grid move
        self.overlay_grid = QAction("Grid move", self)
        self.overlay_grid.setCheckable(True)
        self.overlay_grid.setChecked(cfg.overlay["enable_grid_move"])
        self.overlay_grid.triggered.connect(self.has_grid)
        menu.addAction(self.overlay_grid)

        # Reload preset
        reload_preset = QAction("Reload", self)
        reload_preset.triggered.connect(self.master.reload_preset)
        menu.addAction(reload_preset)
        menu.addSeparator()

        # Restart API
        restart_api = QAction("Restart API", self)
        restart_api.triggered.connect(self.master.restart_api)
        menu.addAction(restart_api)
        menu.addSeparator()

        # Reset submenu
        menu_reset_data = menu.addMenu("Reset data")
        ResetDataMenu(self.master, menu_reset_data)
        menu.addSeparator()

        # Refresh menu
        menu.aboutToShow.connect(self.refresh_overlay_menu)

    def refresh_overlay_menu(self):
        """Refresh overlay menu"""
        self.overlay_lock.setChecked(cfg.overlay["fixed_position"])
        self.overlay_hide.setChecked(cfg.overlay["auto_hide"])
        self.overlay_grid.setChecked(cfg.overlay["enable_grid_move"])

    @staticmethod
    def is_locked():
        """Check lock state"""
        octrl.overlay_lock.toggle()

    @staticmethod
    def is_hidden():
        """Check hide state"""
        octrl.overlay_hide.toggle()

    @staticmethod
    def has_grid():
        """Check hide state"""
        octrl.overlay_grid.toggle()


class ResetDataMenu(QMenu):
    """Reset user data menu"""

    def __init__(self, master, menu):
        super().__init__(master)
        self.master = master

        # Deltabest
        reset_deltabest = QAction("Deltabest", self)
        reset_deltabest.triggered.connect(self.reset_deltabest)
        menu.addAction(reset_deltabest)

        # Energy delta
        reset_energydelta = QAction("Energy delta", self)
        reset_energydelta.triggered.connect(self.reset_energydelta)
        menu.addAction(reset_energydelta)

        # Fuel delta
        reset_fueldelta = QAction("Fuel delta", self)
        reset_fueldelta.triggered.connect(self.reset_fueldelta)
        menu.addAction(reset_fueldelta)

        # Sector best
        reset_sectorbest = QAction("Sector best", self)
        reset_sectorbest.triggered.connect(self.reset_sectorbest)
        menu.addAction(reset_sectorbest)

        # Track map
        reset_trackmap = QAction("Track map", self)
        reset_trackmap.triggered.connect(self.reset_trackmap)
        menu.addAction(reset_trackmap)

    def reset_deltabest(self):
        """Reset deltabest data"""
        self.__confirmation(
            "deltabest", "csv", PATH_DELTABEST, api.read.check.combo_id())

    def reset_energydelta(self):
        """Reset energy delta data"""
        self.__confirmation(
            "energy delta", "energy", PATH_ENERGY, api.read.check.combo_id())

    def reset_fueldelta(self):
        """Reset fuel delta data"""
        self.__confirmation(
            "fuel delta", "fuel", PATH_FUEL, api.read.check.combo_id())

    def reset_sectorbest(self):
        """Reset sector best data"""
        self.__confirmation(
            "sector best", "sector", PATH_SECTORBEST, api.read.check.combo_id())

    def reset_trackmap(self):
        """Reset trackmap data"""
        self.__confirmation(
            "track map", "svg", PATH_TRACKMAP, api.read.check.track_id())

    def __confirmation(self, data_type: str, file_ext: str, file_path: str, combo_name: str):
        """Message confirmation"""
        # Check if on track
        if api.state:
            QMessageBox.warning(
                self.master, "Error",
                "Cannot reset data while on track.")
            return None
        # Check if file exist
        if not os.path.exists(f"{file_path}{combo_name}.{file_ext}"):
            QMessageBox.warning(
                self.master, "Error",
                f"No {data_type} data found.<br><br>You can only reset data from active session.")
            return None
        # Confirm reset
        message_text = (
            f"Are you sure you want to reset {data_type} data for<br>"
            f"<b>{combo_name}</b>"
            " ?<br><br>This cannot be undone!"
        )
        delete_msg = QMessageBox.question(
            self.master, f"Reset {data_type.title()}", message_text,
            buttons=QMessageBox.Yes | QMessageBox.No)
        if delete_msg == QMessageBox.Yes:
            os.remove(f"{file_path}{combo_name}.{file_ext}")
            QMessageBox.information(
                self.master, f"Reset {data_type.title()}",
                f"{data_type.capitalize()} data has been reset for<br><b>{combo_name}</b>")
            combo_name = None
        return None


class ConfigMenu(QMenu):
    """Config menu"""

    def __init__(self, master, menu):
        super().__init__(master)
        self.master = master

        config_units = QAction("Units and symbols", self)
        config_units.triggered.connect(self.open_config_units)
        menu.addAction(config_units)

        config_font = QAction("Global font override", self)
        config_font.triggered.connect(self.open_config_font)
        menu.addAction(config_font)

        config_sharedmem = QAction("Shared memory API", self)
        config_sharedmem.triggered.connect(self.open_config_sharedmemory)
        menu.addAction(config_sharedmem)

        config_compat = QAction("Compatibility", self)
        config_compat.triggered.connect(self.open_config_compatibility)
        menu.addAction(config_compat)

    def open_config_font(self):
        """Config global font"""
        _dialog = FontConfig(self.master)
        _dialog.open()

    def open_config_units(self):
        """Config display units"""
        _dialog = UserConfig(self.master, "units", "misc")
        _dialog.open()

    def open_config_sharedmemory(self):
        """Config sharedmemory"""
        _dialog = UserConfig(self.master, "shared_memory_api", "api")
        _dialog.open()

    def open_config_compatibility(self):
        """Config compatibility"""
        _dialog = UserConfig(self.master, "compatibility", "misc")
        _dialog.open()


class ToolsMenu(QMenu):
    """Tools menu"""

    def __init__(self, master, menu):
        super().__init__(master)
        self.master = master

        editor_fuel = QAction("Fuel calculator", self)
        editor_fuel.triggered.connect(self.open_editor_fuel)
        menu.addAction(editor_fuel)

        editor_heatmap = QAction("Heatmap editor", self)
        editor_heatmap.triggered.connect(self.open_editor_heatmap)
        menu.addAction(editor_heatmap)

        editor_brands = QAction("Vehicle brand editor", self)
        editor_brands.triggered.connect(self.open_editor_brands)
        menu.addAction(editor_brands)

        editor_classes = QAction("Vehicle class editor", self)
        editor_classes.triggered.connect(self.open_editor_classes)
        menu.addAction(editor_classes)

    def open_editor_fuel(self):
        """Fuel calculator"""
        _dialog = FuelCalculator(self.master)
        _dialog.show()

    def open_editor_heatmap(self):
        """Edit heatmap preset"""
        _dialog = HeatmapEditor(self.master)
        _dialog.open()

    def open_editor_brands(self):
        """Edit brands preset"""
        _dialog = VehicleBrandEditor(self.master)
        _dialog.open()

    def open_editor_classes(self):
        """Edit classes preset"""
        _dialog = VehicleClassEditor(self.master)
        _dialog.open()


class WindowMenu(QMenu):
    """Window menu"""

    def __init__(self, master, menu):
        super().__init__(master)

        # Show at startup
        self.show_window = QAction("Show at startup", self)
        self.show_window.setCheckable(True)
        self.show_window.setChecked(cfg.application["show_at_startup"])
        self.show_window.triggered.connect(self.is_show_at_startup)
        menu.addAction(self.show_window)

        # Minimize to tray
        self.minimize_to_tray = QAction("Minimize to tray", self)
        self.minimize_to_tray.setCheckable(True)
        self.minimize_to_tray.setChecked(cfg.application["minimize_to_tray"])
        self.minimize_to_tray.triggered.connect(self.is_minimize_to_tray)
        menu.addAction(self.minimize_to_tray)

        # Remember position
        self.remember_position = QAction("Remember position", self)
        self.remember_position.setCheckable(True)
        self.remember_position.setChecked(cfg.application["remember_position"])
        self.remember_position.triggered.connect(self.is_remember_position)
        menu.addAction(self.remember_position)

        # Refresh menu
        menu.aboutToShow.connect(self.refresh_menu)

    def refresh_menu(self):
        """Refresh window menu"""
        self.show_window.setChecked(cfg.application["show_at_startup"])
        self.minimize_to_tray.setChecked(cfg.application["minimize_to_tray"])
        self.remember_position.setChecked(cfg.application["remember_position"])

    @staticmethod
    def is_show_at_startup():
        """Toggle config window startup state"""
        if not cfg.application["show_at_startup"]:
            cfg.application["show_at_startup"] = True
        else:
            cfg.application["show_at_startup"] = False
        cfg.save()

    @staticmethod
    def is_minimize_to_tray():
        """Toggle minimize to tray state"""
        if not cfg.application["minimize_to_tray"]:
            cfg.application["minimize_to_tray"] = True
        else:
            cfg.application["minimize_to_tray"] = False
        cfg.save()

    @staticmethod
    def is_remember_position():
        """Toggle config window remember position state"""
        if not cfg.application["remember_position"]:
            cfg.application["remember_position"] = True
        else:
            cfg.application["remember_position"] = False
        cfg.save()


class HelpMenu(QMenu):
    """Help menu"""

    def __init__(self, master, menu):
        super().__init__(master)
        self.master = master

        app_guide = QAction("User guide", self)
        app_guide.triggered.connect(self.open_user_guide)
        menu.addAction(app_guide)

        app_faq = QAction("FAQ", self)
        app_faq.triggered.connect(self.open_faq)
        menu.addAction(app_faq)

        app_log = QAction("Show log", self)
        app_log.triggered.connect(self.show_log)
        menu.addAction(app_log)

        menu.addSeparator()
        app_about = QAction("About", self)
        app_about.triggered.connect(self.show_about)
        menu.addAction(app_about)

    def show_about(self):
        """Show about"""
        _dialog = About(self.master)
        _dialog.show()

    def show_log(self):
        """Show log"""
        _dialog = LogInfo(self.master)
        _dialog.show()

    def open_user_guide(self):
        """Open user guide link"""
        QDesktopServices.openUrl(
            "https://github.com/s-victor/TinyPedal/wiki/User-Guide"
        )

    def open_faq(self):
        """Open FAQ link"""
        QDesktopServices.openUrl(
            "https://github.com/s-victor/TinyPedal/wiki/Frequently-Asked-Questions"
        )
