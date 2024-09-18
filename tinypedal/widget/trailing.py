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
Trailing Widget
"""

from collections import deque
from PySide6.QtCore import Qt, QPointF, QRect
from PySide6.QtGui import QPainter, QPixmap, QPen

from ..api_control import api
from ..module_info import minfo
from ._base import Overlay

WIDGET_NAME = "trailing"


class Draw(Overlay):
    """Draw widget"""

    def __init__(self, config):
        # Assign base setting
        Overlay.__init__(self, config, WIDGET_NAME)

        # Config variable
        self.margin = max(int(self.wcfg["display_margin"]), 0)
        self.display_width = max(int(self.wcfg["display_width"]), 2)
        self.display_height = max(int(self.wcfg["display_height"]), 2)
        self.display_scale = max(int(
            self.wcfg["update_interval"] / 20 * self.wcfg["display_scale"]), 1)

        max_line_width = int(max(
            1,
            self.wcfg["throttle_line_width"],
            self.wcfg["brake_line_width"],
            self.wcfg["clutch_line_width"],
            self.wcfg["ffb_line_width"],
        ))
        self.max_samples = 3 + max_line_width  # 3 offset + max line width
        self.pedal_scale = self.display_height / 100
        self.pedal_max_range = self.display_height
        self.area_width = self.display_width
        self.area_height = self.display_height + self.margin * 2
        self.draw_queue = self.config_draw_order()

        # Config canvas
        self.resize(self.area_width, self.area_height)
        self.rect_viewport = self.set_viewport_orientation()

        self.pixmap_background = QPixmap(self.area_width, self.area_height)
        self.pixmap_plot = QPixmap(self.area_width, self.area_height)
        self.pixmap_plot_section = QPixmap(self.area_width, self.area_height)
        self.pixmap_plot_last = QPixmap(self.area_width, self.area_height)
        self.pixmap_plot_last.fill(Qt.transparent)

        if self.wcfg["show_throttle"]:
            self.data_throttle = self.create_data_samples(self.max_samples)
        if self.wcfg["show_brake"]:
            self.data_brake = self.create_data_samples(self.max_samples)
        if self.wcfg["show_clutch"]:
            self.data_clutch = self.create_data_samples(self.max_samples)
        if self.wcfg["show_ffb"]:
            self.data_ffb = self.create_data_samples(self.max_samples)
        if self.wcfg["show_wheel_lock"]:
            self.data_wheel_lock = self.create_data_samples(self.max_samples)
        if self.wcfg["show_wheel_slip"]:
            self.data_wheel_slip = self.create_data_samples(self.max_samples)

        self.pen = QPen()
        self.pen.setCapStyle(Qt.RoundCap)
        self.draw_background()
        self.draw_plot_section()
        self.draw_plot()

        # Last data
        self.delayed_update = False
        self.last_lap_etime = -1
        self.update_plot = 1

        # Set widget state & start update
        self.set_widget_state()

    def timerEvent(self, event):
        """Update when vehicle on track"""
        if api.state:

            # Use elapsed time to determine whether data paused
            # Add 1 extra update compensation
            lap_etime = api.read.timing.elapsed()
            if lap_etime != self.last_lap_etime:
                self.update_plot = 2
            elif self.update_plot:
                self.update_plot -= 1
            self.last_lap_etime = lap_etime

            if self.update_plot:
                if self.wcfg["show_throttle"]:
                    if self.wcfg["show_raw_throttle"]:
                        throttle = api.read.input.throttle_raw()
                    else:
                        throttle = api.read.input.throttle()
                    self.append_sample("throttle", throttle)

                if self.wcfg["show_brake"]:
                    if self.wcfg["show_raw_brake"]:
                        brake = api.read.input.brake_raw()
                    else:
                        brake = api.read.input.brake()
                    self.append_sample("brake", brake)

                if self.wcfg["show_clutch"]:
                    if self.wcfg["show_raw_clutch"]:
                        clutch = api.read.input.clutch_raw()
                    else:
                        clutch = api.read.input.clutch()
                    self.append_sample("clutch", clutch)

                if self.wcfg["show_ffb"]:
                    ffb = abs(api.read.input.force_feedback())
                    self.append_sample("ffb", ffb)

                if self.wcfg["show_wheel_lock"]:
                    wheel_lock = min(abs(min(minfo.wheels.slipRatio)), 1)
                    if wheel_lock >= self.wcfg["wheel_lock_threshold"] and api.read.input.brake_raw() > 0.02:
                        self.append_sample("wheel_lock", wheel_lock)
                    else:
                        self.append_sample("wheel_lock", -999)

                if self.wcfg["show_wheel_slip"]:
                    wheel_slip = min(max(minfo.wheels.slipRatio), 1)
                    if wheel_slip >= self.wcfg["wheel_slip_threshold"] and api.read.input.throttle_raw() > 0.02:
                        self.append_sample("wheel_slip", wheel_slip)
                    else:
                        self.append_sample("wheel_slip", -999)

                # Update after all pedal data set
                if self.delayed_update:
                    self.delayed_update = False
                    self.translate_samples()
                    self.draw_plot_section()
                    self.draw_plot()
                    self.pixmap_plot_last = self.pixmap_plot.copy(
                        0, 0, self.area_width, self.area_height)
                    self.update()  # trigger paint event

    # GUI update methods
    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        painter.setViewport(self.rect_viewport)
        painter.drawPixmap(0, 0, self.pixmap_background)
        painter.drawPixmap(0, 0, self.pixmap_plot)

    def draw_background(self):
        """Draw background"""
        self.pixmap_background.fill(self.wcfg["bkg_color"])
        painter = QPainter(self.pixmap_background)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(Qt.NoBrush)

        # Draw reference line
        if self.wcfg["show_reference_line"]:
            for idx in range(1, 6):
                self.draw_reference_line(
                    painter,
                    self.wcfg[f"reference_line_{idx}_style"],
                    self.wcfg[f"reference_line_{idx}_offset"],
                    self.wcfg[f"reference_line_{idx}_width"],
                    self.wcfg[f"reference_line_{idx}_color"]
                )

    def draw_reference_line(self, painter, style, offset, width, color):
        """Draw reference line"""
        if width > 0:
            if style:
                self.pen.setStyle(Qt.DashLine)
            else:
                self.pen.setStyle(Qt.SolidLine)
            self.pen.setWidth(width)
            self.pen.setColor(color)
            painter.setPen(self.pen)
            painter.drawLine(
                0,
                self.pedal_max_range * offset + self.margin,
                self.display_width,
                self.pedal_max_range * offset + self.margin,
            )

    def draw_plot(self):
        """Draw final plot"""
        self.pixmap_plot.fill(Qt.transparent)
        painter = QPainter(self.pixmap_plot)
        # Draw section plot
        painter.drawPixmap(0, 0, self.pixmap_plot_section)
        # Avoid overlapping previous frame
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        # Draw last plot, +3 sample offset, -2 sample crop
        painter.drawPixmap(
            self.display_scale * 3, 0, self.pixmap_plot_last,
            self.display_scale * 2, 0, 0 ,0)

    def draw_plot_section(self):
        """Draw section plot"""
        self.pixmap_plot_section.fill(Qt.transparent)
        painter = QPainter(self.pixmap_plot_section)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(Qt.NoBrush)
        self.pen.setStyle(Qt.SolidLine)

        for plot_name in self.draw_queue:
            if self.wcfg[f"show_{plot_name}"]:
                self.draw_line(painter, plot_name)

    def draw_line(self, painter, suffix):
        """Draw plot line"""
        self.pen.setWidth(self.wcfg[f"{suffix}_line_width"])
        self.pen.setColor(self.wcfg[f"{suffix}_color"])
        painter.setPen(self.pen)
        if self.wcfg[f"{suffix}_line_style"]:
            painter.drawPoints(getattr(self, f"data_{suffix}"))
        else:
            painter.drawPolyline(getattr(self, f"data_{suffix}"))

    # Additional methods
    @staticmethod
    def create_data_samples(samples):
        """Create data sample list"""
        return deque([QPointF(0, 0) for _ in range(samples)], samples)

    def scale_position(self, position):
        """Scale pedal value"""
        return position * 100 * self.pedal_scale + self.margin

    def append_sample(self, suffix, value):
        """Append input position sample to data list"""
        input_pos = self.scale_position(value)
        getattr(self, f"data_{suffix}").appendleft(QPointF(0, input_pos))
        self.delayed_update = True

    def translate_samples(self):
        """Translate sample position"""
        for index in range(self.max_samples):
            index_offset = index * self.display_scale + 1
            if self.wcfg["show_throttle"]:
                self.data_throttle[index].setX(index_offset)
            if self.wcfg["show_brake"]:
                self.data_brake[index].setX(index_offset)
            if self.wcfg["show_clutch"]:
                self.data_clutch[index].setX(index_offset)
            if self.wcfg["show_ffb"]:
                self.data_ffb[index].setX(index_offset)
            if self.wcfg["show_wheel_lock"]:
                self.data_wheel_lock[index].setX(index_offset)
            if self.wcfg["show_wheel_slip"]:
                self.data_wheel_slip[index].setX(index_offset)

    def set_viewport_orientation(self):
        """Set viewport orientation"""
        if self.wcfg["show_inverted_pedal"]:
            y_pos = 0
            height = self.area_height
        else:
            y_pos = self.area_height
            height = -self.area_height
        if self.wcfg["show_inverted_trailing"]:  # right alignment
            x_pos = self.area_width
            width = -self.area_width
        else:
            x_pos = 0
            width = self.area_width
        return QRect(x_pos, y_pos, width, height)

    def config_draw_order(self):
        """Config plot draw order"""
        plot_list = (
            (self.wcfg["draw_order_index_throttle"], "throttle"),
            (self.wcfg["draw_order_index_brake"], "brake"),
            (self.wcfg["draw_order_index_clutch"], "clutch"),
            (self.wcfg["draw_order_index_ffb"], "ffb"),
            (self.wcfg["draw_order_index_wheel_lock"], "wheel_lock"),
            (self.wcfg["draw_order_index_wheel_slip"], "wheel_slip"),
        )
        return tuple(zip(*sorted(plot_list, reverse=True)))[1]
