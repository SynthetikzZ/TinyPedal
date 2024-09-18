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
Deltabest Widget
"""

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QPen, QBrush

from .. import calculation as calc
from ..api_control import api
from ..module_info import minfo
from ._base import Overlay

WIDGET_NAME = "deltabest"


class Draw(Overlay):
    """Draw widget"""

    def __init__(self, config):
        # Assign base setting
        Overlay.__init__(self, config, WIDGET_NAME)

        # Config font
        self.font = self.config_font(
            self.wcfg["font_name"],
            self.wcfg["font_size"],
            self.wcfg["font_weight"]
        )
        font_m = self.get_font_metrics(self.font)
        font_offset = self.calc_font_offset(font_m)

        # Config variable
        self.dbar_length = int(self.wcfg["bar_length"] * 0.5)
        self.dbar_height = int(self.wcfg["bar_height"])
        bar_gap = self.wcfg["bar_gap"]
        padx = round(font_m.width * self.wcfg["bar_padding_horizontal"])
        pady = round(font_m.capital * self.wcfg["bar_padding_vertical"])

        self.delta_width = font_m.width * 7 + padx * 2
        self.delta_height = int(font_m.capital + pady * 2)

        if self.wcfg["layout"] == 0:
            pos_y1 = 0
        else:
            pos_y1 = self.delta_height + bar_gap

        if self.wcfg["layout"] == 0 and self.wcfg["show_delta_bar"]:
            pos_y2 = self.dbar_height + bar_gap
        else:
            pos_y2 = 0

        self.rect_deltabar = QRectF(0, pos_y1, self.dbar_length * 2, self.dbar_height)
        self.rect_deltapos = QRectF(0, pos_y1, 0, self.dbar_height)
        self.rect_delta = QRectF(0, pos_y2, self.delta_width, self.delta_height)
        self.rect_text_delta = self.rect_delta.adjusted(0, font_offset, 0, 0)

        self.freeze_duration = min(max(self.wcfg["freeze_duration"], 0), 30)

        # Config canvas
        if self.wcfg["show_delta_bar"]:
            self.resize(self.dbar_length * 2,
                        self.dbar_height + bar_gap + self.delta_height)
        else:
            self.resize(self.delta_width, self.delta_height)

        self.pen = QPen()
        self.brush = QBrush(Qt.SolidPattern)

        # Last data
        self.delta_best = 0
        self.last_delta_best = 0
        self.last_laptime = 0
        self.new_lap = True

        # Set widget state & start update
        self.set_widget_state()

    def timerEvent(self, event):
        """Update when vehicle on track"""
        if api.state:

            # Deltabest
            if minfo.delta.lapTimeCurrent < self.freeze_duration:
                self.delta_best = minfo.delta.lapTimeLast - self.last_laptime
                self.new_lap = True
            else:
                if self.new_lap:
                    self.last_laptime = getattr(minfo.delta, f"lapTime{self.wcfg['deltabest_source']}")
                    self.new_lap = False

                self.delta_best = getattr(minfo.delta, f"delta{self.wcfg['deltabest_source']}")

            self.update_deltabest(self.delta_best, self.last_delta_best)
            self.last_delta_best = self.delta_best

    # GUI update methods
    def update_deltabest(self, curr, last):
        """Deltabest update"""
        if curr != last:
            self.update()

    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        delta_pos = self.delta_position(
            self.wcfg["bar_display_range"],
            self.delta_best,
            self.dbar_length)
        # Draw deltabar
        if self.wcfg["show_delta_bar"]:
            self.draw_deltabar(painter, delta_pos)
        # Draw delta readings
        self.draw_readings(painter, delta_pos)

    def draw_deltabar(self, painter, delta_pos):
        """Draw deltabar"""
        if self.delta_best > 0:
            pos_x = delta_pos
            width = self.dbar_length - delta_pos
        else:
            pos_x = self.dbar_length
            width = delta_pos - self.dbar_length

        self.rect_deltapos.moveLeft(pos_x)
        self.rect_deltapos.setWidth(width)

        painter.setPen(Qt.NoPen)
        self.brush.setColor(self.wcfg["bkg_color_deltabar"])
        painter.setBrush(self.brush)
        painter.drawRect(self.rect_deltabar)

        self.brush.setColor(self.color_delta(self.delta_best))
        painter.setBrush(self.brush)
        painter.drawRect(self.rect_deltapos)

    def draw_readings(self, painter, delta_pos):
        """Draw readings"""
        if self.wcfg["swap_style"]:
            self.pen.setColor(self.wcfg["bkg_color_deltabest"])
            self.brush.setColor(self.color_delta(self.delta_best))
        else:
            self.pen.setColor(self.color_delta(self.delta_best))
            self.brush.setColor(self.wcfg["bkg_color_deltabest"])

        if self.wcfg["show_delta_bar"] and self.wcfg["show_animated_deltabest"]:
            pos_x = min(max(delta_pos - self.delta_width * 0.5, 0),
                            self.dbar_length * 2 - self.delta_width)
        elif self.wcfg["show_delta_bar"]:
            pos_x = self.dbar_length - self.delta_width * 0.5
        else:
            pos_x = 0

        self.rect_delta.moveLeft(pos_x)
        self.rect_text_delta.moveLeft(pos_x)

        painter.setPen(Qt.NoPen)
        painter.setBrush(self.brush)
        painter.drawRect(self.rect_delta)

        painter.setFont(self.font)
        painter.setPen(self.pen)
        painter.drawText(
            self.rect_text_delta,
            Qt.AlignCenter,
            f"{calc.sym_range(self.delta_best, self.wcfg['delta_display_range']):+.3f}"[:7]
        )

    # Additional methods
    @staticmethod
    def delta_position(rng, delta, length):
        """Delta position"""
        return (rng - calc.sym_range(delta, rng)) * length / rng

    def color_delta(self, delta):
        """Delta time color"""
        if delta <= 0:
            return self.wcfg["bkg_color_time_gain"]
        return self.wcfg["bkg_color_time_loss"]
