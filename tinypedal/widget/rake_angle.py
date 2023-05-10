#  TinyPedal is an open-source overlay application for racing simulation.
#  Copyright (C) 2022-2023  Xiang
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
Rake angle Widget
"""

from PySide2.QtCore import Qt, Slot
from PySide2.QtGui import QFont, QFontMetrics
from PySide2.QtWidgets import (
    QGridLayout,
    QLabel,
)

from .. import calculation as calc
from .. import readapi as read_data
from ..base import Widget

WIDGET_NAME = "rake_angle"


class Draw(Widget):
    """Draw widget"""

    def __init__(self, config):
        # Assign base setting
        Widget.__init__(self, config, WIDGET_NAME)

        # Config font
        self.font = QFont()
        self.font.setFamily(self.wcfg['font_name'])
        self.font.setPixelSize(self.wcfg['font_size'])
        font_w = QFontMetrics(self.font).averageCharWidth()

        # Config variable
        bar_padx = round(self.wcfg["font_size"] * self.wcfg["bar_padding"])
        self.sign_text = "°" if self.wcfg["show_degree_sign"] else ""
        self.bar_width = font_w * (
            5 + len(self.sign_text) + len(self.wcfg["prefix_rake_angle"]))

        # Base style
        self.setStyleSheet(
            f"font-family: {self.wcfg['font_name']};"
            f"font-size: {self.wcfg['font_size']}px;"
            f"font-weight: {self.wcfg['font_weight']};"
            f"padding: 0 {bar_padx}px;"
        )

        # Create layout
        layout = QGridLayout()
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # Rake angle
        self.bar_rake = QLabel("RAKE")
        self.bar_rake.setAlignment(Qt.AlignCenter)
        self.bar_rake.setStyleSheet(
            f"color: {self.wcfg['font_color_rake_angle']};"
            f"background: {self.wcfg['bkg_color_rake_angle']};"
            f"min-width: {self.bar_width}px;"
            f"max-width: {self.bar_width}px;"
        )

        # Set layout
        layout.addWidget(self.bar_rake, 0, 0)
        self.setLayout(layout)

        # Last data
        self.last_rake = 0

        # Set widget state & start update
        self.set_widget_state()
        self.update_timer.start()

    @Slot()
    def update_data(self):
        """Update when vehicle on track"""
        if self.wcfg["enable"] and read_data.state():

            # Read ride height & rake data
            ride_height = tuple(map(calc.meter2millmeter, read_data.ride_height()))

            # Rake angle
            rake = round(calc.rake(*ride_height), 2)
            self.update_rakeangle(rake, self.last_rake)
            self.last_rake = rake

    # GUI update methods
    def update_rakeangle(self, curr, last):
        """Rake angle data"""
        if curr != last:
            if curr >= 0:
                bgcolor = self.wcfg["bkg_color_rake_angle"]
            else:
                bgcolor = self.wcfg["warning_color_negative_rake"]

            rake_angle = calc.rake2angle(curr, self.wcfg["wheelbase"])
            self.bar_rake.setText(
                f"{self.wcfg['prefix_rake_angle']}{rake_angle:+.02f}{self.sign_text}")
            self.bar_rake.setStyleSheet(
                f"color: {self.wcfg['font_color_rake_angle']};"
                f"background: {bgcolor};"
                f"min-width: {self.bar_width}px;"
            )
