"""
Implementation of every stuff related to logging and I/O.
"""

from kuix.core.exception import format_exception_stack
from kuix.core.utils import Colors as C

from multiprocessing import Lock
import json
import time
import sys
import os


class KuixIO:

    def __init__(self, path):
        self.std = sys.stdout
        self.fle = open(path, "w")
        self.muted = False  # For testing purposes, mute std

    def write(self, data):
        if not self.muted:
            self.std.write(data)
        self.fle.write(data)

    def flush(self):
        self.std.flush()
        self.fle.flush()

    def close(self):
        self.fle.close()
        self.std.close()

    def getvalue(self):
        # This function is required to pass unit tests on pycharm
        pass


# Define a log object
class Log:
    """
    Class that handles a log.
    """

    def __init__(self, data: (str, Exception), log_type: str, route: str, log_time: str):
        self.log_time = log_time
        self.data = data if isinstance(data, str) else format_exception_stack(data)
        self.type = log_type
        self.route = route

    # --- Formatting methods ---
    def to_dict(self):
        return {"time": self.log_time, "data": self.data, "type": self.type, "route": self.route}

    def to_string(self):
        log = ""
        # Header color
        log += Logger.header_colors[self.type] if self.type in Logger.header_colors else f"{C.END}"
        # Time
        log += f"[{self.log_time}] "
        # Type
        log += f"{self.type} "
        # Route
        log += f"from {self.route}:"
        # Body color
        log += Logger.body_colors[self.type] if self.type in Logger.body_colors else f"{C.END}"
        # Data
        log += f" {self.data}"
        # Reset color
        log += f"{C.END}"
        return log


class Logger:
    """
    Class that handles logging and I/O.
    """

    # --- Static constants ---
    # Log types
    TRACE = "TRACE"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    DEBUG = "DEBUG"
    UNKNOWN = "UNKNOWN"
    # Format
    header_colors = {TRACE: f"{C.END}",
                     INFO: f"{C.BGREEN}{C.BLACK}",
                     WARNING: f"{C.BYELLOW}{C.BLACK}",
                     ERROR: f"{C.BRED}{C.BLACK}",
                     CRITICAL: f"{C.BOLD}{C.BRED}{C.BLACK}",
                     DEBUG: f"{C.BCYAN}{C.BLACK}", }
    body_colors = {TRACE: f"{C.END}",
                   INFO: f"{C.END}{C.GREEN}",
                   WARNING: f"{C.END}{C.YELLOW}",
                   ERROR: f"{C.END}{C.RED}",
                   CRITICAL: f"{C.END}{C.RED}",
                   DEBUG: f"{C.END}{C.CYAN}"}

    def __init__(self):
        # --- I/O ---
        # placeholder to allow the creation of commands input to fix multiprocessing issues
        open("/tmp/kuix_in.txt", "w").close()
        self.inp = open("/tmp/kuix_in.txt", "r")

        # --- Logs ---
        # Lock to prevent race conditions
        self._lock = Lock()
        self.verbose = False  # Display trace logs
        self.log_root_path = None  # Path to the root of the logs
        self.enabled_types = [self.INFO, self.WARNING, self.ERROR, self.CRITICAL, self.DEBUG, self.UNKNOWN]
        self.files = {}  # Files to write logs to
        self.file_logging = False  # If file logging is enabled

    def enable_verbose(self):
        self.verbose = True

    def enable_file_logging(self, path: str):
        self.log_root_path = path if path.endswith("/") else path + "/"
        os.makedirs(self.log_root_path, exist_ok=True)
        for _type in self.enabled_types:
            self.files[_type] = open(self.log_root_path + _type.lower() + ".kuix", "a")
        self.file_logging = True

    # --- Main methods ---
    def log(self, message: (str, Exception), log_type: str = "UNKNOWN", route: str = "UNKNOWN"):
        try:
            # If verbose is disabled, don't log trace logs
            if not self.verbose and log_type == self.TRACE:
                return
            # Create the log
            log_time = time.strftime("%d-%m-%y %H:%M:%S")
            log = Log(message, log_type, route, log_time)

            # --- Writing ---
            with self._lock:
                # Print to stdout
                print(log.to_string())
                # Write to file
                if self.file_logging and log_type in self.files:
                    try:
                        self.files[log_type].write(json.dumps(log.to_dict()) + ",\n")
                        self.files[log_type].flush()
                    except Exception as e:
                        print(f"KUIX: Error while writing to log file: {e}")
        except Exception as e:
            print(f"KUIX: Error while logging: {e}")

    # --- Alias methods ---
    def trace(self, message: (str, Exception), route: str = "UNKNOWN"):
        """Log a trace message.

        :param message: The message to log or the exception to log.
        :param route: The route of the log.
        """
        self.log(message, self.TRACE, route)

    def info(self, message: (str, Exception), route: str = "UNKNOWN"):
        """Log an info message.

        :param message: The message to log or the exception to log.
        :param route: The route of the log.
        """
        self.log(message, self.INFO, route)

    def warning(self, message: (str, Exception), route: str = "UNKNOWN"):
        """Log a warning message.

        :param message: The message to log or the exception to log.
        :param route: The route of the log.
        """
        self.log(message, self.WARNING, route)

    def error(self, message: (str, Exception), route: str = "UNKNOWN"):
        """Log an error message.

        :param message: The message to log or the exception to log.
        :param route: The route of the log.
        """
        self.log(message, self.ERROR, route)

    def critical(self, message: (str, Exception), route: str = "UNKNOWN"):
        """Log a critical message.

        :param message: The message to log or the exception to log.
        :param route: The route of the log.
        """
        self.log(message, self.CRITICAL, route)

    def debug(self, message: (str, Exception), route: str = "UNKNOWN"):
        """Log a debug message.

        :param message: The message to log or the exception to log.
        :param route: The route of the log.
        """
        self.log(message, self.DEBUG, route)

    def unknown(self, message: (str, Exception), route: str = "UNKNOWN"):
        """Log an unknown message.

        :param message: The message to log or the exception to log.
        :param route: The route of the log.
        """
        self.log(message, self.UNKNOWN, route)


def _exception_hook(exc_type, value, traceback):
    logger.critical(value, "EXCEPTION")


def kuix_override():
    sys.stdout = kuix_io
    sys.excepthook = _exception_hook


# --- Setup ---
logger = Logger()
kuix_io = KuixIO("/tmp/kuix_out.txt")
kuix_override()
