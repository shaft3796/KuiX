"""
Implements the base class for all workers
"""
import threading

from bkp.kuix.core.event import Events
from bkp.kuix.worker_components.base_worker_component import BaseWorkerComponent
from bkp.kuix.core.exception import GenericException
from bkp.kuix.core.stateful import Stateful
from bkp.kuix.core.logger import logger

# --- MESSAGES ---
ROUTE = "WORKER_<{}>"

NOT_INHERITED_COMPONENT_WARNING = "{}: component <{}> is not inherited from BaseWorkerComponent, " \
                                  "this is not recommended, component '{}' will be added anyway."

WORKER_OPEN_ERROR = "{}: Error while opening, look at the initial exception " \
                       "for more details."
WORKER_START_ERROR = "{}: Error while starting, look at the initial exception " \
                        "for more details."
WORKER_STOP_ERROR = "{}: Error while stopping, look at the initial exception " \
                       "for more details."
WORKER_CLOSE_ERROR = "{}: Error while closing, look at the initial exception " \
                        "for more details."


# --- EXCEPTIONS ---
class WorkerCoreMethodCallError(GenericException):
    pass


# --- CLASSES ---

class BaseWorker(Stateful):

    def __init__(self, worker_identifier: str):
        """
        Initialize a base worker.
        :param worker_identifier: a unique string identifier for the worker
        """
        super().__init__()

        # Args
        self.worker_identifier = worker_identifier
        self.process_api = None  # PLACEHOLDER

        # Attributes
        self.prefix = f"Worker <{type(self).__name__}> '{self.worker_identifier}'"
        self.thread = None  # Worker thread
        self.components = {}  # All worker components
        self.stop_flag = False  # Flag to stop the worker

        # Aliases
        self.ROUTE = ROUTE.format(type(self).__name__)

    def add_component(self, component_identifier, component):
        """
        Shortcut to add an instanced WorkerComponent to the worker.
        :param component_identifier: Unique string identifier for the component.
        :param component: Instance of a component, it's highly recommended to inherit from BaseWorkerComponent.
        :return:
        """

        if not isinstance(component, BaseWorkerComponent):
            logger.warning(NOT_INHERITED_COMPONENT_WARNING.format(self.prefix, type(component).__name__,
                                                                  component_identifier), self.ROUTE)
        self.components[component_identifier] = component
        return component

    def remove_component(self, component_identifier):
        """
        Shortcut to remove a component from the worker.
        :param component_identifier: Unique string identifier for the component.
        :return:
        """
        if component_identifier in self.components:
            del self.components[component_identifier]

    # --- Core methods ---
    def check(self):
        """
        DO NOT OVERRIDE, called by the strategy to check the worker status.
        :return:
        """
        if self.stop_flag:
            exit(0)

    @Stateful.open_method
    def open(self):
        """
        Called only once to open the worker and its components.
        If the worker is already opened, this method raises a StateError.
        WARNING, DO NOT OVERRIDE, override __open__ method instead.

        :return: The response of the __open__ method.

        :raises WorkerCoreMethodCallError: If an exception is raised by the __open__ method or by a component.
        :raise StateError: If the worker is already opened.
        """
        try:
            # Open components
            for component_identifier, component in self.components.items():
                component.open()

            # Open worker
            self.__open__()
        except Exception as e:
            raise WorkerCoreMethodCallError(WORKER_OPEN_ERROR.format(self.prefix)) + e

        # TRIGGER EVENT
        self.process_api.trigger_event(Events.WORKER_OPENED, self.process_api.get_kx_id(), self.worker_identifier)

    @Stateful.start_method
    def start(self):
        """
        Called to start the worker and its components.
        If the worker is already started, not opened or closed, this method raises a StateError.
        WARNING, DO NOT OVERRIDE, override __start__ method instead.

        :return: The response of the __start__ method.

        :raises WorkerCoreMethodCallError: If an exception is raised by the __start__ method or by a component.
        :raise StateError: If the worker is already started, not opened or closed. You can access the initial exception
        type name through StateError.tracebacks[0]["type"].
        """
        try:
            # Start components
            for component_identifier, component in self.components.items():
                component.start()

            # Start worker
            self.__start__()
        except Exception as e:
            raise WorkerCoreMethodCallError(WORKER_START_ERROR.format(self.prefix)) + e

        # Start thread
        self.thread = threading.Thread(target=self.strategy, name=self.worker_identifier)
        self.stop_flag = False
        self.thread.start()

        # TRIGGER EVENT
        self.process_api.trigger_event(Events.WORKER_STARTED, self.process_api.get_kx_id(), self.worker_identifier)

    @Stateful.stop_method
    def stop(self):
        """
        Called to stop the worker and its components.
        If the worker is already stopped, not opened or closed, this method raises a StateError.
        WARNING, DO NOT OVERRIDE, override __stop__ method instead.

        :return: The response of the __stop__ method.

        :raises WorkerCoreMethodCallError: If an exception is raised by the __stop__ method or by a component.
        :raise StateError: If the worker is already stopped, not opened or closed. You can access the initial exception
        type name through StateError.tracebacks[0]["type"].
        """
        try:
            # Stop worker
            self.__stop__()

            # Stop components
            for component_identifier, component in self.components.items():
                component.stop()
        except Exception as e:
            raise WorkerCoreMethodCallError(WORKER_STOP_ERROR.format(self.prefix)) + e

        # Stop thread
        self.stop_flag = True
        self.thread.join()

        # TRIGGER EVENT
        self.process_api.trigger_event(Events.WORKER_STOPPED, self.process_api.get_kx_id(), self.worker_identifier)

    @Stateful.close_method
    def close(self):
        """
        Called only once to close the worker and its components.
        If the worker is already closed, not opened or running, this method raises a StateError.
        WARNING, DO NOT OVERRIDE, override __close__ method instead.

        :return: The response of the __close__ method.

        :raises WorkerCoreMethodCallError: If an exception is raised by the __close__ method or by a component.
        :raise StateError: If the worker is already closed, not opened or running. You can access the initial exception
        type name through StateError.tracebacks[0]["type"].
        """
        try:
            # Close worker
            self.__close__()

            # Close components
            for component_identifier, component in self.components.items():
                component.close()
        except Exception as e:
            raise WorkerCoreMethodCallError(WORKER_CLOSE_ERROR.format(self.prefix)) + e

        # TRIGGER EVENT
        self.process_api.trigger_event(Events.WORKER_CLOSED, self.process_api.get_kx_id(), self.worker_identifier)

    # --- Abstract methods ---
    def __open__(self):
        """
        Override this method to implement the worker open logic.
        :return:
        """
        pass

    def __start__(self):
        """
        Override this method to implement the worker start logic.
        :return:
        """
        pass

    def __stop__(self):
        """
        Override this method to implement the worker stop logic.
        :return:
        """
        pass

    def __close__(self):
        """
        Override this method to implement the worker close logic.
        :return:
        """
        pass

    def strategy(self):
        """
        Override this method to implement the worker strategy.
        :return:
        """
        while True:
            self.check()
            # Do something
            # ...