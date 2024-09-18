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
Tyre temperature Widget
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel

from .. import calculation as calc
from .. import heatmap as hmp
from ..api_control import api
from ._base import Overlay

WIDGET_NAME = "tyre_temperature"


class Draw(Overlay):
    """Draw widget"""

    def __init__(self, config):
        # Assign base setting
        Overlay.__init__(self, config, WIDGET_NAME)

        # Config font
        font_m = self.get_font_metrics(
            self.config_font(self.wcfg["font_name"], self.wcfg["font_size"]))

        # Config variable
        text_def = "n/a"
        bar_padx = round(self.wcfg["font_size"] * self.wcfg["bar_padding"]) * 2
        bar_gap = self.wcfg["bar_gap"]
        inner_gap = self.wcfg["inner_gap"]
        self.leading_zero = min(max(self.wcfg["leading_zero"], 1), 3)
        self.sign_text = "°" if self.wcfg["show_degree_sign"] else ""
        self.tyre_compound_string = self.cfg.units["tyre_compound_symbol"].ljust(20, "?")

        if self.cfg.units["temperature_unit"] == "Fahrenheit":
            text_width = 4 + len(self.sign_text)
        else:
            text_width = 3 + len(self.sign_text)

        self.bar_width_temp = f"min-width: {font_m.width * text_width + bar_padx}px;"

        # Base style
        self.heatmap = hmp.load_heatmap(self.wcfg["heatmap_name"], "tyre_default")
        self.setStyleSheet(
            f"font-family: {self.wcfg['font_name']};"
            f"font-size: {self.wcfg['font_size']}px;"
            f"font-weight: {self.wcfg['font_weight']};"
        )

        # Create layout
        layout = QGridLayout()
        layout.setContentsMargins(0,0,0,0)  # remove border
        layout_stemp = QGridLayout()
        layout_itemp = QGridLayout()
        layout_stemp.setSpacing(inner_gap)
        layout_itemp.setSpacing(inner_gap)
        layout.setSpacing(bar_gap)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        column_stemp = self.wcfg["column_index_surface"]
        column_itemp = self.wcfg["column_index_innerlayer"]

        # Tyre compound
        if self.wcfg["show_tyre_compound"]:
            bar_style_tcmpd = (
                f"color: {self.wcfg['font_color_tyre_compound']};"
                f"background: {self.wcfg['bkg_color_tyre_compound']};"
                f"min-width: {font_m.width + bar_padx}px;"
            )
            self.bar_tcmpd_f = QLabel("-")
            self.bar_tcmpd_f.setAlignment(Qt.AlignCenter)
            self.bar_tcmpd_f.setStyleSheet(bar_style_tcmpd)
            self.bar_tcmpd_r = QLabel("-")
            self.bar_tcmpd_r.setAlignment(Qt.AlignCenter)
            self.bar_tcmpd_r.setStyleSheet(bar_style_tcmpd)
            layout_stemp.addWidget(self.bar_tcmpd_f, 0, 4)
            layout_stemp.addWidget(self.bar_tcmpd_r, 1, 4)

            if self.wcfg["show_innerlayer"]:
                bar_blank_1 = QLabel("")
                bar_blank_1.setStyleSheet(bar_style_tcmpd)
                bar_blank_2 = QLabel("")
                bar_blank_2.setStyleSheet(bar_style_tcmpd)
                layout_itemp.addWidget(bar_blank_1, 0, 4)
                layout_itemp.addWidget(bar_blank_2, 1, 4)

        # Tyre temperature
        self.stemp_set = ("stemp_fl", "stemp_fr", "stemp_rl", "stemp_rr")
        self.itemp_set = ("itemp_fl", "itemp_fr", "itemp_rl", "itemp_rr")

        bar_style_stemp = (
            f"color: {self.wcfg['font_color_surface']};"
            f"background: {self.wcfg['bkg_color_surface']};"
            f"{self.bar_width_temp}"
        )
        bar_style_itemp = (
            f"color: {self.wcfg['font_color_innerlayer']};"
            f"background: {self.wcfg['bkg_color_innerlayer']};"
            f"{self.bar_width_temp}"
        )

        if self.wcfg["show_inner_center_outer"]:
            for suffix in self.stemp_set:
                for idx in range(3):
                    setattr(self, f"bar_{suffix}_{idx}", QLabel(text_def))
                    getattr(self, f"bar_{suffix}_{idx}").setAlignment(Qt.AlignCenter)
                    getattr(self, f"bar_{suffix}_{idx}").setStyleSheet(bar_style_stemp)
                    if suffix == "stemp_fl":  # 2 1 0
                        layout_stemp.addWidget(
                            getattr(self, f"bar_{suffix}_{idx}"), 0, idx)
                    if suffix == "stemp_fr":  # 7 8 9
                        layout_stemp.addWidget(
                            getattr(self, f"bar_{suffix}_{idx}"), 0, 7 + idx)
                    if suffix == "stemp_rl":  # 2 1 0
                        layout_stemp.addWidget(
                            getattr(self, f"bar_{suffix}_{idx}"), 1, idx)
                    if suffix == "stemp_rr":  # 7 8 9
                        layout_stemp.addWidget(
                            getattr(self, f"bar_{suffix}_{idx}"), 1, 7 + idx)

            if self.wcfg["show_innerlayer"]:
                for suffix in self.itemp_set:
                    for idx in range(3):
                        setattr(self, f"bar_{suffix}_{idx}", QLabel(text_def))
                        getattr(self, f"bar_{suffix}_{idx}").setAlignment(Qt.AlignCenter)
                        getattr(self, f"bar_{suffix}_{idx}").setStyleSheet(bar_style_itemp)
                        if suffix == "itemp_fl":  # 2 1 0
                            layout_itemp.addWidget(
                                getattr(self, f"bar_{suffix}_{idx}"), 0, idx)
                        if suffix == "itemp_fr":  # 7 8 9
                            layout_itemp.addWidget(
                                getattr(self, f"bar_{suffix}_{idx}"), 0, 7 + idx)
                        if suffix == "itemp_rl":  # 2 1 0
                            layout_itemp.addWidget(
                                getattr(self, f"bar_{suffix}_{idx}"), 1, idx)
                        if suffix == "itemp_rr":  # 7 8 9
                            layout_itemp.addWidget(
                                getattr(self, f"bar_{suffix}_{idx}"), 1, 7 + idx)

        else:
            for suffix in self.stemp_set:
                setattr(self, f"bar_{suffix}", QLabel(text_def))
                getattr(self, f"bar_{suffix}").setAlignment(Qt.AlignCenter)
                getattr(self, f"bar_{suffix}").setStyleSheet(bar_style_stemp)
                if suffix == "stemp_fl":  # 0
                    layout_stemp.addWidget(
                        getattr(self, f"bar_{suffix}"), 0, 0)
                if suffix == "stemp_fr":  # 9
                    layout_stemp.addWidget(
                        getattr(self, f"bar_{suffix}"), 0, 9)
                if suffix == "stemp_rl":  # 0
                    layout_stemp.addWidget(
                        getattr(self, f"bar_{suffix}"), 1, 0)
                if suffix == "stemp_rr":  # 9
                    layout_stemp.addWidget(
                        getattr(self, f"bar_{suffix}"), 1, 9)

            if self.wcfg["show_innerlayer"]:
                for suffix in self.itemp_set:
                    setattr(self, f"bar_{suffix}", QLabel(text_def))
                    getattr(self, f"bar_{suffix}").setAlignment(Qt.AlignCenter)
                    getattr(self, f"bar_{suffix}").setStyleSheet(bar_style_itemp)
                    if suffix == "itemp_fl":  # 0
                        layout_itemp.addWidget(
                            getattr(self, f"bar_{suffix}"), 0, 0)
                    if suffix == "itemp_fr":  # 9
                        layout_itemp.addWidget(
                            getattr(self, f"bar_{suffix}"), 0, 9)
                    if suffix == "itemp_rl":  # 0
                        layout_itemp.addWidget(
                            getattr(self, f"bar_{suffix}"), 1, 0)
                    if suffix == "itemp_rr":  # 9
                        layout_itemp.addWidget(
                            getattr(self, f"bar_{suffix}"), 1, 9)

        # Set layout
        if self.wcfg["layout"] == 0:
            # Vertical layout
            layout.addLayout(layout_stemp, column_stemp, 0)
            if self.wcfg["show_innerlayer"]:
                layout.addLayout(layout_itemp, column_itemp, 0)
        else:
            # Horizontal layout
            layout.addLayout(layout_stemp, 0, column_stemp)
            if self.wcfg["show_innerlayer"]:
                layout.addLayout(layout_itemp, 0, column_itemp)
        self.setLayout(layout)

        # Last data
        self.last_tcmpd = [None] * 2
        if self.wcfg["show_inner_center_outer"]:
            self.last_stemp = [[-273.15] * 3 for _ in range(4)]
            self.last_itemp = [[-273.15] * 3 for _ in range(4)]
        else:
            self.last_stemp = [-273.15] * 4
            self.last_itemp = [-273.15] * 4

        # Set widget state & start update
        self.set_widget_state()

    def timerEvent(self, event):
        """Update when vehicle on track"""
        if api.state:

            # Tyre compound
            if self.wcfg["show_tyre_compound"]:
                tcmpd = [self.tyre_compound_string[idx] for idx in api.read.tyre.compound()]
                self.update_tcmpd(tcmpd, self.last_tcmpd)
                self.last_tcmpd = tcmpd

            # Inner, center, outer mode
            if self.wcfg["show_inner_center_outer"]:
                # Surface temperature
                stemp = api.read.tyre.surface_temperature()
                for patch_idx in range(3):  # 0 1 2
                    for tyre_idx, suffix in enumerate(self.stemp_set):
                        self.update_stemp(
                            f"{suffix}_{patch_idx}",
                            stemp[tyre_idx][patch_idx],
                            self.last_stemp[tyre_idx][patch_idx]
                        )
                self.last_stemp = stemp

                # Inner layer temperature
                if self.wcfg["show_innerlayer"]:
                    itemp = api.read.tyre.inner_temperature()
                    for patch_idx in range(3):
                        for tyre_idx, suffix in enumerate(self.itemp_set):
                            self.update_itemp(
                                f"{suffix}_{patch_idx}",
                                itemp[tyre_idx][patch_idx],
                                self.last_itemp[tyre_idx][patch_idx]
                            )
                    self.last_itemp = itemp
            # Average mode
            else:
                # Surface temperature
                stemp = tuple(map(calc.mean, api.read.tyre.surface_temperature()))
                for patch_idx, suffix in enumerate(self.stemp_set):
                    self.update_stemp(suffix, stemp[patch_idx], self.last_stemp[patch_idx])
                self.last_stemp = stemp
                # Inner layer temperature
                if self.wcfg["show_innerlayer"]:
                    itemp = tuple(map(calc.mean, api.read.tyre.inner_temperature()))
                    for patch_idx, suffix in enumerate(self.itemp_set):
                        self.update_itemp(suffix, itemp[patch_idx], self.last_itemp[patch_idx])
                    self.last_itemp = itemp

    # GUI update methods
    def update_stemp(self, suffix, curr, last):
        """Tyre surface temperature"""
        if round(curr) != round(last):
            if self.wcfg["swap_style"]:
                color = (f"color: {self.wcfg['font_color_surface']};"
                         f"background: {hmp.select_color(self.heatmap, curr)};")
            else:
                color = (f"color: {hmp.select_color(self.heatmap, curr)};"
                         f"background: {self.wcfg['bkg_color_surface']};")

            getattr(self, f"bar_{suffix}").setText(
                f"{self.temp_units(curr):0{self.leading_zero}.0f}{self.sign_text}")

            getattr(self, f"bar_{suffix}").setStyleSheet(f"{color}{self.bar_width_temp}")

    def update_itemp(self, suffix, curr, last):
        """Tyre inner temperature"""
        if round(curr) != round(last):
            if self.wcfg["swap_style"]:
                color = (f"color: {self.wcfg['font_color_innerlayer']};"
                         f"background: {hmp.select_color(self.heatmap, curr)};")
            else:
                color = (f"color: {hmp.select_color(self.heatmap, curr)};"
                         f"background: {self.wcfg['bkg_color_innerlayer']};")

            getattr(self, f"bar_{suffix}").setText(
                f"{self.temp_units(curr):0{self.leading_zero}.0f}{self.sign_text}")

            getattr(self, f"bar_{suffix}").setStyleSheet(f"{color}{self.bar_width_temp}")

    def update_tcmpd(self, curr, last):
        """Tyre compound"""
        if curr != last:
            self.bar_tcmpd_f.setText(curr[0])
            self.bar_tcmpd_r.setText(curr[1])

    # Additional methods
    def temp_units(self, value):
        """Temperature units"""
        if self.cfg.units["temperature_unit"] == "Fahrenheit":
            return calc.celsius2fahrenheit(value)
        return value
