from kuix.core.utils import Colors as C

import traceback


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


def _dump_exception(_e: Exception):
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
    dumped = _dump_exception(_e)
    data = ""
    if not no_color:
        data += f"\n{C.BOLD}{C.BLUE}{'-' * 5} Traceback Stack {'-' * 5}{C.END}\n"
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
        self.tracebacks = _dump_exception(_e)
        if self.initial_type is None:
            self.initial_type = type(_e).__name__
            self.initial_msg = str(_e)
        return self

    def add_ctx(self, ctx: str):
        self.ctx.append(ctx)
        return self

    def __str__(self):
        return self.base_msg


class Context:

    def __init__(self, ctx: str):
        self.ctx = ctx
        if not isinstance(ctx, str):
            self.ctx = "Unable to set context. Context must be a string. This line has no relation with the error !"

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        # We return if there is no exception
        if exc_type is None:
            return
        exc_val = cast(exc_val, str(exc_val) if isinstance(exc_val, Exception) else "An error occurred")
        exc_val.add_ctx(self.ctx)
        raise exc_val
