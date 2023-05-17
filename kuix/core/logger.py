"""
Implements a custom loging system
"""
import sys
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
        self.std = sys.stdout
        self.kuix = open("/tmp/kuix.tmp", "w")

    def write(self, data):
        self.std.write(data)
        self.kuix.write(data)

    def flush(self):
        self.std.flush()
        self.kuix.flush()

    def close(self):
        self.kuix.close()
        self.std.close()


# -- Log --
# - Enum -
class Levels:
    TRACE = "TRACE", Fore.RESET
    INFO = "INFO", Fore.GREEN
    WARNING = "WARNING", Fore.YELLOW
    ERROR = "ERROR", Fore.RED
    CRITICAL = "CRITICAL", Fore.WHITE + Back.RED
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

    def __init__(self):
        super().__init__()
