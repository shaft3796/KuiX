"""
Contains all the exceptions used in the project.
"""
import traceback
import traceback as tba

from src.core.Utils import C


def deserialize(e: dict):
    """
    Deserializes a dictionary to a GenericException
    :param e:
    :return:
    """
    _e = globals()[e["type"]](e["base_msg"])
    _e.ctx = e["ctx"]
    _e.tracebacks = e["tracebacks"]
    _e.initial_type = e["initial_type"]
    _e.initial_msg = e["initial_msg"]
    return _e


def cast(e, msg="An error occurred", e_type=None):
    """
    Casts an exception to a GenericException or to a given exception type if the exception is not a GenericException
    :param e: the exception to cast
    :param msg: Added when initializing a generic exception, added to the context of the given exception
    if it is already a GenericException
    :param e_type: type of the return exception if the given exception is not a GenericException
    :return: the cast exception
    """
    return e if isinstance(e, GenericException) else (GenericException(msg) + e if e_type is None else e_type(msg) + e)


def dump_exception(_e: Exception):
    if isinstance(_e, GenericException):
        return [{"base_msg": _e.base_msg,
                 "type": type(_e).__name__,
                 "traceback_frames": traceback.format_tb(_e.__traceback__),
                 "ctx": _e.ctx}] + _e.tracebacks
    else:
        return [{"base_msg": _e.args[0] if len(_e.args) > 0 else "An error occurred",
                 "type": type(_e).__name__,
                 "traceback_frames": traceback.format_tb(_e.__traceback__),
                 "ctx": []}]


def format_exception_stack(_e: Exception, color=C.RED, no_color=False):
    """dumped = dump_exception(_e)
    print(f"{C.BOLD}{C.BLUE}{'-' * 5} Traceback Stack {'-' * 5}{C.END}")
    i = 0
    for j in range(len(dumped) - 1, -1, -1):
        part = dumped[j]
        print(f"{color}{C.BOLD}{f'Initial exception:' if i == 0 else f'Exception {i}:'}{C.END}")
        i += 1
        for k in range(len(part["traceback_frames"])):
            frame = part["traceback_frames"][k]
            print(f"{color}{C.ITALIC}{frame}{C.END}", end="" if k != len(part["traceback_frames"]) else "\n")
        print(f"{C.CYAN}'{part['type']}': {C.END}{part['base_msg']}")
        if len(part["ctx"]) > 0:
            for ctx in part["ctx"]:
                print(f"{color}>{C.END}\t{C.ITALIC}{ctx}{C.END}")
        print()
    print(f"{C.BOLD}{C.BLUE}{'-' * 5} Messages Stack {'-' * 5}{C.END}")
    i = 0
    for j in range(len(dumped) - 1, -1, -1):
        part = dumped[j]
        print(f"{color}{f'Initial exception:' if i == 0 else f'Exception {i}:'}{C.END}", end=" ")
        i += 1
        print(f"{C.CYAN}'{part['type']}': {C.END}{part['base_msg']}")
    print()"""
    dumped = dump_exception(_e)
    data = ""
    if not no_color:
        data += f"{C.BOLD}{C.BLUE}{'-' * 5} Traceback Stack {'-' * 5}{C.END}\n"
        i = 0
        for j in range(len(dumped) - 1, -1, -1):
            part = dumped[j]
            data += f"{color}{C.BOLD}{f'Initial exception:' if i == 0 else f'Exception {i}:'}{C.END}\n"
            i += 1
            for k in range(len(part["traceback_frames"])):
                frame = part["traceback_frames"][k]
                data += f"{color}{C.ITALIC}{frame}{C.END}" if k != len(part["traceback_frames"]) else "\n"
            data += f"{C.CYAN}'{part['type']}': {C.END}{part['base_msg']}\n"
            if len(part["ctx"]) > 0:
                for ctx in part["ctx"]:
                    data += f"{color}>{C.END}\t{C.ITALIC}{ctx}{C.END}\n"
            data += "\n"
        data += f"{C.BOLD}{C.BLUE}{'-' * 5} Messages Stack {'-' * 5}{C.END}\n"
        i = 0
        for j in range(len(dumped) - 1, -1, -1):
            part = dumped[j]
            data += f"{color}{f'Initial exception:' if i == 0 else f'Exception {i}:'}{C.END} "
            i += 1
            data += f"{C.CYAN}'{part['type']}': {C.END}{part['base_msg']}\n"
        data += "\n"
    else:
        data += f"{'-' * 5} Traceback Stack {'-' * 5}\n"
        i = 0
        for j in range(len(dumped) - 1, -1, -1):
            part = dumped[j]
            data += f"{f'Initial exception:' if i == 0 else f'Exception {i}:'}\n"
            i += 1
            for k in range(len(part["traceback_frames"])):
                frame = part["traceback_frames"][k]
                data += f"{frame}" if k != len(part["traceback_frames"]) else "\n"
            data += f"'{part['type']}': {part['base_msg']}\n"
            if len(part["ctx"]) > 0:
                for ctx in part["ctx"]:
                    data += f">{ctx}\n"
            data += "\n"
        data += f"{'-' * 5} Messages Stack {'-' * 5}\n"
        i = 0
        for j in range(len(dumped) - 1, -1, -1):
            part = dumped[j]
            data += f"{f'Initial exception:' if i == 0 else f'Exception {i}:'} "
            i += 1
            data += f"'{part['type']}': {part['base_msg']}\n"
        data += "\n"
    return data


class GenericException(Exception):

    def __init__(self, msg: str = "An error occurred."):
        """
        :param msg: Base message.
        """
        # Base message of the exception
        self.base_msg = msg
        # List of specifically formatted tracebacks returned by dump_exception method
        self.tracebacks = []
        # Context
        self.ctx = []
        # Initial exception to programmatically access the first exception raised
        self.initial_type = None
        self.initial_msg = None

    def __add__(self, _e: Exception):
        """
        :param _e: Exception to be added to the cause chain
        :return: self
        """
        self.tracebacks = dump_exception(_e)
        self.initial_type = type(_e).__name__
        self.initial_msg = str(_e)
        return self

    def add_ctx(self, ctx: str):
        self.ctx.append(ctx)
        return self

    def serialize(self):
        return {
            "type": type(self).__name__,
            "base_msg": self.base_msg,
            "tracebacks": self.tracebacks,
            "ctx": self.ctx,
            "initial_type": self.initial_type,
            "initial_msg": self.initial_msg,
        }

    def __str__(self):
        return self.base_msg


# --- EVENTS ---
class EventCallbackError(GenericException):
    pass


# --- SOCKET EXCEPTIONS ---

# Server
class SocketServerBindError(GenericException):
    pass


class SocketServerAcceptError(GenericException):
    pass


class SocketServerClientNotFound(Exception):
    pass


class SocketServerListeningConnectionError(GenericException):
    pass


class SocketServerSendError(GenericException):
    pass


class SocketServerCloseError(GenericException):
    pass


class SocketServerEventCallbackError(GenericException):
    pass


# Client
class SocketClientConnectionError(GenericException):
    pass


class SocketClientListeningError(GenericException):
    pass


class SocketClientSendError(GenericException):
    pass


class SocketClientCloseError(GenericException):
    pass


class SocketClientEventCallbackError(GenericException):
    pass


# --- IPC ---

class UnknownEndpoint(Exception):
    pass


class UnknownRid(Exception):
    pass


class UnknownRequestType(Exception):
    pass


class EventSubscriptionError(Exception):
    pass


# Server
class IpcServerRequestHandlerError(GenericException):
    pass


class ClientIdentifierNotFoundError(GenericException):
    pass


# Client
class IpcClientRequestHandlerError(GenericException):
    pass


# --- PROCESS ---
class KxProcessComponentImportError(GenericException):
    pass


class KxProcessComponentInitError(GenericException):
    pass


class KxProcessComponentNotFoundError(GenericException):
    pass


class KxProcessComponentMethodCallError(GenericException):
    pass


class KxProcessStrategyImportError(GenericException):
    pass


class StrategyNotFoundError(Exception):
    pass


class WorkerAlreadyExistsError(Exception):
    pass


class WorkerNotFoundError(Exception):
    pass


class WorkerInitError(GenericException):
    pass


class WorkerMethodCallError(GenericException):
    pass


# --- Strategy & strategy components ---
class StrategyComponentOpeningError(GenericException):
    pass


class StrategyComponentStartingError(GenericException):
    pass


class StrategyComponentStoppingError(GenericException):
    pass


class StrategyComponentClosingError(GenericException):
    pass


class WorkerAlreadyStarted(Exception):
    pass


class WorkerAlreadyStopped(Exception):
    pass


class WorkerStoppingTimeout(Exception):
    pass


class WorkerStoppingError(GenericException):
    pass


class StrategyClosingError(GenericException):
    pass


# --- Core ---
class CoreSetupError(GenericException):
    pass


class CoreConfigLoadError(GenericException):
    pass


class CoreConfigGenerationError(GenericException):
    pass


class CoreNotConfigured(Exception):
    pass


class CoreAlreadyConfigured(Exception):
    pass


class CoreClosingError(GenericException):
    pass


class CoreNotStarted(Exception):
    pass


class CoreAlreadyStarted(Exception):
    pass


class ProcessAlreadyExists(Exception):
    pass


class ProcessNotFound(Exception):
    pass


class ProcessLaunchError(Exception):
    pass


class StrategyAlreadyAdded(Exception):
    pass


class ProcessComponentAlreadyAdded(Exception):
    pass


class StrategyNotAdded(Exception):
    pass
