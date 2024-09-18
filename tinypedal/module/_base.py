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
Data module base
"""

import logging
import threading

logger = logging.getLogger(__name__)


class DataModule:
    """Data module base"""

    def __init__(self, config: object, module_name: str):
        super().__init__()
        self.module_name = module_name

        # Base config
        self.cfg = config

        # Module config
        self.mcfg = self.cfg.user.setting[module_name]

        # Module update thread
        self.stopped = True
        self.event = threading.Event()

        # Module update interval
        self.active_interval = max(
            self.mcfg["update_interval"],
            self.cfg.compatibility["minimum_update_interval"]) / 1000
        self.idle_interval = max(
            self.active_interval,
            self.mcfg["idle_update_interval"],
            self.cfg.compatibility["minimum_update_interval"]) / 1000

    def start(self):
        """Start update thread"""
        if self.stopped:
            self.stopped = False
            self.event.clear()
            threading.Thread(target=self.update_data, daemon=True).start()
            logger.info("ACTIVE: %s", self.module_name.replace("_", " "))

    def stop(self):
        """Stop update thread"""
        self.event.set()
        self.cfg.active_module_list.pop(self.module_name)
        self.stopped = True
        logger.info("CLOSED: %s", self.module_name.replace("_", " "))

    def update_data(self):
        """Update module data, rewrite in child class"""
