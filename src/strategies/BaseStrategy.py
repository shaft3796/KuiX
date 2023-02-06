"""
Implements the base strategy class.
There is also an implementation of a debug strategy.
"""
from src.strategy_components.BaseStrategyComponent import DebugStrategyComponent, BaseStrategyComponent
from src.core.Logger import LOGGER, STRATEGY
from src.core.Exceptions import *
import dataclasses
import threading
import time


@dataclasses.dataclass
class StrategyStatus:
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"


class BaseStrategy:
    """
    Base strategy class to inherit from.
    """

    def __init__(self, process, identifier: str):
        """
        Constructor to instance a worker for the strategy.
        :param process: KxProcess instance
        :param identifier: Worker identifier
        """
        # Args
        self.identifier = identifier
        self.process = process

        self.thread = None  # Worker thread
        self.worker_status = StrategyStatus.STOPPED  # Worker status
        self.components = {}  # All strategy components

    def add_component(self, name, component):
        """
        Shortcut to add an instanced StrategyComponent to the worker.
        :param name: Recognizable name for the component used to easily access it later.
        :param component: Instance of a component, it's highly recommended to inherit from BaseStrategyComponent.
        :return: the component instance.
        """
        if not isinstance(component, BaseStrategyComponent):
            LOGGER.warning(
                f"Worker {self.identifier} of strategy {self.__class__} tried to add a component that is not "
                f"an instance of BaseStrategyComponent. This can lead to unexpected behaviours, inheritance "
                f"from BaseStrategyComponent is highly recommended.")
        self.components[name] = component
        return component

    def get_status(self):
        """
        Returns the worker status.
        :return: the worker status. (StrategyStatus.STARTING, StrategyStatus.RUNNING, StrategyStatus.STOPPING,
        StrategyStatus.STOPPED)
        """
        return self.worker_status

    # --- Core ---
    def __open__(self):
        """
        Opens the strategy, basically calls __open__ on all components.
        :raises StrategyComponentOpeningError: if an error occurs while opening a component.
        """
        for component in self.components.values():
            try:
                component.__open__()
            except Exception as e:
                raise StrategyComponentOpeningError(f"Error while opening strategy component: {component.__class__}, "
                                                    f"look at the initial exception for more details.") + e

    def __start__(self):
        """
        Starts the strategy, calls __start__ on all components. Start a new thread and run the strategy.
        :raises StrategyComponentStartingError: if an error occurs while starting a component.
        """
        # Checking if the worker is already started
        if self.thread is not None:
            raise WorkerAlreadyStarted("Worker is already started or still running.")
        # Starting components
        for component in self.components.values():
            try:
                component.__start__()
            except Exception as e:
                raise StrategyComponentStartingError(f"Error while starting strategy component: {component.__class__}, "
                                                     f"look at the initial exception for more details.") + e
        # Starting the worker
        self.thread = threading.Thread(target=self.strategy, name=f"STRATEGY_{self.__class__}_{self.identifier}")
        self.worker_status = StrategyStatus.STARTING
        self.thread.start()
        self.worker_status = StrategyStatus.RUNNING

    def __stop__(self):
        """
        Stops the strategy, stop the strategy thread. Calls __stop__ on all components.
        :raises WorkerAlreadyStopped: if the worker is already stopped.
        :raises WorkerStoppingTimeout: if the worker is still running after 10mn.
        :raise StrategyComponentStoppingError: if an error occurs while stopping a component.
        """
        # Checking if the worker is already stopped
        if self.thread is None:
            raise WorkerAlreadyStopped("Worker is already stopped.")
        # Stopping the worker
        self.worker_status = StrategyStatus.STOPPING
        timer = 0
        _ = False
        while self.worker_status != StrategyStatus.STOPPED:
            if timer > 600:
                self.thread = None
                raise WorkerStoppingTimeout("Worker was scheduled to stop but is still running after 10mn. "
                                            "The strategy thread will be dumped but will be still running ! "
                                            "This will leads to unexpected behaviours and performances "
                                            "issues. Please consider adding self.check_status calls "
                                            "in your strategy.")
            if timer > 60 and not _:
                LOGGER.warning(f"Worker {self.identifier} was scheduled to stop but is still running after 60 seconds. "
                               f"Consider adding self.check_status calls in your strategy.", STRATEGY)
                _ = True
            time.sleep(0.1)
            timer += 0.1
        self.thread = None
        # Stopping components
        for component in self.components.values():
            try:
                component.__stop__()
            except Exception as e:
                raise StrategyComponentStoppingError(f"Error while stopping strategy component: {component.__class__}, "
                                                     f"look at the initial exception for more details.") + e

    def __close__(self):
        """
        Close the strategy, call self.__stop__ first. Calls self.close_strategy and __close__ on all components.
        :raises WorkerStoppingError: if an error occurs while stopping the worker.
        :raises StrategyClosingError: if an error occurs while closing the strategy.
        :raises StrategyComponentClosingError: if an error occurs while closing a component.
        """
        # Stop the worker
        try:
            self.__stop__()
        except WorkerAlreadyStopped:
            pass
        except WorkerStoppingTimeout as e:
            LOGGER.warning_exception(e, STRATEGY)
        except Exception as e:
            raise WorkerStoppingError(f"Error while stopping worker: {self.__class__}, "
                                      f"look at the initial exception for more details.") + e

        # Closing the strategy
        try:
            self.close_strategy()
        except Exception as e:
            raise StrategyClosingError(f"Error while closing strategy: {self.__class__}, "
                                       f"look at the initial exception for more details.") + e

        # Closing components
        for component in self.components.values():
            try:
                component.__close__()
            except Exception as e:
                raise StrategyComponentClosingError(f"Error while closing strategy component: {component.__class__}, "
                                                    f"look at the initial exception for more details.") + e

    def check_status(self):
        """
        Calls this method from your strategy to check if the strategy needs to be stopped. If so, it will call
        self.stop_strategy and exit the strategy thread.
        """
        if self.worker_status == StrategyStatus.STOPPING:
            self.stop_strategy()
            self.worker_status = StrategyStatus.STOPPED
            exit(0)  # Exit strategy thread

    # --- Strategy ---
    def strategy(self):
        """
        Override this method to implement your strategy. This method is run in a new thread.
        :return:
        """
        while True:
            pass
            self.check_status()
            time.sleep(1)

    def stop_strategy(self):
        """
        Override this method to implement your strategy stop. This method is called when the strategy is stopped.
        :return:
        """
        pass

    def close_strategy(self):
        """
        Override this method to implement your strategy close. This method is called when the strategy is definitively
        closed.
        """
        pass


class DebugStrategy(BaseStrategy):

    # Constructor for the strategy
    def __init__(self, process, identifier: str):
        super().__init__(process, identifier)

        # Add a component
        self.add_component("debug", DebugStrategyComponent(self))
        # Shortcuts
        self.debug = self.components["debug"]

    # The strategy
    def strategy(self):
        while True:
            self.check_status()
            LOGGER.info(f"DebugStrategy {self.identifier} running.", STRATEGY)
            self.debug.debug_call()
            time.sleep(1)

    def stop_strategy(self):
        LOGGER.info(f"DebugStrategy {self.identifier} stopping.", STRATEGY)

    def close_strategy(self):
        LOGGER.info(f"DebugStrategy {self.identifier} closing.", STRATEGY)
