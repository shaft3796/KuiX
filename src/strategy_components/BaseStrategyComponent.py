"""
Implements the base strategy component class.
There is also an implementation of a debug strategy component.
"""
from src.core.Logger import LOGGER, STRATEGY_COMP


class BaseStrategyComponent:

    # Constructor for the component
    def __init__(self, worker):
        self.worker = worker

    # --- Core ---
    def __open__(self):
        """
        To override, called to open the component.
        :return:
        """
        pass

    def __start__(self):
        """
        To override, called to start the component.
        :return:
        """
        pass

    def __stop__(self):
        """
        To override, called to stop the component.
        :return:
        """
        pass

    def __close__(self):
        """
        To override, called to close the component.
        :return:
        """
        pass


class DebugStrategyComponent(BaseStrategyComponent):

    # Constructor for the component
    def __init__(self, worker):
        super().__init__(worker)

    # To override, called to start the component
    def __open__(self):
        LOGGER.info(f"DebugStrategyComponent for worker {self.worker.identifier} opened.", STRATEGY_COMP)

    def __start__(self):
        LOGGER.info(f"DebugStrategyComponent for worker {self.worker.identifier} started.", STRATEGY_COMP)

    # To override, called to stop the component
    def __stop__(self):
        LOGGER.info(f"DebugStrategyComponent for worker {self.worker.identifier} stopped.", STRATEGY_COMP)

    # To override, called to close the component
    def __close__(self):
        LOGGER.info(f"DebugStrategyComponent for worker {self.worker.identifier} closed.", STRATEGY_COMP)

    # A debug call
    def debug_call(self):
        LOGGER.info(f"DebugStrategyComponent for worker {self.worker.identifier} debug call.", STRATEGY_COMP)
