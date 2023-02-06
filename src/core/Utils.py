"""
This module contains utility classes, functions and stuff for KuiX
"""
import threading
from dataclasses import dataclass
import traceback as tba

# EOF character for socket communication
EOT = "04"
# Message sent to test if a socket connection is still alive
IGNORE = b"PING_TEST_TO_BE_IGNORED"


# Terminal colors
@dataclass
class C:
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


# Workers status
@dataclass
class WorkerStatus:
    """
    Worker status
    """
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    CLOSED = "CLOSED"


# Decorator to run a function in a separate thread
def nonblocking(static_identifier: str = None):
    """
    A decorator.
    A wrapped function when called will run in a separate thread.
    :param str static_identifier: An identifier used to name the thread. If None, the wrapped function will require a
    thread identifier as first argument.
    :return: the wrapped function
    :rtype: callable
    """

    def dynamic_nonblocking(func):
        def wrapper(thread_identifier, *args, **kwargs):
            thread = threading.Thread(target=func, args=args, kwargs=kwargs, name=thread_identifier)
            thread.start()

        return wrapper

    def static_nonblocking(func):
        def wrapper(*args, **kwargs):
            thread = threading.Thread(target=func, args=args, kwargs=kwargs, name=static_identifier)
            thread.start()

        return wrapper

    return dynamic_nonblocking if static_identifier is None else static_nonblocking


# Decorator to add a function as an endpoint by adding a special attribute to it
def Endpoint(_endpoint: str):
    """
    Decorator to add a function as an endpoint by adding a special attribute to it
    :param _endpoint: name of the endpoint
    :return:
    """

    def decorator(function):
        function.__setattr__("faf_endpoint", _endpoint)
        return function

    return decorator


# Decorator to add a function as a blocking endpoint by adding a special attribute to it
def BlockingEndpoint(_endpoint: str):
    """
    Decorator to add a function as an endpoint by adding a special attribute to it
    :param _endpoint: name of the endpoint
    :return:
    """

    def decorator(function):
        function.__setattr__("blocking_endpoint", _endpoint)
        return function

    return decorator


# Decorator used for blocking requests to automatically send the response returned by the callback
def Respond(_endpoint: str):
    """
    Decorator used for blocking requests to automatically send the response returned by the callback
    :param _endpoint: name of the endpoint
    :return: the decorated function
    """

    def decorator(function):

        def wrapper(self, rid, data):
            self.send_response(_endpoint, function(self, rid, data), rid)

        return wrapper

    return decorator

