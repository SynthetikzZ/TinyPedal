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
Wheels module
"""

from collections import deque
import logging

from ._base import DataModule
from ..module_info import minfo
from ..api_control import api
from .. import calculation as calc

MODULE_NAME = "module_wheels"

logger = logging.getLogger(__name__)


class Realtime(DataModule):
    """Wheels data"""

    def __init__(self, config):
        super().__init__(config, MODULE_NAME)

    def update_data(self):
        """Update module data"""
        reset = False
        update_interval = self.active_interval

        while not self.event.wait(update_interval):
            if api.state:

                if not reset:
                    reset = True
                    update_interval = self.active_interval

                    gen_wheel_radius = self.calc_wheel_radius()
                    radius_front, radius_rear = next(gen_wheel_radius)

                # Read telemetry
                speed = api.read.vehicle.speed()
                wheel_rot = api.read.wheel.rotation()

                # Wheel radius
                radius_front, radius_rear = gen_wheel_radius.send((speed, wheel_rot))

                # Wheel slip ratio
                slip_ratio = (
                    calc.slip_ratio(wheel_rot[0], radius_front, speed),
                    calc.slip_ratio(wheel_rot[1], radius_front, speed),
                    calc.slip_ratio(wheel_rot[2], radius_rear, speed),
                    calc.slip_ratio(wheel_rot[3], radius_rear, speed)
                )

                # Output wheels data
                minfo.wheels.radiusFront = radius_front
                minfo.wheels.radiusRear = radius_rear
                minfo.wheels.slipRatio = slip_ratio

            else:
                if reset:
                    reset = False
                    update_interval = self.idle_interval
                    if radius_front != 0 and radius_rear != 0:
                        self.mcfg["last_vehicle_info"] = api.read.check.vehicle_id()
                        self.mcfg["last_wheel_radius_front"] = radius_front
                        self.mcfg["last_wheel_radius_rear"] = radius_rear
                    self.cfg.save()

    def calc_wheel_radius(self):
        """Calc wheel radius"""
        if self.mcfg["last_vehicle_info"] == api.read.check.vehicle_id():
            radius_front = self.mcfg["last_wheel_radius_front"]
            radius_rear = self.mcfg["last_wheel_radius_rear"]
            min_samples_f = 160
            min_samples_r = 160
        else:
            radius_front = 0
            radius_rear = 0
            min_samples_f = 20
            min_samples_r = 20

        samples_slice_f = sample_slice_indices(min_samples_f)
        samples_slice_r = sample_slice_indices(min_samples_r)
        list_radius_f = deque([], 160)
        list_radius_r = deque([], 160)
        speed = 0
        wheel_rot = 0,0,0,0

        while True:
            if speed > 3:
                # Get wheel rotation difference
                # Max rotation vs average, negative = forward, so use min instead of max
                diff_rot_f = calc.min_vs_avg(wheel_rot[0:2])
                diff_rot_r = calc.min_vs_avg(wheel_rot[2:4])
                # Record radius value for targeted rotation difference
                if 0 < diff_rot_f < 0.1:
                    list_radius_f.append(
                        calc.rot2radius(speed, calc.mean(wheel_rot[0:2])))
                if 0 < diff_rot_r < 0.1:
                    list_radius_r.append(
                        calc.rot2radius(speed, calc.mean(wheel_rot[2:4])))
                # Front average wheel radius
                if len(list_radius_f) >= min_samples_f:
                    radius_front = round(
                        calc.mean(sorted(list_radius_f)[samples_slice_f])
                        , 3)
                    if min_samples_f < 160:
                        min_samples_f *= 2  # double sample counts
                        samples_slice_f = sample_slice_indices(min_samples_f)
                # Rear average wheel radius
                if len(list_radius_r) >= min_samples_r:
                    radius_rear = round(
                        calc.mean(sorted(list_radius_r)[samples_slice_r])
                        , 3)
                    if min_samples_r < 160:
                        min_samples_r *= 2
                        samples_slice_r = sample_slice_indices(min_samples_r)
            # Output
            speed, wheel_rot = yield radius_front, radius_rear


def sample_slice_indices(min_samples):
    """Calculate sample slice indices from minimum samples"""
    return slice(int(min_samples * 0.25), int(min_samples * 0.75))
