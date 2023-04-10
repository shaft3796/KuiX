"""
This module contains utility classes, functions and stuff for KuiX
"""
import threading
from dataclasses import dataclass


# Terminal colors
@dataclass
class Colors:
    """
    Pre defined terminal colors codes
    """
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    GRAY = '\033[37m'

    BBLACK = '\033[40m'
    BRED = '\033[41m'
    BGREEN = '\033[42m'
    BYELLOW = '\033[43m'
    BBLUE = '\033[44m'
    BMAGENTA = '\033[45m'
    BCYAN = '\033[46m'
    BGRAY = '\033[47m'

    END = '\033[0m'
    BOLD = '\033[1m'
    ITALIC = '\033[3m'


class Lockable:
    """
    A class with methods that can be locked for multithreading
    """

    def __init__(self):
        self.locks = {}

    @staticmethod
    def locked(func):
        def wrapper(self, *args, **kwargs):
            if func.__name__ not in self.locks:
                self.locks[func.__name__] = threading.Lock()
            with self.locks[func.__name__]:
                return func(self, *args, **kwargs)

        return wrapper
