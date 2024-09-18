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
Log handler setup
"""

import re
import sys
import logging

from .const import PATH_LOG


LOGGING_FORMAT_CONSOLE = logging.Formatter(
    "%(asctime)s %(levelname)s: %(message)s", datefmt="%H:%M:%S")
LOGGING_FORMAT_FILE = logging.Formatter(
    "%(asctime)s %(levelname)s: %(message)s")
LOGGING_FILENAME = "tinypedal.log"


def new_stream_handler(_logger, stream):
    """Create new stream handler

    Args:
        _logger: logger instance.
        stream: stream object.
    Returns:
        Stream handler
    """
    _handler = logging.StreamHandler(stream)
    _handler.setFormatter(LOGGING_FORMAT_CONSOLE)
    _handler.setLevel(logging.INFO)
    _logger.addHandler(_handler)
    return _handler


def new_file_handler(_logger, filepath: str, filename: str):
    """Create new file handler

    Args:
        _logger: logger instance.
        filepath: log file path.
        filename: log file name.
    Returns:
        File handler.
    """
    _handler = logging.FileHandler(f"{filepath}{filename}")
    _handler.setFormatter(LOGGING_FORMAT_FILE)
    _handler.setLevel(logging.INFO)
    _logger.addHandler(_handler)
    return _handler


def set_logging_level(_logger, log_stream=None, log_level="1") -> None:
    """Set logging level

    Args:
        _logger: logger instance.
        log_stream: log stream object.
        log_level:
            0 = no logging output.
            1 = output log to console only.
            2 = output log to both console & file.
    """
    for _arg in sys.argv:
        if re.match("^--log-level=", _arg):
            log_level = _arg.strip("--log-level=")
            break

    _logger.setLevel(logging.INFO)
    if log_stream is not None:
        new_stream_handler(_logger, log_stream)

    if log_level == "1":
        new_stream_handler(_logger, sys.stdout)
        _logger.info("LOGGING: output to console")
    elif log_level == "2":
        new_stream_handler(_logger, sys.stdout)
        _logger.info("LOGGING: output to console")
        new_file_handler(_logger, PATH_LOG, LOGGING_FILENAME)
        _logger.info("LOGGING: output to %s", LOGGING_FILENAME)
