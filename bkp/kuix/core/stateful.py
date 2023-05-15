from kuix.core.exception import GenericException

# --- MESSAGES ---
STATEFUL_ALREADY_OPENED = "{}: state error, already opened, open method can only be called once."
STATEFUL_NOT_OPENED = "{}: state error, open method must be called before calling this method."
STATEFUL_ALREADY_RUNNING = "{}: state error, already running, call stop before calling this method."
STATEFUL_NOT_RUNNING = "{}: state error, not running, call start before calling this method."
STATEFUL_ALREADY_CLOSED = "{}: state error, already closed, close method can only be called once and no method can be " \
                            "called after it."
STATE_ERROR = "{}: state error, look at the initial exception for more details."


# --- EXCEPTIONS ---
class StatefulNotOpenedError(GenericException):
    pass


class StatefulAlreadyOpenedError(GenericException):
    pass


class StatefulNotRunningError(GenericException):
    pass


class StatefulAlreadyRunningError(GenericException):
    pass


class StatefulAlreadyClosedError(GenericException):
    pass


class StateError(GenericException):
    pass


# --- CLASSES ---

# State used by workers and components
class Stateful:
    def __init__(self):
        """
        Initialize a stateful object.
        """
        self.prefix = "<Unknown>"  # Placeholder

        self.OPENED = False
        self.RUNNING = False
        self.CLOSED = False

    # --- State Check Decorators ---
    @staticmethod
    def require_not_opened(func):
        """
        Decorator to check if the stateful object is not opened.

        :raise StateError: If the stateful object is opened.
        """
        def wrapper(self, *args, **kwargs):
            if self.OPENED:
                raise StateError(STATE_ERROR.format(self.prefix)) + \
                        StatefulAlreadyOpenedError(STATEFUL_ALREADY_OPENED.format(self.prefix))
            return func(self, *args, **kwargs)

        return wrapper

    @staticmethod
    def require_opened(func):
        """
        Decorator to check if the stateful object is opened.

        :raise StateError: If the stateful object is not opened.
        """
        def wrapper(self, *args, **kwargs):
            if not self.OPENED:
                raise StateError(STATE_ERROR.format(self.prefix)) + \
                        StatefulNotOpenedError(STATEFUL_NOT_OPENED.format(self.prefix))
            return func(self, *args, **kwargs)

        return wrapper

    @staticmethod
    def require_running(func):
        """
        Decorator to check if the stateful object is running.

        :raise StateError: If the stateful object is not running.
        """
        def wrapper(self, *args, **kwargs):
            if not self.RUNNING:
                raise StateError(STATE_ERROR.format(self.prefix)) + \
                        StatefulNotRunningError(STATEFUL_NOT_RUNNING.format(self.prefix))
            return func(self, *args, **kwargs)

        return wrapper

    @staticmethod
    def require_not_running(func):
        """
        Decorator to check if the stateful object is not running.

        :raise StateError: If the stateful object is running.
        """
        def wrapper(self, *args, **kwargs):
            if self.RUNNING:
                raise StateError(STATE_ERROR.format(self.prefix)) + \
                        StatefulAlreadyRunningError(STATEFUL_ALREADY_RUNNING.format(self.prefix))
            return func(self, *args, **kwargs)

        return wrapper

    @staticmethod
    def require_not_closed(func):
        """
        Decorator to check if the stateful object is not closed.

        :raise StateError: If the stateful object is closed.
        """
        def wrapper(self, *args, **kwargs):
            if self.CLOSED:
                raise StateError(STATE_ERROR.format(self.prefix)) + \
                        StatefulAlreadyClosedError(STATEFUL_ALREADY_CLOSED.format(self.prefix))
            return func(self, *args, **kwargs)

        return wrapper

    # --- State Set Decorators ---
    @staticmethod
    def set_opened(func):
        """
        Decorator to set the stateful object as opened after the function call.
        """
        def wrapper(self, *args, **kwargs):
            res = func(self, *args, **kwargs)
            self.OPENED = True
            return res

        return wrapper

    @staticmethod
    def set_running(func):
        """
        Decorator to set the stateful object as running after the function call.
        """
        def wrapper(self, *args, **kwargs):
            res = func(self, *args, **kwargs)
            self.RUNNING = True
            return res

        return wrapper

    @staticmethod
    def set_not_running(func):
        """
        Decorator to set the stateful object as not running after the function call.
        """
        def wrapper(self, *args, **kwargs):
            res = func(self, *args, **kwargs)
            self.RUNNING = False
            return res

        return wrapper

    @staticmethod
    def set_closed(func):
        """
        Decorator to set the stateful object as closed after the function call.
        """
        def wrapper(self, *args, **kwargs):
            res = func(self, *args, **kwargs)
            self.CLOSED = True
            return res

        return wrapper

    # --- Abstractions ---
    @staticmethod
    def open_method(func):
        """
        Abstraction of a set_opened and a require_not_opened decorator.

        :raise StateError: If the stateful object is opened.
        """

        @Stateful.set_opened
        @Stateful.require_not_opened
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)

        return wrapper

    @staticmethod
    def start_method(func):
        """
        Abstraction of a set_running, require_opened, require_not_running and require_not_closed decorator.

        :raises StateError: If the stateful object is not opened, is already running or is closed.
        """

        @Stateful.set_running
        @Stateful.require_opened
        @Stateful.require_not_running
        @Stateful.require_not_closed
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)

        return wrapper

    @staticmethod
    def stop_method(func):
        """
        Abstraction of a set_not_running, require_opened, require_running and require_not_closed decorator.

        :raises StateError: If the stateful object is not opened, is not running or is closed.
        """

        @Stateful.set_not_running
        @Stateful.require_opened
        @Stateful.require_running
        @Stateful.require_not_closed
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)

        return wrapper

    @staticmethod
    def close_method(func):
        """
        Abstraction of a set_closed, require_opened, require_not_closed and require_not_running decorator.

        :raises StateError: If the stateful object is not opened, is already closed or is running.
        """

        @Stateful.set_closed
        @Stateful.require_opened
        @Stateful.require_not_closed
        @Stateful.require_not_running
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)

        return wrapper

    # --- State Check Methods ---
    def is_opened(self):
        return self.OPENED

    def is_running(self):
        return self.RUNNING

    def is_closed(self):
        return self.CLOSED

    # --- State Set Methods ---
    def method_set_opened(self):
        self.OPENED = True

    def method_set_running(self):
        self.RUNNING = True

    def method_set_not_running(self):
        self.RUNNING = False

    def method_set_closed(self):
        self.CLOSED = True
