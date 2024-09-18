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
Fuel Widget
"""

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QLabel, QGridLayout

from .. import calculation as calc
from ..api_control import api
from ..module_info import minfo
from ._base import Overlay

WIDGET_NAME = "fuel"


class Draw(Overlay):
    """Draw widget"""

    def __init__(self, config):
        # Assign base setting
        Overlay.__init__(self, config, WIDGET_NAME)

        # Config font
        font_m = self.get_font_metrics(
            self.config_font(self.wcfg["font_name"], self.wcfg["font_size"]))

        # Config variable
        text_def = "-.--"
        self.bar_width = max(self.wcfg["bar_width"], 3)
        bar_padx = round(self.wcfg["font_size"] * self.wcfg["bar_padding"]) * 2
        bar_gap = self.wcfg["bar_gap"]
        self.decimals = tuple(
            map(self.decimal_range, (
            self.wcfg["decimal_places_end"],  # 0
            self.wcfg["decimal_places_remain"],  # 1
            self.wcfg["decimal_places_refuel"],  # 2
            self.wcfg["decimal_places_used"],  # 3
            self.wcfg["decimal_places_delta"],  # 4
            self.wcfg["decimal_places_early"],  # 5
            self.wcfg["decimal_places_laps"],  # 6
            self.wcfg["decimal_places_minutes"],  # 7
            self.wcfg["decimal_places_save"],  # 8
            self.wcfg["decimal_places_pits"],  # 9
        )))

        # Base style
        self.setStyleSheet(
            f"font-family: {self.wcfg['font_name']};"
            f"font-size: {self.wcfg['font_size']}px;"
            f"font-weight: {self.wcfg['font_weight']};"
        )
        self.style_width = (f"min-width: {font_m.width * self.bar_width + bar_padx}px;"
                            f"max-width: {font_m.width * self.bar_width + bar_padx}px;")

        # Create layout
        layout = QGridLayout()
        layout.setContentsMargins(0,0,0,0)  # remove border
        layout_upper = QGridLayout()
        layout_lower = QGridLayout()
        layout_upper.setSpacing(0)
        layout_lower.setSpacing(0)
        layout.setSpacing(bar_gap)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        column_upr = self.wcfg["column_index_upper"]
        column_mid = self.wcfg["column_index_middle"]
        column_lwr = self.wcfg["column_index_lower"]

        # Caption
        if self.wcfg["show_caption"]:
            bar_style_desc = (
                f"color: {self.wcfg['font_color_caption']};"
                f"background: {self.wcfg['bkg_color_caption']};"
                f"font-size: {int(self.wcfg['font_size'] * 0.8)}px;"
                f"{self.style_width}"
            )
            caption_list = (
                self.wcfg["caption_text_end"],
                self.wcfg["caption_text_remain"],
                self.wcfg["caption_text_refuel"],
                self.wcfg["caption_text_used"],
                self.wcfg["caption_text_delta"],
                self.wcfg["caption_text_early"],
                self.wcfg["caption_text_laps"],
                self.wcfg["caption_text_minutes"],
                self.wcfg["caption_text_save"],
                self.wcfg["caption_text_pits"],
            )
            for index, caption in enumerate(caption_list):
                setattr(self, f"bar_desc_{caption}", QLabel(caption))
                getattr(self, f"bar_desc_{caption}").setAlignment(Qt.AlignCenter)
                getattr(self, f"bar_desc_{caption}").setStyleSheet(bar_style_desc)
                if index < 5:
                    row_idx = 2 if self.wcfg["swap_upper_caption"] else 0
                    layout_upper.addWidget(getattr(self, f"bar_desc_{caption}"), row_idx, index)
                else:
                    row_idx = 0 if self.wcfg["swap_lower_caption"] else 2
                    layout_lower.addWidget(getattr(self, f"bar_desc_{caption}"), row_idx, index - 5)

        # Estimated end fuel
        self.bar_fuel_end = QLabel(text_def)
        self.bar_fuel_end.setAlignment(Qt.AlignCenter)
        self.bar_fuel_end.setStyleSheet(
            f"color: {self.wcfg['font_color_end']};"
            f"background: {self.wcfg['bkg_color_end']};"
            f"{self.style_width}"
        )

        # Remaining fuel
        self.bar_fuel_curr = QLabel(text_def)
        self.bar_fuel_curr.setAlignment(Qt.AlignCenter)
        self.bar_fuel_curr.setStyleSheet(
            f"color: {self.wcfg['font_color_remain']};"
            f"background: {self.wcfg['bkg_color_remain']};"
            f"{self.style_width}"
        )

        # Total needed fuel
        self.bar_fuel_need = QLabel(text_def)
        self.bar_fuel_need.setAlignment(Qt.AlignCenter)
        self.bar_fuel_need.setStyleSheet(
            f"color: {self.wcfg['font_color_refuel']};"
            f"background: {self.wcfg['bkg_color_refuel']};"
            f"{self.style_width}"
        )

        # Estimated fuel consumption
        self.bar_fuel_used = QLabel(text_def)
        self.bar_fuel_used.setAlignment(Qt.AlignCenter)
        self.bar_fuel_used.setStyleSheet(
            f"color: {self.wcfg['font_color_used']};"
            f"background: {self.wcfg['bkg_color_used']};"
            f"{self.style_width}"
        )

        # Delta fuel consumption
        self.bar_fuel_delta = QLabel(text_def)
        self.bar_fuel_delta.setAlignment(Qt.AlignCenter)
        self.bar_fuel_delta.setStyleSheet(
            f"color: {self.wcfg['font_color_delta']};"
            f"background: {self.wcfg['bkg_color_delta']};"
            f"{self.style_width}"
        )

        # Estimate pit stop counts when pitting at end of current lap
        self.bar_fuel_early = QLabel(text_def)
        self.bar_fuel_early.setAlignment(Qt.AlignCenter)
        self.bar_fuel_early.setStyleSheet(
            f"color: {self.wcfg['font_color_early']};"
            f"background: {self.wcfg['bkg_color_early']};"
            f"{self.style_width}"
        )

        # Estimated laps current fuel can last
        self.bar_fuel_laps = QLabel(text_def)
        self.bar_fuel_laps.setAlignment(Qt.AlignCenter)
        self.bar_fuel_laps.setStyleSheet(
            f"color: {self.wcfg['font_color_laps']};"
            f"background: {self.wcfg['bkg_color_laps']};"
            f"{self.style_width}"
        )

        # Estimated minutes current fuel can last
        self.bar_fuel_mins = QLabel(text_def)
        self.bar_fuel_mins.setAlignment(Qt.AlignCenter)
        self.bar_fuel_mins.setStyleSheet(
            f"color: {self.wcfg['font_color_minutes']};"
            f"background: {self.wcfg['bkg_color_minutes']};"
            f"{self.style_width}"
        )

        # Estimated one less pit fuel consumption
        self.bar_fuel_save = QLabel(text_def)
        self.bar_fuel_save.setAlignment(Qt.AlignCenter)
        self.bar_fuel_save.setStyleSheet(
            f"color: {self.wcfg['font_color_save']};"
            f"background: {self.wcfg['bkg_color_save']};"
            f"{self.style_width}"
        )

        # Estimate pit stop counts when pitting at end of current stint
        self.bar_fuel_pits = QLabel(text_def)
        self.bar_fuel_pits.setAlignment(Qt.AlignCenter)
        self.bar_fuel_pits.setStyleSheet(
            f"color: {self.wcfg['font_color_pits']};"
            f"background: {self.wcfg['bkg_color_pits']};"
            f"{self.style_width}"
        )

        # Fuel level bar
        if self.wcfg["show_fuel_level_bar"]:
            self.fuel_level_width = (font_m.width * self.bar_width + bar_padx) * 5
            self.fuel_level_height = max(self.wcfg["fuel_level_bar_height"], 1)
            self.rect_fuel_left = QRectF(0, 0, 0, self.fuel_level_height)
            self.rect_fuel_start = QRectF(
                0, 0,
                max(self.wcfg["starting_fuel_level_mark_width"], 1),
                self.fuel_level_height)
            self.rect_fuel_refuel = QRectF(
                0, 0,
                max(self.wcfg["refueling_level_mark_width"], 1),
                self.fuel_level_height)

            self.fuel_level = QLabel()
            self.fuel_level.setFixedSize(self.fuel_level_width, self.fuel_level_height)
            self.pixmap_fuel_level = QPixmap(self.fuel_level_width, self.fuel_level_height)
            self.draw_fuel_level(self.fuel_level, self.pixmap_fuel_level, [0,0,0])

        # Set layout
        layout_upper.addWidget(self.bar_fuel_end, 1, 0)
        layout_upper.addWidget(self.bar_fuel_curr, 1, 1)
        layout_upper.addWidget(self.bar_fuel_need, 1, 2)
        layout_upper.addWidget(self.bar_fuel_used, 1, 3)
        layout_upper.addWidget(self.bar_fuel_delta, 1, 4)
        layout_lower.addWidget(self.bar_fuel_early, 1, 0)
        layout_lower.addWidget(self.bar_fuel_laps, 1, 1)
        layout_lower.addWidget(self.bar_fuel_mins, 1, 2)
        layout_lower.addWidget(self.bar_fuel_save, 1, 3)
        layout_lower.addWidget(self.bar_fuel_pits, 1, 4)
        layout.addLayout(layout_upper, column_upr, 0)
        if self.wcfg["show_fuel_level_bar"]:
            layout.addWidget(self.fuel_level, column_mid, 0)
        layout.addLayout(layout_lower, column_lwr, 0)
        self.setLayout(layout)

        # Last data
        self.last_amount_end = None
        self.last_amount_curr = None
        self.last_amount_need = None
        self.last_used_last = None
        self.last_delta_fuel = None
        self.last_est_pits_early = None
        self.last_est_runlaps = None
        self.last_est_runmins = None
        self.last_fuel_save = None
        self.last_est_pits_end = None
        self.last_fuel_level = None

        # Set widget state & start update
        self.set_widget_state()

    def timerEvent(self, event):
        """Update when vehicle on track"""
        if api.state:

            # Estimated end fuel
            amount_end = f"{self.fuel_units(minfo.fuel.amountEndStint):.{self.decimals[0]}f}"
            self.update_fuel("end", amount_end, self.last_amount_end)
            self.last_amount_end = amount_end

            # Remaining fuel
            amount_curr = f"{self.fuel_units(minfo.fuel.amountCurrent):.{self.decimals[1]}f}"
            self.update_fuel(
                "curr", amount_curr, self.last_amount_curr, minfo.fuel.estimatedLaps)
            self.last_amount_curr = amount_curr

            # Total needed fuel
            amount_need = f"{calc.sym_range(self.fuel_units(minfo.fuel.amountNeeded), 9999):+.{self.decimals[2]}f}"
            self.update_fuel(
                "need", amount_need, self.last_amount_need, minfo.fuel.estimatedLaps)
            self.last_amount_need = amount_need

            # Estimated fuel consumption
            used_last = f"{self.fuel_units(minfo.fuel.estimatedConsumption):.{self.decimals[3]}f}"
            self.update_fuel("used", used_last, self.last_used_last)
            self.last_used_last = used_last

            # Delta fuel consumption
            delta_fuel = f"{self.fuel_units(minfo.fuel.deltaConsumption):+.{self.decimals[4]}f}"
            self.update_fuel("delta", delta_fuel, self.last_delta_fuel)
            self.last_delta_fuel = delta_fuel

            # Estimate pit stop counts when pitting at end of current lap
            est_pits_early = f"{min(max(minfo.fuel.estimatedNumPitStopsEarly, 0), 99.99):.{self.decimals[5]}f}"
            self.update_fuel("early", est_pits_early, self.last_est_pits_early)
            self.last_est_pits_early = est_pits_early

            # Estimated laps current fuel can last
            est_runlaps = f"{min(minfo.fuel.estimatedLaps, 9999):.{self.decimals[6]}f}"
            self.update_fuel("laps", est_runlaps, self.last_est_runlaps)
            self.last_est_runlaps = est_runlaps

            # Estimated minutes current fuel can last
            est_runmins = f"{min(minfo.fuel.estimatedMinutes, 9999):.{self.decimals[7]}f}"
            self.update_fuel("mins", est_runmins, self.last_est_runmins)
            self.last_est_runmins = est_runmins

            # Estimated one less pit fuel consumption
            fuel_save = f"{min(max(self.fuel_units(minfo.fuel.oneLessPitConsumption), 0), 99.99):.{self.decimals[8]}f}"
            self.update_fuel("save", fuel_save, self.last_fuel_save)
            self.last_fuel_save = fuel_save

            # Estimate pit stop counts when pitting at end of current stint
            est_pits_end = f"{min(max(minfo.fuel.estimatedNumPitStopsEnd, 0), 99.99):.{self.decimals[9]}f}"
            self.update_fuel("pits", est_pits_end, self.last_est_pits_end)
            self.last_est_pits_end = est_pits_end

            # Fuel level bar
            if self.wcfg["show_fuel_level_bar"]:
                fuel_capacity = max(minfo.fuel.capacity, 1)
                fuel_level = (
                    round(minfo.fuel.amountCurrent / fuel_capacity, 3),
                    round(minfo.fuel.amountStart / fuel_capacity, 3),
                    round((minfo.fuel.amountCurrent + minfo.fuel.amountNeeded) / fuel_capacity, 3),
                )
                self.update_fuel_level(fuel_level, self.last_fuel_level)
                self.last_fuel_level = fuel_level

    # GUI update methods
    def update_fuel(self, suffix, curr, last, state=None):
        """Update fuel data"""
        if curr != last:
            if state:  # low fuel warning
                getattr(self, f"bar_fuel_{suffix}").setStyleSheet(
                    f"{self.color_lowfuel(state, suffix)}{self.style_width}"
                )
            getattr(self, f"bar_fuel_{suffix}").setText(
                curr[:self.bar_width].strip("."))

    def update_fuel_level(self, curr, last):
        """Fuel level update"""
        if curr != last:
            self.draw_fuel_level(self.fuel_level, self.pixmap_fuel_level, curr)

    def draw_fuel_level(self, canvas, pixmap, fuel_data):
        """Fuel level"""
        pixmap.fill(self.wcfg["bkg_color_fuel_level"])
        painter = QPainter(pixmap)

        # Update fuel level highlight
        painter.setPen(Qt.NoPen)
        self.rect_fuel_left.setWidth(fuel_data[0] * self.fuel_level_width)
        painter.fillRect(self.rect_fuel_left, self.wcfg["highlight_color_fuel_level"])

        # Update starting fuel level mark
        if self.wcfg["show_starting_fuel_level_mark"]:
            self.rect_fuel_start.moveLeft(fuel_data[1] * self.fuel_level_width)
            painter.fillRect(self.rect_fuel_start, self.wcfg["starting_fuel_level_mark_color"])

        if self.wcfg["show_refueling_level_mark"]:
            self.rect_fuel_refuel.moveLeft(fuel_data[2] * self.fuel_level_width)
            painter.fillRect(self.rect_fuel_refuel, self.wcfg["refueling_level_mark_color"])

        canvas.setPixmap(pixmap)

    # Additional methods
    def fuel_units(self, fuel):
        """2 different fuel unit conversion, default is Liter"""
        if self.cfg.units["fuel_unit"] == "Gallon":
            return calc.liter2gallon(fuel)
        return fuel

    def color_lowfuel(self, state, suffix):
        """Low fuel warning color"""
        if suffix == "curr":
            fgcolor = self.wcfg["font_color_remain"]
            bgcolor = self.wcfg["bkg_color_remain"]
        else:
            fgcolor = self.wcfg["font_color_refuel"]
            bgcolor = self.wcfg["bkg_color_refuel"]

        if state > self.wcfg["low_fuel_lap_threshold"]:
            return f"color: {fgcolor};background: {bgcolor};"
        return f"color: {fgcolor};background: {self.wcfg['warning_color_low_fuel']};"

    @staticmethod
    def decimal_range(value):
        """Decimal place range"""
        return min(max(int(value), 0), 3)
