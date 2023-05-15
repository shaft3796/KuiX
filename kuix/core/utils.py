"""
Utilities for kuix
"""
from kuix.core.exceptions import GenericException

import threading


# -- Lockable object --
# - Class -
class Lockable:
    """
    Implements a decorator to lock methods for multithreading
    """

    def __init__(self):
        """
        Initializes the locks
        """
        self.locks = {}

    @staticmethod
    def locked(func):
        """
        Decorator to lock a method
        """

        def wrapper(self, *args, **kwargs):
            """
            Wrapper for the method
            """
            if func.__name__ not in self.locks:
                self.locks[func.__name__] = threading.Lock()
            with self.locks[func.__name__]:
                return func(self, *args, **kwargs)

        return wrapper


# -- Stateful object --
# - Exceptions -
class NotBuiltError(GenericException):
    """
    Exception raised when a stateful object is not built
    """

    def __init__(self, prefix: str):
        """
        Initializes the exception
        """
        super().__init__(f"{prefix}: The object is not built, you must build it first.")


class AlreadyBuiltError(GenericException):
    """
    Exception raised when a stateful object is already built
    """

    def __init__(self, prefix: str):
        """
        Initializes the exception
        """
        super().__init__(f"{prefix}: The object is already built, you must build it only once.")


class NotRunningError(GenericException):
    """
    Exception raised when a stateful object is not running
    """

    def __init__(self, prefix: str):
        """
        Initializes the exception
        """
        super().__init__(f"{prefix}: The object is not running, you must start it first.")


class AlreadyRunningError(GenericException):
    """
    Exception raised when a stateful object is already running
    """

    def __init__(self, prefix: str):
        """
        Initializes the exception
        """
        super().__init__(f"{prefix}: The object is already running, you must stop it first.")


class NotDestroyedError(GenericException):
    """
    Exception raised when a stateful object is not destroyed
    """

    def __init__(self, prefix: str):
        """
        Initializes the exception
        """
        super().__init__(f"{prefix}: The object is not destroyed, you must destroy it first.")


class AlreadyDestroyedError(GenericException):
    """
    Exception raised when a stateful object is already destroyed
    """

    def __init__(self, prefix: str):
        """
        Initializes the exception
        """
        super().__init__(f"{prefix}: The object is already destroyed, you must destroy it only once.")


# - Enum -
class State:
    """
    Represents the state of a stateful object
    INITIALIZED: The object is initialized, not built and cannot be started or destroyed.
    BUILT: The object is built, not running and ready to be started.
    RUNNING: The object is built, running and ready to be stopped.
    DESTROYED: The object is destroyed, not running and cannot be started.
    """
    INITIALIZED = 0
    BUILT = 1
    RUNNING = 2
    DESTROYED = 3


# - Class -
class Stateful:
    def __init__(self):
        """
        Initializes the state
        """
        self.prefix = "<Unknown>"  # Placeholder for the prefix
        self.state = State.INITIALIZED

    # -- Check methods --
    def is_built(self) -> bool:
        """
        Checks if the object is built
        """
        return not self.state == State.INITIALIZED

    def is_running(self) -> bool:
        """
        Checks if the object is running
        """
        return self.state == State.RUNNING

    def is_destroyed(self) -> bool:
        """
        Checks if the object is destroyed
        """
        return self.state == State.DESTROYED

    # -- Set methods --
    def set_built(self):
        """
        Sets the object as built
        """
        self.state = State.BUILT

    def set_running(self):
        """
        Sets the object as running
        """
        self.state = State.RUNNING

    def set_destroyed(self):
        """
        Sets the object as destroyed
        """
        self.state = State.DESTROYED

    # -- Check decorators
    @staticmethod
    def require_built(func):
        """
        Decorator to check if the object is built
        """

        def wrapper(self, *args, **kwargs):
            if not self.is_built():
                raise NotBuiltError(self.prefix).add_context("Method: " + func.__name__)
            return func(self, *args, **kwargs)

        return wrapper

    @staticmethod
    def require_not_built(func):
        """
        Decorator to check if the object is not built
        """

        def wrapper(self, *args, **kwargs):
            if self.is_built():
                raise AlreadyBuiltError(self.prefix).add_context("Method: " + func.__name__)
            return func(self, *args, **kwargs)

        return wrapper

    @staticmethod
    def require_running(func):
        """
        Decorator to check if the object is running
        """

        def wrapper(self, *args, **kwargs):
            if not self.is_running():
                raise NotRunningError(self.prefix).add_context("Method: " + func.__name__)
            return func(self, *args, **kwargs)

        return wrapper

    @staticmethod
    def require_not_running(func):
        """
        Decorator to check if the object is not running
        """

        def wrapper(self, *args, **kwargs):
            if self.is_running():
                raise AlreadyRunningError(self.prefix).add_context("Method: " + func.__name__)
            return func(self, *args, **kwargs)

        return wrapper

    @staticmethod
    def require_destroyed(func):
        """
        Decorator to check if the object is destroyed
        """

        def wrapper(self, *args, **kwargs):
            if not self.is_destroyed():
                raise NotDestroyedError(self.prefix).add_context("Method: " + func.__name__)
            return func(self, *args, **kwargs)

        return wrapper

    @staticmethod
    def require_not_destroyed(func):
        """
        Decorator to check if the object is not destroyed
        """

        def wrapper(self, *args, **kwargs):
            if self.is_destroyed():
                raise AlreadyDestroyedError(self.prefix).add_context("Method: " + func.__name__)
            return func(self, *args, **kwargs)

        return wrapper

    # -- Stateful decorators abstractions --
    @staticmethod
    def build_method(func):
        """
        Decorator to build the object
        """

        @Stateful.require_not_built
        def wrapper(self, *args, **kwargs):
            ret = func(self, *args, **kwargs)
            self.set_built()
            return ret

        return wrapper

    @staticmethod
    def start_method(func):
        """
        Decorator to start the object
        """

        @Stateful.require_built
        @Stateful.require_not_running
        @Stateful.require_not_destroyed
        def wrapper(self, *args, **kwargs):
            ret = func(self, *args, **kwargs)
            self.set_running()
            return ret

        return wrapper

    @staticmethod
    def stop_method(func):
        """
        Decorator to stop the object
        """

        @Stateful.require_running
        def wrapper(self, *args, **kwargs):
            ret = func(self, *args, **kwargs)
            self.set_built()
            return ret

        return wrapper

    @staticmethod
    def destroy_method(func):
        """
        Decorator to destroy the object
        """

        @Stateful.require_built
        @Stateful.require_not_running
        @Stateful.require_not_destroyed
        def wrapper(self, *args, **kwargs):
            ret = func(self, *args, **kwargs)
            self.set_destroyed()
            return ret

        return wrapper

# TODO: implements Exceptions
# TODO: implements Logger
# TODO: Unittest for logger, exceptions, utils