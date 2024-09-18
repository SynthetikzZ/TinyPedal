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
Fuel calculator
"""

import math
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QBrush, QColor
from PySide6.QtWidgets import (
    QWidget,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
    QLineEdit,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
)

from ..api_control import api
from ..const import APP_ICON
from ..setting import cfg
from ..module_info import minfo
from .. import calculation as calc
from .. import formatter as fmt

PANEL_LEFT_WIDTH = 350


class FuelCalculator(QDialog):
    """Fuel calculator"""

    def __init__(self, master):
        super().__init__(master)
        # Base setting
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setWindowIcon(QIcon(APP_ICON))
        self.setWindowTitle("Fuel Calculator")
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.read_only_color = self.palette().window().color().name(QColor.HexRgb)
        self.history_data = minfo.history.consumption

        # Set view
        self.panel_calculator = QWidget()
        self.set_panel_calculator(self.panel_calculator)

        # Panel table
        self.panel_table = QWidget()
        self.set_panel_table(self.panel_table)

        # Load data
        self.reload_data()

        # Layout
        layout_main = QHBoxLayout()
        layout_main.addWidget(self.panel_calculator)
        layout_main.addWidget(self.panel_table)
        self.setLayout(layout_main)
        self.setFixedWidth(self.sizeHint().width())

    def toggle_history_panel(self):
        """Toggle history data panel"""
        if not self.panel_table.isVisible():
            self.panel_table.show()
            self.setFixedWidth(self.sizeHint().width())
            self.button_toggle.setText("Hide history")
        else:
            self.panel_table.hide()
            self.setFixedWidth(self.sizeHint().width())
            self.button_toggle.setText("Show history")

    def add_selected_data(self):
        """Add selected history data"""
        selected_data = self.table_history.selectedItems()
        if not selected_data:
            QMessageBox.warning(
                self, "Error",
                "No data selected.")
            return None

        data_laptime = [data for data in selected_data if data.column() == 1]
        data_fuel = [data for data in selected_data if data.column() == 2]
        data_energy = [data for data in selected_data if data.column() == 3]

        # Send data to calculator
        if data_laptime:
            dataset = [fmt.laptime_string_to_seconds(data.text()) for data in data_laptime]
            output_value = calc.mean(dataset) if len(data_laptime) > 1 else dataset[0]
            self.spinbox_minutes.setValue(output_value // 60)
            self.spinbox_seconds.setValue(output_value % 60)
            self.spinbox_mseconds.setValue(output_value % 1 * 1000)
        if data_fuel:
            dataset = [float(data.text()) for data in data_fuel]
            output_value = calc.mean(dataset) if len(data_fuel) > 1 else dataset[0]
            self.spinbox_fuel_used.setValue(output_value)
        if data_energy:
            dataset = [float(data.text()) for data in data_energy]
            output_value = calc.mean(dataset) if len(data_energy) > 1 else dataset[0]
            self.spinbox_energy_used.setValue(output_value)
        return None

    def reload_data(self):
        """Reload history data"""
        self.refresh_table()
        # Load laptime from last valid lap
        laptime = self.history_data[0][2]
        if laptime > 0 and self.history_data[0][1]:
            self.spinbox_minutes.setValue(laptime // 60)
            self.spinbox_seconds.setValue(laptime % 60)
            self.spinbox_mseconds.setValue(laptime % 1 * 1000)
        # Load tank capacity
        capacity = api.read.vehicle.tank_capacity()
        if capacity:
            self.spinbox_capacity.setValue(self.fuel_units(capacity))
        # Load consumption from last valid lap
        if self.history_data[0][1]:
            fuel_used = self.history_data[0][3]
            self.spinbox_fuel_used.setValue(self.fuel_units(fuel_used))
            energy_used = self.history_data[0][4]
            self.spinbox_energy_used.setValue(energy_used)

    def refresh_table(self):
        """Refresh history data table"""
        self.history_data = minfo.history.consumption
        self.table_history.clear()
        self.table_history.setRowCount(len(self.history_data))
        row_index = 0
        style_invalid = QBrush("#C40", Qt.SolidPattern)

        for lap in self.history_data:
            lapnumber = QTableWidgetItem()
            lapnumber.setText(f"{lap[0]}")
            lapnumber.setTextAlignment(Qt.AlignCenter)
            lapnumber.setFlags(Qt.ItemFlags(0))

            laptime = QTableWidgetItem()
            laptime.setText(calc.sec2laptime(lap[2]))
            laptime.setTextAlignment(Qt.AlignCenter)
            laptime.setFlags(Qt.ItemFlags(33))

            used_fuel = QTableWidgetItem()
            used_fuel.setText(f"{self.fuel_units(lap[3]):.3f}")
            used_fuel.setTextAlignment(Qt.AlignCenter)
            used_fuel.setFlags(Qt.ItemFlags(33))

            used_energy = QTableWidgetItem()
            used_energy.setText(f"{lap[4]:.3f}")
            used_energy.setTextAlignment(Qt.AlignCenter)
            used_energy.setFlags(Qt.ItemFlags(33))

            battery_drain = QTableWidgetItem()
            battery_drain.setText(f"{lap[5]:.3f}")
            battery_drain.setTextAlignment(Qt.AlignCenter)
            battery_drain.setFlags(Qt.ItemFlags(0))

            battery_regen = QTableWidgetItem()
            battery_regen.setText(f"{lap[6]:.3f}")
            battery_regen.setTextAlignment(Qt.AlignCenter)
            battery_regen.setFlags(Qt.ItemFlags(0))

            if not lap[1]:  # set invalid lap text color
                laptime.setForeground(style_invalid)
                used_fuel.setForeground(style_invalid)
                used_energy.setForeground(style_invalid)

            self.table_history.setItem(row_index, 0, lapnumber)
            self.table_history.setItem(row_index, 1, laptime)
            self.table_history.setItem(row_index, 2, used_fuel)
            self.table_history.setItem(row_index, 3, used_energy)
            self.table_history.setItem(row_index, 4, battery_drain)
            self.table_history.setItem(row_index, 5, battery_regen)
            row_index += 1

        self.table_history.setHorizontalHeaderLabels((
            "Lap",
            "Time",
            f"Fuel({self.fuel_unit_text()})",
            "Energy(%)",
            "Drain(%)",
            "Regen(%)"
        ))

    def set_panel_calculator(self, panel):
        """Set panel calculator"""
        frame_laptime = QFrame()
        frame_laptime.setFrameShape(QFrame.StyledPanel)
        frame_laptime.setFixedWidth(PANEL_LEFT_WIDTH)

        frame_fuel = QFrame()
        frame_fuel.setFrameShape(QFrame.StyledPanel)
        frame_fuel.setFixedWidth(PANEL_LEFT_WIDTH)

        frame_race = QFrame()
        frame_race.setFrameShape(QFrame.StyledPanel)
        frame_race.setFixedWidth(PANEL_LEFT_WIDTH)

        frame_output_fuel = QFrame()
        frame_output_fuel.setFrameShape(QFrame.StyledPanel)

        frame_output_energy = QFrame()
        frame_output_energy.setFrameShape(QFrame.StyledPanel)

        frame_output_start_fuel = QFrame()
        frame_output_start_fuel.setFrameShape(QFrame.StyledPanel)

        frame_output_start_energy = QFrame()
        frame_output_start_energy.setFrameShape(QFrame.StyledPanel)

        self.set_input_laptime(frame_laptime)
        self.set_input_fuel(frame_fuel)
        self.set_input_race(frame_race)

        self.set_output_fuel(frame_output_fuel)
        self.set_output_energy(frame_output_energy)
        self.set_output_start_fuel(frame_output_start_fuel)
        self.set_output_start_energy(frame_output_start_energy)

        button_reload = QPushButton("Reload")
        button_reload.clicked.connect(self.reload_data)
        button_reload.setFocusPolicy(Qt.NoFocus)

        self.button_toggle = QPushButton("Hide history")
        self.button_toggle.clicked.connect(self.toggle_history_panel)
        self.button_toggle.setFocusPolicy(Qt.NoFocus)

        layout_split1 = QHBoxLayout()
        layout_split1.addWidget(frame_output_fuel)
        layout_split1.addWidget(frame_output_energy)

        layout_split2 = QHBoxLayout()
        layout_split2.addWidget(frame_output_start_fuel)
        layout_split2.addWidget(frame_output_start_energy)

        layout_calculator = QVBoxLayout()
        layout_calculator.setAlignment(Qt.AlignTop)
        layout_calculator.addWidget(frame_laptime)
        layout_calculator.addWidget(frame_fuel)
        layout_calculator.addWidget(frame_race)
        layout_calculator.addLayout(layout_split1)
        layout_calculator.addLayout(layout_split2)

        layout_button = QHBoxLayout()
        layout_button.addWidget(button_reload, stretch=1)
        layout_button.addStretch(stretch=1)
        layout_button.addWidget(self.button_toggle, stretch=1)

        layout_panel = QVBoxLayout()
        layout_panel.setContentsMargins(0,0,0,0)
        layout_panel.addLayout(layout_calculator)
        layout_panel.addLayout(layout_button)
        panel.setLayout(layout_panel)

    def set_panel_table(self, panel):
        """Set panel table"""
        self.table_history = QTableWidget(self)
        self.table_history.setColumnCount(6)
        self.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_history.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table_history.verticalHeader().setVisible(False)
        self.table_history.setColumnWidth(0, 40)
        self.table_history.setFixedWidth(380)

        button_add = QPushButton("Add selected data")
        button_add.clicked.connect(self.add_selected_data)
        button_add.setFocusPolicy(Qt.NoFocus)

        layout_panel = QVBoxLayout()
        layout_panel.setContentsMargins(0,0,0,0)
        layout_panel.addWidget(self.table_history)
        layout_panel.addWidget(button_add)
        panel.setLayout(layout_panel)

    def carry_over_laptime(self):
        """Carry over lap time value"""
        if self.spinbox_seconds.value() > 59:
            self.spinbox_seconds.setValue(0)
            self.spinbox_minutes.setValue(self.spinbox_minutes.value() + 1)
        elif self.spinbox_seconds.value() < 0:
            if self.spinbox_minutes.value() > 0:
                self.spinbox_seconds.setValue(59)
                self.spinbox_minutes.setValue(self.spinbox_minutes.value() - 1)
            else:
                self.spinbox_seconds.setValue(0)

        if self.spinbox_mseconds.value() > 999:
            self.spinbox_mseconds.setValue(0)
            self.spinbox_seconds.setValue(self.spinbox_seconds.value() + 1)
        elif self.spinbox_mseconds.value() < 0:
            if self.spinbox_seconds.value() > 0 or self.spinbox_minutes.value() > 0:
                self.spinbox_mseconds.setValue(900)
                self.spinbox_seconds.setValue(self.spinbox_seconds.value() - 1)
            else:
                self.spinbox_mseconds.setValue(0)

    def set_input_laptime(self, frame):
        """Set input laptime"""
        self.spinbox_minutes = QSpinBox()
        self.spinbox_minutes.setAlignment(Qt.AlignRight)
        self.spinbox_minutes.setRange(0, 9999)
        self.spinbox_minutes.valueChanged.connect(self.update_input)

        self.spinbox_seconds = QSpinBox()
        self.spinbox_seconds.setAlignment(Qt.AlignRight)
        self.spinbox_seconds.setRange(-1, 60)
        self.spinbox_seconds.valueChanged.connect(self.update_input)

        self.spinbox_mseconds = QSpinBox()
        self.spinbox_mseconds.setAlignment(Qt.AlignRight)
        self.spinbox_mseconds.setRange(-1, 1000)
        self.spinbox_mseconds.setSingleStep(100)
        self.spinbox_mseconds.valueChanged.connect(self.update_input)

        layout_laptime = QGridLayout()
        layout_laptime.setColumnStretch(0, 1)
        layout_laptime.setColumnStretch(2, 1)
        layout_laptime.setColumnStretch(4, 1)

        layout_laptime.addWidget(QLabel("Lap Time:"), 0, 0, 1, 6)

        layout_laptime.addWidget(self.spinbox_minutes, 1, 0)
        layout_laptime.addWidget(QLabel("m"), 1, 1)

        layout_laptime.addWidget(self.spinbox_seconds, 1, 2)
        layout_laptime.addWidget(QLabel("s"), 1, 3)

        layout_laptime.addWidget(self.spinbox_mseconds, 1, 4)
        layout_laptime.addWidget(QLabel("ms"), 1, 5)

        frame.setLayout(layout_laptime)

    def set_input_fuel(self, frame):
        """Set input fuel"""
        self.spinbox_capacity = QDoubleSpinBox()
        self.spinbox_capacity.setRange(0, 9999)
        self.spinbox_capacity.setDecimals(2)
        self.spinbox_capacity.setAlignment(Qt.AlignRight)
        self.spinbox_capacity.valueChanged.connect(self.update_input)

        self.lineedit_fuel_ratio = QLineEdit("0.000")
        self.lineedit_fuel_ratio.setAlignment(Qt.AlignRight)
        self.lineedit_fuel_ratio.setReadOnly(True)
        self.set_read_only_style(self.lineedit_fuel_ratio)

        self.spinbox_fuel_used = QDoubleSpinBox()
        self.spinbox_fuel_used.setRange(0, 9999)
        self.spinbox_fuel_used.setDecimals(3)
        self.spinbox_fuel_used.setSingleStep(0.1)
        self.spinbox_fuel_used.setAlignment(Qt.AlignRight)
        self.spinbox_fuel_used.valueChanged.connect(self.update_input)

        self.spinbox_energy_used = QDoubleSpinBox()
        self.spinbox_energy_used.setRange(0, 100)
        self.spinbox_energy_used.setDecimals(3)
        self.spinbox_energy_used.setSingleStep(0.1)
        self.spinbox_energy_used.setAlignment(Qt.AlignRight)
        self.spinbox_energy_used.valueChanged.connect(self.update_input)

        layout_grid = QGridLayout()
        layout_grid.setColumnStretch(0, 1)
        layout_grid.setColumnStretch(2, 1)

        layout_grid.addWidget(QLabel("Tank Capacity:"), 0, 0, 1, 2)
        layout_grid.addWidget(self.spinbox_capacity, 1, 0)
        layout_grid.addWidget(QLabel(self.fuel_unit_text()), 1, 1)

        layout_grid.addWidget(QLabel("Fuel Ratio:"), 2, 0, 1, 2)
        layout_grid.addWidget(self.lineedit_fuel_ratio, 3, 0)

        layout_grid.addWidget(QLabel("Fuel Consumption:"), 0, 2, 1, 2)
        layout_grid.addWidget(self.spinbox_fuel_used, 1, 2)
        layout_grid.addWidget(QLabel(self.fuel_unit_text()), 1, 3)

        layout_grid.addWidget(QLabel("Energy Consumption:"), 2, 2, 1, 2)
        layout_grid.addWidget(self.spinbox_energy_used, 3, 2)
        layout_grid.addWidget(QLabel("%"), 3, 3)

        frame.setLayout(layout_grid)

    def set_input_race(self, frame):
        """Set input race"""
        self.spinbox_race_minutes = QSpinBox()
        self.spinbox_race_minutes.setRange(0, 9999)
        self.spinbox_race_minutes.setAlignment(Qt.AlignRight)
        self.spinbox_race_minutes.valueChanged.connect(self.update_input)
        self.spinbox_race_minutes.valueChanged.connect(self.disable_race_lap)

        self.spinbox_race_laps = QSpinBox()
        self.spinbox_race_laps.setRange(0, 9999)
        self.spinbox_race_laps.setAlignment(Qt.AlignRight)
        self.spinbox_race_laps.valueChanged.connect(self.update_input)
        self.spinbox_race_laps.valueChanged.connect(self.disable_race_minute)

        self.spinbox_formation = QDoubleSpinBox()
        self.spinbox_formation.setRange(0, 9999)
        self.spinbox_formation.setDecimals(2)
        self.spinbox_formation.setSingleStep(0.1)
        self.spinbox_formation.setAlignment(Qt.AlignRight)
        self.spinbox_formation.valueChanged.connect(self.update_input)

        self.spinbox_pit_seconds = QDoubleSpinBox()
        self.spinbox_pit_seconds.setRange(0, 9999)
        self.spinbox_pit_seconds.setDecimals(1)
        self.spinbox_pit_seconds.setAlignment(Qt.AlignRight)
        self.spinbox_pit_seconds.valueChanged.connect(self.update_input)

        layout_grid = QGridLayout()
        layout_grid.setColumnStretch(0, 1)
        layout_grid.setColumnStretch(2, 1)

        layout_grid.addWidget(QLabel("Race Minutes:"), 0, 0, 1, 2)
        layout_grid.addWidget(self.spinbox_race_minutes, 1, 0)
        layout_grid.addWidget(QLabel("min"), 1, 1)

        layout_grid.addWidget(QLabel("Race Laps:"), 0, 2, 1, 2)
        layout_grid.addWidget(self.spinbox_race_laps, 1, 2)
        layout_grid.addWidget(QLabel("lap"), 1, 3)

        layout_grid.addWidget(QLabel("Formation/Rolling:"), 2, 0, 1, 2)
        layout_grid.addWidget(self.spinbox_formation, 3, 0)
        layout_grid.addWidget(QLabel("lap"), 3, 1)

        layout_grid.addWidget(QLabel("Average Pit Seconds:"), 2, 2, 1, 2)
        layout_grid.addWidget(self.spinbox_pit_seconds, 3, 2)
        layout_grid.addWidget(QLabel("sec"), 3, 3)

        frame.setLayout(layout_grid)

    def set_output_fuel(self, frame):
        """Set output display"""
        self.lineedit_total_fuel = QLineEdit("0.000 ≈ 0")
        self.lineedit_total_fuel.setAlignment(Qt.AlignRight)
        self.lineedit_total_fuel.setReadOnly(True)
        self.set_read_only_style(self.lineedit_total_fuel)

        self.lineedit_pit_stops_fuel = QLineEdit("0.000 ≈ 0")
        self.lineedit_pit_stops_fuel.setAlignment(Qt.AlignRight)
        self.lineedit_pit_stops_fuel.setReadOnly(True)
        self.set_read_only_style(self.lineedit_pit_stops_fuel)

        self.lineedit_total_laps_fuel = QLineEdit("0.000")
        self.lineedit_total_laps_fuel.setAlignment(Qt.AlignRight)
        self.lineedit_total_laps_fuel.setReadOnly(True)
        self.set_read_only_style(self.lineedit_total_laps_fuel)

        self.lineedit_total_minutes_fuel = QLineEdit("0.000")
        self.lineedit_total_minutes_fuel.setAlignment(Qt.AlignRight)
        self.lineedit_total_minutes_fuel.setReadOnly(True)
        self.set_read_only_style(self.lineedit_total_minutes_fuel)

        self.lineedit_end_fuel = QLineEdit("0.000")
        self.lineedit_end_fuel.setAlignment(Qt.AlignRight)
        self.lineedit_end_fuel.setReadOnly(True)
        self.set_read_only_style(self.lineedit_end_fuel)

        self.lineedit_one_less_fuel = QLineEdit("0.000")
        self.lineedit_one_less_fuel.setAlignment(Qt.AlignRight)
        self.lineedit_one_less_fuel.setReadOnly(True)
        self.set_read_only_style(self.lineedit_one_less_fuel)

        layout_output = QGridLayout()

        layout_output.addWidget(QLabel("Total Race Fuel:"), 0, 0, 1, 2)
        layout_output.addWidget(self.lineedit_total_fuel, 1, 0)
        layout_output.addWidget(QLabel(self.fuel_unit_text()), 1, 1)

        layout_output.addWidget(QLabel("Total Pit Stops:"), 2, 0, 1, 2)
        layout_output.addWidget(self.lineedit_pit_stops_fuel, 3, 0)
        layout_output.addWidget(QLabel("pit"), 3, 1)

        layout_output.addWidget(QLabel("Total Laps:"), 4, 0, 1, 2)
        layout_output.addWidget(self.lineedit_total_laps_fuel, 5, 0)
        layout_output.addWidget(QLabel("lap"), 5, 1)

        layout_output.addWidget(QLabel("Total Minutes:"), 6, 0, 1, 2)
        layout_output.addWidget(self.lineedit_total_minutes_fuel, 7, 0)
        layout_output.addWidget(QLabel("min"), 7, 1)

        layout_output.addWidget(QLabel("End Stint Fuel:"), 8, 0, 1, 2)
        layout_output.addWidget(self.lineedit_end_fuel, 9, 0)
        layout_output.addWidget(QLabel(self.fuel_unit_text()), 9, 1)

        layout_output.addWidget(QLabel("One Less Pit Stop:"), 10, 0, 1, 2)
        layout_output.addWidget(self.lineedit_one_less_fuel, 11, 0)
        layout_output.addWidget(QLabel(self.fuel_unit_text()), 11, 1)

        frame.setLayout(layout_output)

    def set_output_energy(self, frame):
        """Set output display"""
        self.lineedit_total_energy = QLineEdit("0.000 ≈ 0")
        self.lineedit_total_energy.setAlignment(Qt.AlignRight)
        self.lineedit_total_energy.setReadOnly(True)
        self.set_read_only_style(self.lineedit_total_energy)

        self.lineedit_pit_stops_energy = QLineEdit("0.000 ≈ 0")
        self.lineedit_pit_stops_energy.setAlignment(Qt.AlignRight)
        self.lineedit_pit_stops_energy.setReadOnly(True)
        self.set_read_only_style(self.lineedit_pit_stops_energy)

        self.lineedit_total_laps_energy = QLineEdit("0.000")
        self.lineedit_total_laps_energy.setAlignment(Qt.AlignRight)
        self.lineedit_total_laps_energy.setReadOnly(True)
        self.set_read_only_style(self.lineedit_total_laps_energy)

        self.lineedit_total_minutes_energy = QLineEdit("0.000")
        self.lineedit_total_minutes_energy.setAlignment(Qt.AlignRight)
        self.lineedit_total_minutes_energy.setReadOnly(True)
        self.set_read_only_style(self.lineedit_total_minutes_energy)

        self.lineedit_end_energy = QLineEdit("0.000")
        self.lineedit_end_energy.setAlignment(Qt.AlignRight)
        self.lineedit_end_energy.setReadOnly(True)
        self.set_read_only_style(self.lineedit_end_energy)

        self.lineedit_one_less_energy = QLineEdit("0.000")
        self.lineedit_one_less_energy.setAlignment(Qt.AlignRight)
        self.lineedit_one_less_energy.setReadOnly(True)
        self.set_read_only_style(self.lineedit_one_less_energy)

        layout_output = QGridLayout()

        layout_output.addWidget(QLabel("Total Race Energy:"), 0, 2, 1, 2)
        layout_output.addWidget(self.lineedit_total_energy, 1, 2)
        layout_output.addWidget(QLabel("%"), 1, 3)

        layout_output.addWidget(QLabel("Total Pit Stops:"), 2, 2, 1, 2)
        layout_output.addWidget(self.lineedit_pit_stops_energy, 3, 2)
        layout_output.addWidget(QLabel("pit"), 3, 3)

        layout_output.addWidget(QLabel("Total Laps:"), 4, 2, 1, 2)
        layout_output.addWidget(self.lineedit_total_laps_energy, 5, 2)
        layout_output.addWidget(QLabel("lap"), 5, 3)

        layout_output.addWidget(QLabel("Total Minutes:"), 6, 2, 1, 2)
        layout_output.addWidget(self.lineedit_total_minutes_energy, 7, 2)
        layout_output.addWidget(QLabel("min"), 7, 3)

        layout_output.addWidget(QLabel("End Stint Energy:"), 8, 2, 1, 2)
        layout_output.addWidget(self.lineedit_end_energy, 9, 2)
        layout_output.addWidget(QLabel("%"), 9, 3)

        layout_output.addWidget(QLabel("One Less Pit Stop:"), 10, 2, 1, 2)
        layout_output.addWidget(self.lineedit_one_less_energy, 11, 2)
        layout_output.addWidget(QLabel("%"), 11, 3)

        frame.setLayout(layout_output)

    def set_output_start_fuel(self, frame):
        """Set output display"""
        self.spinbox_start_fuel = QDoubleSpinBox()
        self.spinbox_start_fuel.setRange(0, 9999)
        self.spinbox_start_fuel.setDecimals(2)
        self.spinbox_start_fuel.setAlignment(Qt.AlignRight)
        self.spinbox_start_fuel.valueChanged.connect(self.validate_starting_fuel)
        self.spinbox_start_fuel.valueChanged.connect(self.update_input)

        self.lineedit_average_refuel = QLineEdit("0.000")
        self.lineedit_average_refuel.setAlignment(Qt.AlignRight)
        self.lineedit_average_refuel.setReadOnly(True)
        self.set_read_only_style(self.lineedit_average_refuel)

        layout_output = QGridLayout()

        layout_output.addWidget(QLabel("Starting Fuel:"), 0, 0, 1, 2)
        layout_output.addWidget(self.spinbox_start_fuel, 1, 0)
        layout_output.addWidget(QLabel(self.fuel_unit_text()), 1, 1)

        layout_output.addWidget(QLabel("Average Refueling:"), 2, 0, 1, 2)
        layout_output.addWidget(self.lineedit_average_refuel, 3, 0)
        layout_output.addWidget(QLabel(self.fuel_unit_text()), 3, 1)

        frame.setLayout(layout_output)

    def set_output_start_energy(self, frame):
        """Set output display"""
        self.spinbox_start_energy = QDoubleSpinBox()
        self.spinbox_start_energy.setRange(0, 100)
        self.spinbox_start_energy.setDecimals(2)
        self.spinbox_start_energy.setAlignment(Qt.AlignRight)
        self.spinbox_start_energy.valueChanged.connect(self.update_input)

        self.lineedit_average_replenish = QLineEdit("0.000")
        self.lineedit_average_replenish.setAlignment(Qt.AlignRight)
        self.lineedit_average_replenish.setReadOnly(True)
        self.set_read_only_style(self.lineedit_average_replenish)

        layout_output = QGridLayout()

        layout_output.addWidget(QLabel("Starting Energy:"), 0, 2, 1, 2)
        layout_output.addWidget(self.spinbox_start_energy, 1, 2)
        layout_output.addWidget(QLabel("%"), 1, 3)

        layout_output.addWidget(QLabel("Average Replenishing:"), 2, 2, 1, 2)
        layout_output.addWidget(self.lineedit_average_replenish, 3, 2)
        layout_output.addWidget(QLabel("%"), 3, 3)

        frame.setLayout(layout_output)

    def update_input(self):
        """Calculate and output results"""
        self.carry_over_laptime()
        tank_capacity = self.spinbox_capacity.value()
        fuel_used = self.spinbox_fuel_used.value()
        fuel_start = self.spinbox_start_fuel.value() if self.spinbox_start_fuel.value() else tank_capacity
        total_race_seconds = self.spinbox_race_minutes.value() * 60
        total_race_laps = self.spinbox_race_laps.value()
        total_formation_laps = self.spinbox_formation.value()
        average_pit_seconds = self.spinbox_pit_seconds.value()
        laptime = (
            self.spinbox_minutes.value() * 60
            + self.spinbox_seconds.value()
            + self.spinbox_mseconds.value() * 0.001
        )
        energy_used = self.spinbox_energy_used.value()
        energy_start = self.spinbox_start_energy.value() if self.spinbox_start_energy.value() else 100

        # Calc fuel ratio
        if cfg.units["fuel_unit"] == "Gallon":
            fuel_used *= 3.785411784
        fuel_ratio = calc.fuel_to_energy_ratio(fuel_used, energy_used)
        self.lineedit_fuel_ratio.setText(f"{fuel_ratio:.3f}")

        # Calc fuel
        if all((laptime, tank_capacity, fuel_used, total_race_seconds + total_race_laps)):
            self.run_calculation(
                "fuel", tank_capacity, fuel_used, fuel_start, total_race_seconds,
                total_race_laps, total_formation_laps, average_pit_seconds, laptime)

        # Calc energy
        if all((laptime, energy_used, total_race_seconds + total_race_laps)):
            self.run_calculation(
                "energy", 100, energy_used, energy_start, total_race_seconds,
                total_race_laps, total_formation_laps, average_pit_seconds, laptime)

    def run_calculation(self, output_type, tank_capacity, consumption, fuel_start,
        total_race_seconds, total_race_laps, total_formation_laps, average_pit_seconds, laptime):
        """Calculate and output results"""
        estimate_pit_counts = 0
        minimum_pit_counts = 0  # minimum pit stop required to finish race
        loop_counts = 10  # max loop limit

        # Total pit seconds depends on estimated pit counts
        # Recalculate and find nearest minimum pit counts on previous loop
        while loop_counts:
            minimum_pit_counts = math.ceil(estimate_pit_counts)
            if total_race_seconds:  # time-type race
                total_pit_seconds = minimum_pit_counts * average_pit_seconds
                total_race_laps = total_formation_laps + calc.time_type_full_laps_remain(
                    0, laptime, total_race_seconds - total_pit_seconds)
            else:  # lap-type race
                total_race_laps = total_formation_laps + total_race_laps

            total_need_frac = calc.total_fuel_needed(total_race_laps, consumption, 0)

            # Keep 1 decimal place for Gallon
            if cfg.units["fuel_unit"] == "Gallon" and output_type == "fuel":
                total_need_full = math.ceil(total_need_frac * 10) / 10
            else:
                total_need_full = math.ceil(total_need_frac)

            amount_refuel = total_need_full - tank_capacity

            amount_curr = min(total_need_full, tank_capacity)

            end_stint_fuel = calc.end_stint_fuel(amount_curr, 0, consumption)

            estimate_pit_counts = calc.end_stint_pit_counts(
                amount_refuel, tank_capacity - end_stint_fuel)

            loop_counts -= 1
            # Set one last loop to revert back to last minimum pit counts
            # If new rounded up minimum pit counts is not enough to finish race
            if (minimum_pit_counts < estimate_pit_counts and
                minimum_pit_counts == math.floor(estimate_pit_counts)):
                loop_counts = 1

            if minimum_pit_counts == math.ceil(estimate_pit_counts):
                break

        total_runlaps = calc.end_stint_laps(total_need_full, consumption)

        total_runmins = calc.end_stint_minutes(total_runlaps, laptime)

        used_one_less = calc.one_less_pit_stop_consumption(
            estimate_pit_counts, tank_capacity, amount_curr, total_race_laps)

        if minimum_pit_counts:
            average_refuel = (total_need_full - fuel_start + minimum_pit_counts * end_stint_fuel) / minimum_pit_counts
        elif fuel_start < total_need_full <= tank_capacity:
            average_refuel = total_need_full - fuel_start
        else:
            average_refuel = 0

        # Output
        if output_type == "fuel":
            self.lineedit_total_fuel.setText(
                f"{total_need_frac:.3f} ≈ {total_need_full}")
            self.lineedit_end_fuel.setText(
                f"{end_stint_fuel:.3f}")
            self.lineedit_pit_stops_fuel.setText(
                f"{max(estimate_pit_counts, 0):.3f} ≈ {max(math.ceil(minimum_pit_counts), 0)}")
            self.lineedit_one_less_fuel.setText(
                f"{max(used_one_less, 0):.3f}")
            self.lineedit_total_laps_fuel.setText(
                f"{total_runlaps:.3f}")
            self.lineedit_total_minutes_fuel.setText(
                f"{total_runmins:.3f}")
            self.lineedit_average_refuel.setText(
                f"{average_refuel:.3f}")
            # Set warning color
            if average_refuel > tank_capacity:  # exceeded tank capacity
                self.lineedit_average_refuel.setStyleSheet("background: #F40;")
            else:
                self.set_read_only_style(self.lineedit_average_refuel)
        else:
            self.lineedit_total_energy.setText(
                f"{total_need_frac:.3f} ≈ {total_need_full}")
            self.lineedit_end_energy.setText(
                f"{end_stint_fuel:.3f}")
            self.lineedit_pit_stops_energy.setText(
                f"{max(estimate_pit_counts, 0):.3f} ≈ {max(math.ceil(minimum_pit_counts), 0)}")
            self.lineedit_one_less_energy.setText(
                f"{max(used_one_less, 0):.3f}")
            self.lineedit_total_laps_energy.setText(
                f"{total_runlaps:.3f}")
            self.lineedit_total_minutes_energy.setText(
                f"{total_runmins:.3f}")
            self.lineedit_average_replenish.setText(
                f"{average_refuel:.3f}")
            # Set warning color
            if average_refuel > tank_capacity:  # exceeded tank capacity
                self.lineedit_average_replenish.setStyleSheet("background: #F40;")
            else:
                self.set_read_only_style(self.lineedit_average_replenish)

    def disable_race_lap(self):
        """Disable race laps if race minutes is set"""
        if self.spinbox_race_minutes.value() > 0:
            if self.spinbox_race_laps.isEnabled():
                self.spinbox_race_laps.setValue(0)
                self.spinbox_race_laps.setDisabled(True)
        else:
            self.spinbox_race_laps.setDisabled(False)

    def disable_race_minute(self):
        """Disable race minutes if race laps is set"""
        if self.spinbox_race_laps.value() > 0:
            if self.spinbox_race_minutes.isEnabled():
                self.spinbox_race_minutes.setValue(0)
                self.spinbox_race_minutes.setDisabled(True)
        else:
            self.spinbox_race_minutes.setDisabled(False)

    @staticmethod
    def fuel_unit_text():
        """Set fuel unit text"""
        if cfg.units["fuel_unit"] == "Gallon":
            return "gal"
        return "L"

    def fuel_units(self, fuel):
        """2 different fuel unit conversion, default is Liter"""
        if cfg.units["fuel_unit"] == "Gallon":
            return calc.liter2gallon(fuel)
        return fuel

    def validate_starting_fuel(self):
        """Validate starting fuel"""
        if self.spinbox_start_fuel.value() > self.spinbox_capacity.value():
            self.spinbox_start_fuel.setValue(self.spinbox_capacity.value())

    def set_read_only_style(self, line_edit):
        """Set read only style"""
        line_edit.setStyleSheet(f"background: {self.read_only_color};")
