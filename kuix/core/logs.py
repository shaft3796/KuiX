"""
Implements a custom loging system
"""
import json
import os
import sys
import time
from datetime import datetime

from colorama import Fore, Style, Back

from kuix.core.exceptions import KuixException
from kuix.core.utils import Lockable

BOLD = '\033[1m'
UNDERLINE = '\033[4m'
ITALIC = '\x1B[3m'


# -- Custom IO --
class KuixIO:

    def __init__(self):
        self.kuix = open("/tmp/kuix.tmp", "w")

    def write(self, data):
        sys.__stdout__.write(data)
        self.kuix.write(data)

    def flush(self):
        sys.__stdout__.flush()
        self.kuix.flush()

    def close(self):
        sys.__stdout__.close()
        self.kuix.close()


# -- Log --
# - Enum -
class Levels:
    TRACE = "TRACE", Fore.RESET
    INFO = "INFO", Fore.GREEN
    WARNING = "WARNING", Fore.YELLOW
    ERROR = "ERROR", Fore.RED
    CRITICAL = "CRITICAL", Fore.BLACK + Back.RED
    DEBUG = "DEBUG", Fore.CYAN


# - Defines a log object -
class Log:
    """
    Represents a log object
    """

    def __init__(self, data: (str, Exception), level: str, log_time: int):
        self.log_time = log_time
        self.data = '\n' + data.format(level[1]) if isinstance(data, KuixException) else data
        self.level = level

    # --- Formatting methods ---
    def to_dict(self):
        return {"time": self.log_time, "data": self.data, "level": self.level[0]}

    def to_string(self):
        # Timestamp
        log = f"{ITALIC}{self.level[1]}[{datetime.fromtimestamp(self.log_time).strftime('%Y/%m/%d %H:%M:%S')}]{Style.RESET_ALL} "
        # level
        log += f"{self.level[1]}{BOLD}{UNDERLINE}{self.level[0]}{Style.RESET_ALL}{self.level[1]}: "
        # Data
        log += f" {self.data}{Style.RESET_ALL}"
        return log


# -- Logger --
class Logger(Lockable):

    def __init__(self, path=None):
        """
        Initializes the logger.
        :param path: None by default, if modified, the logger will use this path as the root path to save logs.

        """
        super().__init__()

        # --- Logs ---
        self.is_verbose = False
        self.is_debug = False

        # -- Persistence --
        self.root_path = path if path is None else (path if path.endswith("/") else path + "/")
        self.files = {}

        if self.root_path is not None:
            os.makedirs(self.root_path, exist_ok=True)
            for level in Levels.__dict__.keys():
                if not level.startswith("_"):
                    self.files[level] = open(self.root_path + level.lower() + ".json", "a")

    def enable_verbose(self):
        """
        Enables verbose mode.
        """
        self.is_verbose = True

    def enable_debug(self):
        """
        Enables debug mode.
        """
        self.is_debug = True

    @Lockable.locked
    def log(self, data: (str, Exception), level=Levels.INFO):
        """
        Logs data to the console and to the log files.
        :param data: Data to be logged, a string or an exception.
        :param level: Level of the log, import src.core.logger.Levels to use the predefined levels.
        :raises KuixException: If the level is not valid.
        """
        if level not in Levels.__dict__.values():
            raise KuixException(f"Invalid log level: {level}, use src.core.logger.Levels to use the predefined levels.")

        if (level == Levels.DEBUG and not self.is_debug) or (level == Levels.TRACE and not self.is_verbose):
            return

        try:
            log = Log(data, level, int(time.time()))
            # - Terminal -
            print(log.to_string())

            # - Files -
            if self.root_path is not None:
                try:
                    self.files[level[0]].write(json.dumps(log.to_dict(), indent=0) + "\n")

                    # Flush
                    self.files[level[0]].flush()
                except Exception as e:
                    print(f"Error while writing to log file: {e}")
        except Exception as e:
            print(f"Error while logging: {e}")

    # --- Shortcuts ---
    def trace(self, data: (str, Exception)):
        self.log(data, Levels.TRACE)

    def info(self, data: (str, Exception)):
        self.log(data, Levels.INFO)

    def warning(self, data: (str, Exception)):
        self.log(data, Levels.WARNING)

    def error(self, data: (str, Exception)):
        self.log(data, Levels.ERROR)

    def critical(self, data: (str, Exception)):
        self.log(data, Levels.CRITICAL)

    def debug(self, data: (str, Exception)):
        self.log(data, Levels.DEBUG)

    # --- Destructor ---
    def __del__(self):
        for file in self.files.values():
            file.close()


def _exception_hook(exc_type, value, traceback):
    try:
        logger.critical(value)
    except Exception as e:
        print(f"Error while logging: {e}")


def kuix_override():
    sys.stdout = kuix_io
    sys.excepthook = _exception_hook


# -- Global --
kuix_io = KuixIO()
logger = Logger()
kuix_override()
