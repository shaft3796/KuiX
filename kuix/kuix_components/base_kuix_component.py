"""
Implementation of the base class for all kuix components
"""
from kuix.core.exception import GenericException
from kuix.core.logger import logger
from kuix.core.stateful import Stateful

# --- MESSAGES ---
ROUTE = "KUIX_COMPONENT_<{}>"


COMPONENT_OPEN_ERROR = "{}: Error while opening, look at the initial exception " \
                       "for more details."
COMPONENT_START_ERROR = "{}: Error while starting, look at the initial exception " \
                        "for more details."
COMPONENT_STOP_ERROR = "{}: Error while stopping, look at the initial exception " \
                       "for more details."
COMPONENT_CLOSE_ERROR = "{}: Error while closing, look at the initial exception " \
                        "for more details."


# --- EXCEPTIONS ---
class KuixComponentCoreMethodCallError(GenericException):
    pass


# --- CLASSES ---
class BaseKuixComponent(Stateful):

    def __init__(self, kuix_api):
        """
        Initialize the kuix component.

        :param kuix_api: The kuix API.
        """
        super().__init__()

        self.kuix_api = kuix_api
        self.prefix = f"<{type(self).__name__}> component of kuix"
        self.ROUTE = ROUTE.format(type(self).__name__)

    # --- Core methods ---
    @Stateful.open_method
    def open(self):
        """
        Called only once to open the component.
        If the component is already opened, this method raises a StateError.
        WARNING, DO NOT OVERRIDE, override __open__ method instead.

        :return: The response of the __open__ method.

        :raises KuixComponentCoreMethodCallError: If an exception is raised by the __open__ method.
        :raise StateError: If the component is already opened.
        """
        try:
            resp = self.__open__()
        except Exception as e:
            e = KuixComponentCoreMethodCallError(COMPONENT_OPEN_ERROR.format(self.prefix)) + e
            raise e

        return resp

    @Stateful.start_method
    def start(self):
        """
        Called to start the component.
        If the component is already started, not opened or closed, this method raises a StateError.
        WARNING, DO NOT OVERRIDE, override __start__ method instead.

        :return: The response of the __start__ method.

        :raises KuixComponentCoreMethodCallError: If an exception is raised by the __start__ method.
        :raise StateError: If the component is already started, not opened or closed. You can access the initial exception
        type name through StateError.tracebacks[0]["type"].
        """

        try:
            resp = self.__start__()
        except Exception as e:
            e = KuixComponentCoreMethodCallError(COMPONENT_START_ERROR.format(self.prefix)) + e
            raise e

        return resp

    @Stateful.stop_method
    def stop(self):
        """
        Called to stop the component.
        If the component is already stopped, not opened or closed, this method raises a StateError.
        WARNING, DO NOT OVERRIDE, override __stop__ method instead.

        :return: The response of the __stop__ method.

        :raises KuixComponentCoreMethodCallError: If an exception is raised by the __stop__ method.
        :raise StateError: If the component is already stopped, not opened or closed. You can access the initial exception
        type name through StateError.tracebacks[0]["type"].
        """
        try:
            resp = self.__stop__()
        except Exception as e:
            e = KuixComponentCoreMethodCallError(COMPONENT_STOP_ERROR.format(self.prefix)) + e
            raise e

        return resp

    @Stateful.close_method
    def close(self):
        """
        Called only once to close the component.
        If the component is already closed, not opened or running, this method raises a StateError.
        WARNING, DO NOT OVERRIDE, override __close__ method instead.

        :return: The response of the __close__ method.

        :raises KuixComponentCoreMethodCallError: If an exception is raised by the __close__ method.
        :raise StateError: If the component is already closed, not opened or running. You can access the initial exception
        type name through StateError.tracebacks[0]["type"].
        """
        try:
            resp = self.__close__()
        except Exception as e:
            e = KuixComponentCoreMethodCallError(COMPONENT_CLOSE_ERROR.format(self.prefix)) + e
            raise e

        return resp

    # --- Abstract methods ---
    def __open__(self):
        """
        Override this method to implement the component open logic.
        """
        return None

    def __start__(self):
        """
        Override this method to implement the component start logic.
        """
        return None

    def __stop__(self):
        """
        Override this method to implement the component stop logic.
        """
        return None

    def __close__(self):
        """
        Override this method to implement the component close logic.
        """
        return None