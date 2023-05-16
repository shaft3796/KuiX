"""
Implementation of an enhanced exception system.
Each exception is a class that inherits from KuixException.
The KuixException.contextualize method allows to add context string to the exception to easily debug and track execution flow.
The KuixException implements a + operator to chain exceptions. This replace the raise ... from ... syntax.
"""
import traceback

from colorama import Fore, Style


# -- Generic Exception Class --
class KuixException(Exception):

    def __init__(self, message: str = "An exception occured."):
        """
        :param message: Base message of the exception.
        """
        super().__init__(message)
        self.base_message = message

        self.context = []  # Store the context of the exception as a list of strings
        self.exceptions = []  # Store the exceptions chain as a list of KuixException

    def __add__(self, _e: Exception):
        """
        :param _e: Exception to be added to the cause chain
        :return: self
        """
        if not isinstance(_e, KuixException):
            _e = KuixException(str(_e))
        self.exceptions.append(_e)
        return self

    def contextualize(self, context: str):
        """
        :param context: Context to be added to the exception
        :return: self
        """
        self.context.append(context)
        return self

    def __str__(self):
        return self.base_message

    def format(self, color=Fore.LIGHTRED_EX):
        """
        :param color: Color of the exception message, empty string to disable color
        :return: Formatted exception message
        """
        HEADER = Fore.BLUE if color else ""
        RESET = Fore.RESET if color else ""
        BOLD_COLOR = color + "\033[1m" if color else ""
        MESSAGE = Fore.LIGHTCYAN_EX if color else ""
        CONTEXT = Fore.LIGHTYELLOW_EX + "\033[3m" if color else ""

        def _format(_e):
            _data = ""
            # Exception Traceback
            frames = traceback.format_tb(_e.__traceback__)
            for frame in frames:
                _data += f"{color}{frame}{RESET}"
            # Exception Message
            _data += f"{MESSAGE}{_e.base_message}{RESET}\n"
            # Exception Context
            if len(_e.context) > 0:
                for ctx in _e.context:
                    _data += f"{CONTEXT}> {ctx}{RESET}\n"
            return _data

        # Traceback Header
        data = f"{HEADER}{'-' * 5} Traceback Chain {'-' * 5}{RESET}\n"

        # Exception chain
        cpy = self.exceptions.copy()
        cpy.reverse()
        for i, e in enumerate(cpy):
            # Exception Header
            data += f"{BOLD_COLOR}{'Initial exception:' if i == 0 else f'Exception {i}:'} {e.__class__.__name__}{RESET}\n"
            data += _format(e)
            data += "\n"

        # Final Exception Header
        data += f"{BOLD_COLOR}Final exception: {self.__class__.__name__}{RESET}\n"
        data += _format(self)
        data += "\n"

        return data


# -- Context Manager to handle exceptions contextualization --
class Contextualize:

    def __init__(self, context: str):
        self.context = context
        if not isinstance(context, str):
            self.context = "Unable to set context. Context must be a string. This line has no relation with the error !"

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        # We return if there is no exception or if the exception is not a KuixException
        if exc_type is None or not issubclass(exc_type, KuixException):
            return
        exc_val.contextualize(self.context)
        raise exc_val