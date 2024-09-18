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
Force Widget
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel

from ..api_control import api
from ..module_info import minfo
from ._base import Overlay

WIDGET_NAME = "force"


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
        bar_width = f"min-width: {font_m.width * 6 + bar_padx}px;"

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

        column_lg = self.wcfg["column_index_long_gforce"]
        column_lt = self.wcfg["column_index_lat_gforce"]
        column_dr = self.wcfg["column_index_downforce_ratio"]
        column_fd = self.wcfg["column_index_front_downforce"]
        column_rd = self.wcfg["column_index_rear_downforce"]

        # G force
        if self.wcfg["show_g_force"]:
            self.bar_gforce_lgt = QLabel("n/a")
            self.bar_gforce_lgt.setAlignment(Qt.AlignCenter)
            self.bar_gforce_lgt.setStyleSheet(
                f"color: {self.wcfg['font_color_g_force']};"
                f"background: {self.wcfg['bkg_color_g_force']};"
            )

            self.bar_gforce_lat = QLabel("n/a")
            self.bar_gforce_lat.setAlignment(Qt.AlignCenter)
            self.bar_gforce_lat.setStyleSheet(
                f"color: {self.wcfg['font_color_g_force']};"
                f"background: {self.wcfg['bkg_color_g_force']};"
            )

        # Downforce ratio
        if self.wcfg["show_downforce_ratio"]:
            self.bar_df_ratio = QLabel("n/a")
            self.bar_df_ratio.setAlignment(Qt.AlignCenter)
            self.bar_df_ratio.setStyleSheet(
                f"color: {self.wcfg['font_color_downforce_ratio']};"
                f"background: {self.wcfg['bkg_color_downforce_ratio']};"
            )

        # Front downforce
        if self.wcfg["show_front_downforce"]:
            self.bar_df_front = QLabel("n/a")
            self.bar_df_front.setAlignment(Qt.AlignCenter)
            self.bar_df_front.setStyleSheet(
                f"color: {self.wcfg['font_color_front_downforce']};"
                f"background: {self.wcfg['bkg_color_front_downforce']};"
            )

        # Rear downforce
        if self.wcfg["show_rear_downforce"]:
            self.bar_df_rear = QLabel("n/a")
            self.bar_df_rear.setAlignment(Qt.AlignCenter)
            self.bar_df_rear.setStyleSheet(
                f"color: {self.wcfg['font_color_rear_downforce']};"
                f"background: {self.wcfg['bkg_color_rear_downforce']};"
            )

        # Set layout
        if self.wcfg["layout"] == 0:
            # Vertical layout
            if self.wcfg["show_g_force"]:
                layout.addWidget(self.bar_gforce_lgt, column_lg, 0)
                layout.addWidget(self.bar_gforce_lat, column_lt, 0)
            if self.wcfg["show_downforce_ratio"]:
                layout.addWidget(self.bar_df_ratio, column_dr, 0)
            if self.wcfg["show_front_downforce"]:
                layout.addWidget(self.bar_df_front, column_fd, 0)
            if self.wcfg["show_rear_downforce"]:
                layout.addWidget(self.bar_df_rear, column_rd, 0)
        else:
            # Horizontal layout
            if self.wcfg["show_g_force"]:
                layout.addWidget(self.bar_gforce_lgt, 0, column_lg)
                layout.addWidget(self.bar_gforce_lat, 0, column_lt)
            if self.wcfg["show_downforce_ratio"]:
                layout.addWidget(self.bar_df_ratio, 0, column_dr)
            if self.wcfg["show_front_downforce"]:
                layout.addWidget(self.bar_df_front, 0, column_fd)
            if self.wcfg["show_rear_downforce"]:
                layout.addWidget(self.bar_df_rear, 0, column_rd)
        self.setLayout(layout)

        # Last data
        self.last_gf_lgt = None
        self.last_gf_lat = None
        self.last_df_ratio = None
        self.last_df_front = None
        self.last_df_rear = None

        # Set widget state & start update
        self.set_widget_state()

    def timerEvent(self, event):
        """Update when vehicle on track"""
        if api.state:

            # G force
            if self.wcfg["show_g_force"]:
                # Longitudinal g-force
                gf_lgt = round(minfo.force.lgtGForceRaw, 2)
                self.update_gf_lgt(gf_lgt, self.last_gf_lgt)
                self.last_gf_lgt = gf_lgt

                # Lateral g-force
                gf_lat = round(minfo.force.latGForceRaw, 2)
                self.update_gf_lat(gf_lat, self.last_gf_lat)
                self.last_gf_lat = gf_lat

            # Downforce ratio
            if self.wcfg["show_downforce_ratio"]:
                df_ratio = f"{minfo.force.downForceRatio:.2f}"[:5].strip(".")
                self.update_df_ratio(df_ratio, self.last_df_ratio)
                self.last_df_ratio = df_ratio

            # Front downforce
            if self.wcfg["show_front_downforce"]:
                df_front = round(minfo.force.downForceFront)
                self.update_df_front(df_front, self.last_df_front)
                self.last_df_front = df_front

            # Rear downforce
            if self.wcfg["show_rear_downforce"]:
                df_rear = round(minfo.force.downForceRear)
                self.update_df_rear(df_rear, self.last_df_rear)
                self.last_df_rear = df_rear

    # GUI update methods
    def update_gf_lgt(self, curr, last):
        """Longitudinal g-force"""
        if curr != last:
            self.bar_gforce_lgt.setText(f"{self.gforce_lgt(curr)} {abs(curr):.2f}")

    def update_gf_lat(self, curr, last):
        """Lateral g-force"""
        if curr != last:
            self.bar_gforce_lat.setText(f"{abs(curr):.2f} {self.gforce_lat(curr)}")

    def update_df_ratio(self, curr, last):
        """Downforce ratio"""
        if curr != last:
            self.bar_df_ratio.setText(f"{curr}%")

    def update_df_front(self, curr, last):
        """Downforce front"""
        if curr != last:
            if curr >= 0:
                color = (f"color: {self.wcfg['font_color_front_downforce']};"
                         f"background: {self.wcfg['bkg_color_front_downforce']};")
            else:
                color = (f"color: {self.wcfg['font_color_front_downforce']};"
                         f"background: {self.wcfg['warning_color_liftforce']};")

            self.bar_df_front.setText(f"F{abs(curr):5.0f}"[:6])
            self.bar_df_front.setStyleSheet(color)

    def update_df_rear(self, curr, last):
        """Downforce rear"""
        if curr != last:
            if curr >= 0:
                color = (f"color: {self.wcfg['font_color_rear_downforce']};"
                         f"background: {self.wcfg['bkg_color_rear_downforce']};")
            else:
                color = (f"color: {self.wcfg['font_color_rear_downforce']};"
                         f"background: {self.wcfg['warning_color_liftforce']};")

            self.bar_df_rear.setText(f"R{abs(curr):5.0f}"[:6])
            self.bar_df_rear.setStyleSheet(color)

    # Additional methods
    @staticmethod
    def gforce_lgt(g_force):
        """Longitudinal g-force direction symbol"""
        if g_force > 0.1:
            return "▼"
        if g_force < -0.1:
            return "▲"
        return "●"

    @staticmethod
    def gforce_lat(g_force):
        """Lateral g-force direction symbol"""
        if g_force > 0.1:
            return "◀"
        if g_force < -0.1:
            return "▶"
        return "●"
