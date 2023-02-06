"""
This file contains the logging system of KuiX
"""
import sys
import traceback

from src.core.Exceptions import GenericException, cast, format_exception_stack
from src.core.Utils import C
from dataclasses import dataclass
import multiprocessing
import json
import time
import os

# --- Log types and data ---
TRACE = "TRACE"
INFO = "INFO"
WARNING = "WARNING"
ERROR = "ERROR"
DEBUG = "DEBUG"
UNCAUGHT = "UNCAUGHT"


@dataclass
class LogTypes:
    """
    Used by the logger to color the logs
    """
    __type_header_color__ = {TRACE: f"{C.END}", INFO: f"{C.BOLD}{C.BGREEN}{C.BLACK}",
                             WARNING: f"{C.BOLD}{C.BYELLOW}{C.BLACK}",
                             ERROR: f"{C.BOLD}{C.BRED}{C.BLACK}", DEBUG: f"{C.BOLD}{C.BCYAN}{C.BLACK}", }
    __type_body_color__ = {TRACE: f"{C.END}", INFO: f"{C.END}{C.GREEN}", WARNING: f"{C.END}{C.YELLOW}",
                           ERROR: f"{C.END}{C.RED}",
                           DEBUG: f"{C.END}{C.MAGENTA}"}


# -- Logging routes --
CORE = "CORE"
CORE_COMP = "CORE_COMPONENT"
KX_PROCESS = "KX_PROCESS"
KX_PROCESS_COMP = "KX_PROCESS_COMPONENT"
STRATEGY = "STRATEGY"
STRATEGY_COMP = "STRATEGY_COMPONENT"


# LOGGER
class Logger:
    """
    This class is used to log data in the console and in files, this class is automatically instanced and can be
    accessed globally from this module
    """

    def __init__(self):
        """
        Automatic instancing of the logger as a global variable accessible from this module
        """
        # PLACEHOLDER
        self.log_path = None
        self.verbose = False
        self.lock = multiprocessing.Lock()

    # Call to enable file logging
    def set_log_path(self, path: str):
        """
        Call this method to enable log saving to the file system
        :param str path: Path to the log folder
        """
        try:
            self.log_path = path
            # Create log files
            os.makedirs(self.log_path, exist_ok=True)
            # Create log files for each route
            for route in [CORE, CORE_COMP, STRATEGY, STRATEGY_COMP]:
                for log_type in [INFO, WARNING, ERROR, DEBUG]:
                    if not os.path.exists(f"{self.log_path}/{route}_{log_type}.log"):
                        open(f"{self.log_path}/{route}_{log_type}.log", "w").close()
        except Exception as e:
            print("KXT Error: Logger could not be initialized, exiting...")
            raise e

    # Enable verbose mode to log TRACE to the console
    def enable_verbose(self):
        """
        Call this method to enable verbose mode, this will log TRACE to the console
        """
        self.verbose = True

    # --- Core ---
    def log(self, data: str, log_type: str, route: str):
        """
        Log data to the console and to the file system if set_log_path() has been called
        :param str data: Content of the log
        :param log_type: Type of the log (INFO, WARNING, ERROR, DEBUG)
        :param route: Route of the log (CORE, CORE_COMP, STRATEGY, STRATEGY_COMP)
        """
        # Pre check for verbose mode
        if not self.verbose and log_type == TRACE:
            return
        with self.lock:
            color_header = LogTypes.__type_header_color__[log_type]
            color_body = LogTypes.__type_body_color__[log_type]
            log_time = time.strftime("%d-%m-%y %H:%M:%S")

            # One line log
            _log = f"{color_header}[{log_time}] {log_type} from {route}:{color_body} {data}{C.END}"

            # JSON log
            json_log = json.dumps({"time": log_time, "type": log_type, "route": route, "data": data})

            # Logging
            print(_log + '\n', end='')
            if self.log_path is not None and log_type != TRACE:
                for retry in range(3):
                    try:
                        with open(f"{self.log_path}/{route}_{log_type}.log", "a") as f:
                            f.write(json_log + "\n")
                        break
                    except FileNotFoundError:
                        open(f"{self.log_path}/{route}_{log_type}.log", "w").close()

    # --- SHORTCUTS ---
    def trace(self, data: str, route: str):
        """
        Shortcut to directly log data as a TRACE log
        :param data: data of the log
        :param route: data of the log
        """
        self.log(data, TRACE, route)

    def info(self, data: str, route: str):
        """
        Shortcut to directly log data as an INFO log
        :param data: data of the log
        :param route: data of the log
        """
        self.log(data, INFO, route)

    def warning(self, data: str, route: str):
        """
        Shortcut to directly log data as a WARNING log
        :param data: data of the log
        :param route: data of the log
        """
        self.log(data, WARNING, route)

    def error(self, data: str, route: str):
        """
        Shortcut to directly log data as an ERROR log
        :param data: data of the log
        :param route: data of the log
        """
        self.log(data, ERROR, route)

    def debug(self, data: str, route: str):
        """
        Shortcut to directly log data as a DEBUG log
        :param data: data of the log
        :param route: data of the log
        """
        self.log(data, DEBUG, route)

    def warning_exception(self, exception, route: str):
        """
        Shortcut to directly log an Exception as a WARNING log
        :param exception: the Exception
        :param route: the route of the log (CORE, CORE_COMP, STRATEGY, STRATEGY_COMP)
        """
        with self.lock:
            color_header = LogTypes.__type_header_color__["WARNING"]
            color_body = LogTypes.__type_body_color__["WARNING"]
            log_time = time.strftime("%d-%m-%y %H:%M:%S")

            # Console log
            _log = f"{color_header}[{log_time}] WARNING from {route}:{color_body}{C.END}\n"
            _log += format_exception_stack(exception, color=color_body)

            # JSON log
            try:
                json_log = json.dumps({"time": log_time, "type": "WARNING", "route": route, "data":
                    _log})
            except Exception as e:
                self.warning(f"Error while logging and dumping to json exception: {e}", route)

            # Logging
            print(_log, end='')
            if self.log_path:
                for retry in range(3):
                    try:
                        with open(f"{self.log_path}/{route}_WARNING.log", "a") as f:
                            f.write(json_log + "\n")
                        break
                    except FileNotFoundError:
                        open(f"{self.log_path}/{route}_WARNING.log", "w").close()

    def error_exception(self, exception, route: str):
        """
        Shortcut to directly log an Exception as an ERROR log
        :param exception: the Exception
        :param route: the route of the log (CORE, CORE_COMP, STRATEGY, STRATEGY_COMP)
        """
        with self.lock:
            color_header = LogTypes.__type_header_color__["ERROR"]
            color_body = LogTypes.__type_body_color__["ERROR"]
            log_time = time.strftime("%d-%m-%y %H:%M:%S")

            # Console log
            _log = f"{color_header}[{log_time}] ERROR from {route}:{color_body}{C.END}\n"
            _log += format_exception_stack(exception)

            # JSON log
            try:
                json_log = json.dumps({"time": log_time, "type": "ERROR", "route": route, "data":
                    _log})
            except Exception as e:
                self.warning(f"Error while logging and dumping to json exception: {e}", route)

            # Logging
            print(_log, end='')
            if self.log_path:
                for retry in range(3):
                    try:
                        with open(f"{self.log_path}/{route}_ERROR.log", "a") as f:
                            f.write(json_log + "\n")
                        break
                    except FileNotFoundError:
                        open(f"{self.log_path}/{route}_ERROR.log", "w").close()


# Pre instanced logger
LOGGER = Logger()


# Override Exception hook
def hook(exc_type, e, tb):
    LOGGER.error_exception(e, UNCAUGHT)

sys.excepthook = hook
