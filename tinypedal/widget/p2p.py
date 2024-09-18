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
P2P Widget
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel

from ..api_control import api
from ..module_info import minfo
from ._base import Overlay

WIDGET_NAME = "p2p"


class Draw(Overlay):
    """Draw widget"""

    def __init__(self, config):
        # Assign base setting
        Overlay.__init__(self, config, WIDGET_NAME)

        # Config font
        font_m = self.get_font_metrics(
            self.config_font(self.wcfg["font_name"], self.wcfg["font_size"]))

        # Config variable
        bar_padx = round(self.wcfg["font_size"] * self.wcfg["bar_padding"]) * 2
        bar_gap = self.wcfg["bar_gap"]
        self.bar_width_battery = f"min-width: {font_m.width * 3 + bar_padx}px;"
        self.bar_width_timer = f"min-width: {font_m.width * 4 + bar_padx}px;"

        # Base style
        self.setStyleSheet(
            f"font-family: {self.wcfg['font_name']};"
            f"font-size: {self.wcfg['font_size']}px;"
            f"font-weight: {self.wcfg['font_weight']};"
        )

        # Create layout
        layout = QGridLayout()
        layout.setContentsMargins(0,0,0,0)  # remove border
        layout.setSpacing(bar_gap)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        column_bc = self.wcfg["column_index_battery_charge"]
        column_at = self.wcfg["column_index_activation_timer"]

        # Battery charge
        if self.wcfg["show_battery_charge"]:
            self.bar_battery_charge = QLabel("P2P")
            self.bar_battery_charge.setAlignment(Qt.AlignCenter)
            self.bar_battery_charge.setStyleSheet(
                f"color: {self.wcfg['font_color_battery_charge']};"
                f"background: {self.wcfg['bkg_color_battery_charge']};"
                f"{self.bar_width_battery}"
            )

        # Activation timer
        if self.wcfg["show_activation_timer"]:
            self.bar_active_timer = QLabel("0.00")
            self.bar_active_timer.setAlignment(Qt.AlignCenter)
            self.bar_active_timer.setStyleSheet(
                f"color: {self.wcfg['font_color_activation_timer']};"
                f"background: {self.wcfg['bkg_color_activation_timer']};"
                f"{self.bar_width_timer}"
            )

        # Set layout
        if self.wcfg["show_battery_charge"]:
            layout.addWidget(self.bar_battery_charge, 0, column_bc)
        if self.wcfg["show_activation_timer"]:
            layout.addWidget(self.bar_active_timer, 0, column_at)
        self.setLayout(layout)

        # Last data
        self.last_battery_charge = None
        self.last_active_timer = None

        # Set widget state & start update
        self.set_widget_state()

    def timerEvent(self, event):
        """Update when vehicle on track"""
        if api.state:

            # Battery charge
            if self.wcfg["show_battery_charge"]:
                alt_active_state = (
                    api.read.engine.gear() >= self.wcfg["activation_threshold_gear"] and
                    api.read.vehicle.speed() * 3.6 > self.wcfg["activation_threshold_speed"] and
                    api.read.input.throttle_raw() >= self.wcfg["activation_threshold_throttle"] and
                    minfo.hybrid.motorState
                )
                battery_charge = (
                    minfo.hybrid.batteryCharge,
                    minfo.hybrid.motorState,
                    alt_active_state,
                    minfo.hybrid.motorActiveTimer,
                    minfo.hybrid.motorInActiveTimer
                )
                self.update_battery_charge(battery_charge, self.last_battery_charge)
                self.last_battery_charge = battery_charge

            # Activation timer
            if self.wcfg["show_activation_timer"]:
                active_timer = (
                    minfo.hybrid.motorActiveTimer,
                    minfo.hybrid.motorState
                )
                self.update_active_timer(active_timer, self.last_active_timer)
                self.last_active_timer = active_timer

    # GUI update methods
    def update_battery_charge(self, curr, last):
        """Battery charge"""
        if curr != last:
            # State = active
            if curr[1] == 2:
                bgcolor = self.wcfg["bkg_color_battery_drain"]
            # State = regen
            elif curr[1] == 3:
                bgcolor = self.wcfg["bkg_color_battery_regen"]
            # alt_active_state True, active_timer, inactive_timer
            elif (curr[2] and
                  curr[4] >= self.wcfg["minimum_activation_time_delay"] and
                  curr[3] < self.wcfg["maximum_activation_time_per_lap"] - 0.05):
                bgcolor = self.wcfg["bkg_color_battery_charge"]
            else:
                bgcolor = self.wcfg["bkg_color_inactive"]

            if curr[0] < 99.5:
                format_text = f"±{curr[0]:02.0f}"
            else:
                format_text = "MAX"

            self.bar_battery_charge.setText(format_text)
            self.bar_battery_charge.setStyleSheet(
                f"color: {self.wcfg['font_color_battery_charge']};"
                f"background: {bgcolor};"
                f"{self.bar_width_battery}"
            )

    def update_active_timer(self, curr, last):
        """P2P activation timer"""
        if curr != last:
            if curr[1] != 2:
                fgcolor = self.wcfg["font_color_inactive"]
            else:
                fgcolor = self.wcfg["bkg_color_inactive"]

            format_text = f"{curr[0]:.2f}"[:4]
            self.bar_active_timer.setText(format_text)
            self.bar_active_timer.setStyleSheet(
                f"color: {fgcolor};"
                f"background: {self.wcfg['bkg_color_activation_timer']};"
                f"{self.bar_width_timer}"
            )
