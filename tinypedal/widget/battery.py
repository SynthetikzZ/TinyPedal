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
Battery Widget
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel

from ..api_control import api
from ..module_info import minfo
from ._base import Overlay

WIDGET_NAME = "battery"


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
        bar_width = f"min-width: {font_m.width * 8 + bar_padx}px;"
        self.freeze_duration = min(max(self.wcfg["freeze_duration"], 0), 30)

        # Base style
        self.setStyleSheet(
            f"font-family: {self.wcfg['font_name']};"
            f"font-size: {self.wcfg['font_size']}px;"
            f"font-weight: {self.wcfg['font_weight']};"
            f"{bar_width}"
        )

        # Create layout
        layout = QGridLayout()
        layout.setContentsMargins(0,0,0,0)  # remove border
        layout.setSpacing(bar_gap)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        column_bc = self.wcfg["column_index_battery_charge"]
        column_bd = self.wcfg["column_index_battery_drain"]
        column_br = self.wcfg["column_index_battery_regen"]
        column_at = self.wcfg["column_index_activation_timer"]

        # Battery charge
        if self.wcfg["show_battery_charge"]:
            self.bar_battery_charge = QLabel("BATTERY")
            self.bar_battery_charge.setAlignment(Qt.AlignCenter)
            self.bar_battery_charge.setStyleSheet(
                f"color: {self.wcfg['font_color_battery_charge']};"
                f"background: {self.wcfg['bkg_color_battery_charge']};"
            )

        # Battery drain
        if self.wcfg["show_battery_drain"]:
            self.bar_battery_drain = QLabel("B DRAIN")
            self.bar_battery_drain.setAlignment(Qt.AlignCenter)
            self.bar_battery_drain.setStyleSheet(
                f"color: {self.wcfg['font_color_battery_drain']};"
                f"background: {self.wcfg['bkg_color_battery_drain']};"
            )

        # Battery regen
        if self.wcfg["show_battery_regen"]:
            self.bar_battery_regen = QLabel("B REGEN")
            self.bar_battery_regen.setAlignment(Qt.AlignCenter)
            self.bar_battery_regen.setStyleSheet(
                f"color: {self.wcfg['font_color_battery_regen']};"
                f"background: {self.wcfg['bkg_color_battery_regen']};"
            )

        # Activation timer
        if self.wcfg["show_activation_timer"]:
            self.bar_activation_timer = QLabel("B TIMER")
            self.bar_activation_timer.setAlignment(Qt.AlignCenter)
            self.bar_activation_timer.setStyleSheet(
                f"color: {self.wcfg['font_color_activation_timer']};"
                f"background: {self.wcfg['bkg_color_activation_timer']};"
            )

        # Set layout
        if self.wcfg["layout"] == 0:
            # Vertical layout
            if self.wcfg["show_battery_charge"]:
                layout.addWidget(self.bar_battery_charge, column_bc, 0)
            if self.wcfg["show_battery_drain"]:
                layout.addWidget(self.bar_battery_drain, column_bd, 0)
            if self.wcfg["show_battery_regen"]:
                layout.addWidget(self.bar_battery_regen, column_br, 0)
            if self.wcfg["show_activation_timer"]:
                layout.addWidget(self.bar_activation_timer, column_at, 0)
        else:
            # Horizontal layout
            if self.wcfg["show_battery_charge"]:
                layout.addWidget(self.bar_battery_charge, 0, column_bc)
            if self.wcfg["show_battery_drain"]:
                layout.addWidget(self.bar_battery_drain, 0, column_bd)
            if self.wcfg["show_battery_regen"]:
                layout.addWidget(self.bar_battery_regen, 0, column_br)
            if self.wcfg["show_activation_timer"]:
                layout.addWidget(self.bar_activation_timer, 0, column_at)
        self.setLayout(layout)

        # Last data
        self.last_lap_stime = 0  # last lap start time

        self.last_battery_charge = None
        self.last_battery_drain = None
        self.last_battery_regen = None
        self.last_motor_active_timer = None

        # Set widget state & start update
        self.set_widget_state()

    def timerEvent(self, event):
        """Update when vehicle on track"""
        if api.state:

            lap_stime = api.read.timing.start()
            lap_etime = api.read.timing.elapsed()

            # Battery charge & usage
            if self.wcfg["show_battery_charge"]:
                self.update_battery_charge(
                    minfo.hybrid.batteryCharge, self.last_battery_charge)

            if lap_stime != self.last_lap_stime:
                laptime_curr = lap_etime - lap_stime
                if laptime_curr >= self.freeze_duration or laptime_curr < 0:
                    self.last_lap_stime = lap_stime
                battery_drain = minfo.hybrid.batteryDrainLast
                battery_regen = minfo.hybrid.batteryRegenLast
            else:
                battery_drain = minfo.hybrid.batteryDrain
                battery_regen = minfo.hybrid.batteryRegen

            if self.wcfg["show_battery_drain"]:
                self.update_battery_drain(battery_drain, self.last_battery_drain)
                self.last_battery_drain = battery_drain

            if self.wcfg["show_battery_regen"]:
                self.update_battery_regen(battery_regen, self.last_battery_regen)
                self.last_battery_regen = battery_regen

            self.last_battery_charge = minfo.hybrid.batteryCharge

            # Motor activation timer
            if self.wcfg["show_activation_timer"]:
                self.update_activation_timer(
                    minfo.hybrid.motorActiveTimer, self.last_motor_active_timer)
                self.last_motor_active_timer = minfo.hybrid.motorActiveTimer

    # GUI update methods
    def update_battery_charge(self, curr, last):
        """Battery charge"""
        if curr != last:
            if curr > self.wcfg["low_battery_threshold"]:
                color = (f"color: {self.wcfg['font_color_battery_charge']};"
                         f"background: {self.wcfg['bkg_color_battery_charge']};")
            else:
                color = (f"color: {self.wcfg['font_color_battery_charge']};"
                         f"background: {self.wcfg['warning_color_low_battery']};")

            format_text = f"{curr:.2f}"[:7].rjust(7)
            self.bar_battery_charge.setText(f"B{format_text}")
            self.bar_battery_charge.setStyleSheet(color)

    def update_battery_drain(self, curr, last):
        """Battery drain"""
        if curr != last:
            format_text = f"{curr:.2f}"[:7].rjust(7)
            self.bar_battery_drain.setText(f"-{format_text}")

    def update_battery_regen(self, curr, last):
        """Battery regen"""
        if curr != last:
            format_text = f"{curr:.2f}"[:7].rjust(7)
            self.bar_battery_regen.setText(f"+{format_text}")

    def update_activation_timer(self, curr, last):
        """Motor activation timer"""
        if curr != last:
            format_text = f"{curr:.2f}"[:7].rjust(7)
            self.bar_activation_timer.setText(f"{format_text}s")
