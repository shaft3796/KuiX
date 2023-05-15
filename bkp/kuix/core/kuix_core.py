"""
Implementation of the core class of KuiX.
"""
import os
import time

from kuix.core.event import Events
from kuix.core.exception import GenericException, Context
from kuix.core.ipc import new_hub, Connector, API
from kuix.core.kx_process import KxProcessAPI, new_kx_process, WorkerAlreadyAddedError, UnknownWorkerError, \
    WorkerStateError, UnknownComponentMethodError
from kuix.core.logger import logger
from kuix.core.stateful import StateError
from kuix.core.utils import Lockable
from kuix.kuix_components.base_kuix_component import KuixComponentCoreMethodCallError, BaseKuixComponent

# --- MESSAGES ---
ROUTE = "KUIX_CORE"

NOT_INHERITED_COMPONENT_WARNING = "{}: component <{}> is not inherited from BaseKuixComponent, " \
                                  "this is not recommended, component '{}' will be added anyway."
NOT_CONFIGURED_ERROR = "{}: KuiX is not configured, please call Kuix.load_config() or Kuix.load_json_config() " \
                       "before using KuiX."
ALREADY_CONFIGURED_ERROR = "{}: KuiX is already configured, you can call a config method only once."
NOT_SETUP_ERROR = "{}: KuiX is not set up, please call Kuix.setup() before using KuiX."
CLOSED_ERROR = "{}: KuiX is closed, you can't use it anymore."

FILES_SETUP_ERROR = "{}: Error while setting up the files for KuiX, look at the initial exception " \
                    "for more details."
COMPONENT_CLOSE_ERROR_CTX = "{}: Error while closing the component '{}', look at the initial exception " \
                            "for more details. This error will be ignored."
KX_PROCESS_ALREADY_EXISTS_ERROR = "{}: A process with the identifier '{}' already exists."

UNKNOWN_KX_PROCESS_ERROR = "{}: The kx_id '{}' does not match any existing kx process, " \
                           "please create one using kuix.create_process method."
UNKNOWN_WORKER_ERROR = "{}: The worker '{}' does not match any existing worker, " \
                       "please add one using kuix.add_worker method."
UNKNOWN_COMPONENT_ERROR = "{}: The component '{}' does not match any existing component, " \
                          "please add one using kuix.add_component method."
UNKNOWN_COMPONENT_METHOD_ERROR = "{}: The component '{}' does not have the method '{}', " \
                                    "please check the method name."

# CTX
KUIX_CLOSE_PROCESS_CTX = "{}: Error while closing the process '{}', look at the initial exception " \
                         "for more details."
KUIX_REMOVE_WORKER_CTX = "{}: Error while removing the worker '{}', look at the initial exception " \
                         "for more details."
COMPONENT_OPEN_ERROR_CTX = "{}: Error while setting up the core, look at the initial exception " \
                           "for more details."


# --- EXCEPTIONS ---
class NotConfiguredError(GenericException):
    pass


class AlreadyConfiguredError(GenericException):
    pass


class NotSetupError(GenericException):
    pass


class ClosedError(GenericException):
    pass


class KuixSetupError(GenericException):
    pass


class KxProcessAlreadyExistsError(GenericException):
    pass


class UnknownKxProcessError(GenericException):
    pass


class UnknownComponentError(GenericException):
    pass


# --- CLASSES ---
class KuixAPI(API, Lockable):
    """
    The API of the KuiX core.
    Abstraction of some features.
    """

    def __init__(self, kuix):
        API.__init__(self)
        Lockable.__init__(self)

        self.kuix = kuix

    def add_component(self, component_identifier, component):
        """
        Add an instanced KuixComponent to KuiX.
        :param component_identifier: Unique string identifier for the component.
        :param component: Instance of a component, it's highly recommended to inherit from BaseKuixComponent.
        :return: the component.
        """
        return self.kuix.add_component(component_identifier, component)

    # -- Placeholders for future methods --
    def _load_config(self):
        """
        Load the configuration of KuiX.
        """
        self.kuix._load_config()

    def _load_json_config(self):
        """
        Load the configuration of KuiX.
        """
        self.kuix._load_json_config()

    # -- State Methods --
    def is_configured(self):
        """
        Return True if KuiX is configured, False otherwise.
        """
        return self.kuix.configured

    def is_setup(self):
        """
        Return True if KuiX is set up, False otherwise.
        """
        return self.kuix.is_setup

    def is_closed(self):
        """
        Return True if KuiX is closed, False otherwise.
        """
        return self.kuix.is_closed

    def setup(self):
        """
        Setup KuiX.
        """
        self.kuix.setup()

    def close(self):
        """
        Close KuiX.
        """
        self.kuix.close()

    # -- Process Methods --
    def create_process(self, kx_id: str, *args, **kwargs):
        """
        Create a new KuiX process.

        :param kx_id: The identifier of the KuiX process.
        :param args: Additional arguments to pass to the KuiX process if it was overridden. For advanced usage only.
        :param kwargs: Additional keyword arguments to pass to the KuiX process if it was overridden. For advanced usage only.

        :raises KuixProcessAlreadyExistsError: If a process with the given identifier already exists.
        """
        self.kuix.create_process(kx_id, *args, **kwargs)

    def is_process(self, kx_id: str) -> bool:
        """
        Return True if the kx_id match an existing kx_process.
        """
        return self.kuix.is_process(kx_id)

    def get_process(self, kx_id: str) -> KxProcessAPI:
        """
        Return the KxProcessAPI of the process matching the kx_id

        :param kx_id: The identifier  of the kxprocess.

        :raise UnknownKxProcessError: If the kx_id doesn't match any existing kxprocess.
        """
        return self.kuix.get_process(kx_id)

    def close_process(self, kx_id: str, kill: bool = True):
        """
        Close a kxprocess. All running components and workers will be closed.

        :param kx_id: The identifier of the kxprocess.
        :param kill: Close the process without raising any exceptions if a worker or a component raise one.

        :raise UnknownKxProcessError: If the kx_id doesn't match any existing kxprocess.
        :raise WorkerMethodCallError: If you choose to don't kill the process, raise any exception raised by worker.close call.

        """
        self.kuix.close_process(kx_id, kill)

    # --- ABSTRACTIONS ---
    # -- Call --
    def call_worker_component(self, process_identifier: str, worker_identifier: str, component_identifier: str,
                                method_name: str, *args, **kwargs):
        """
        Call a method of a component of a worker. Allows interaction between kuix components and workers.
        :param process_identifier: The process identifier as a string.
        :param worker_identifier: The worker identifier as a string.
        :param component_identifier: The component identifier as a string, as specified in the worker's definition
        when calling Worker.add_component method.
        :param method_name: The method name as a string.
        :param args: Additional method arguments.
        :param kwargs: Additional method keyword arguments.
        :return: The method return value.

        :raises UnknownKxProcessError: If the process does not exist.
        :raises UnknownWorkerError: If the worker does not exist.
        :raises UnknownComponentError: If the component does not exist.
        :raises UnknownComponentMethodError: If the method does not exist.
        :raises Exception: If the method call raises an exception.
        """
        process_api = self.get_process(process_identifier)
        return process_api.call_worker_component(worker_identifier, component_identifier, method_name, *args, **kwargs)

    def call_kuix_component(self, component_identifier: str, method_name: str, *args, **kwargs):
        """
        Call a method of a kuix component. Allows interaction between kuix components and workers components.
        :param component_identifier: The component identifier as a string, as specified when calling kuix.add_component
        method.
        :param method_name: The method name as a string.
        :param args: Additional method arguments.
        :param kwargs: Additional method keyword arguments.
        :return: The method return value.

        :raises UnknownComponentError: If the component does not exist.
        :raises UnknownComponentMethodError: If the method does not exist.
        :raises Exception: If the method call raises an exception.
        """
        if component_identifier not in self.kuix.components:
            raise UnknownComponentError(UNKNOWN_COMPONENT_ERROR.format(self.kuix.prefix, component_identifier))
        component = self.kuix.components[component_identifier]
        if not hasattr(component, method_name):
            raise UnknownComponentMethodError(UNKNOWN_COMPONENT_METHOD_ERROR.format(self.kuix.prefix,
                                                                                    component_identifier, method_name))
        method = getattr(component, method_name)
        return method(*args, **kwargs)

    # -- Workers Base --
    @Lockable.locked
    def load_worker(self, kx_id, worker):
        """
        Add a worker, open and start it.

        :param kx_id: The identifier of the kx process.
        :param worker: The worker to add.

        :raises WorkerAlreadyAddedError: If the worker is already added.
        :raises WorkerMethodCallError: If the worker open or start method fails.
        """
        if not self.kuix.is_process(kx_id):
            raise UnknownKxProcessError(UNKNOWN_KX_PROCESS_ERROR)
        try:
            self.kuix.get_process(kx_id).load_worker(worker)
            self.kuix.workers[worker.worker_identifier] = kx_id
        except WorkerAlreadyAddedError as e:
            raise e.add_ctx(f"{self.kuix.prefix}: add_worker on {kx_id}")

    @Lockable.locked
    def add_worker(self, kx_id, worker):
        """
        Add a worker to the process.

        :param kx_id: The identifier of the kx process.
        :param worker: The worker to add.

        :raises UnknownKxProcessError: If the kx_id doesn't match an existing kxprocess.
        :raises WorkerAlreadyAddedError: If the worker is already added.
        """
        if not self.kuix.is_process(kx_id):
            raise UnknownKxProcessError(UNKNOWN_KX_PROCESS_ERROR)
        try:
            self.kuix.get_process(kx_id).add_worker(worker)
            self.kuix.workers[worker.worker_identifier] = kx_id
        except WorkerAlreadyAddedError as e:
            raise e.add_ctx(f"{self.kuix.prefix}: add_worker on {kx_id}")

    def is_worker_in_process(self, kx_id, worker_identifier):
        """
        Return True if the worker is added to the process.

        :param kx_id: The identifier of the kx process.
        :param worker_identifier: The worker identifier to check.

        :raises UnknownKxProcessError: If the kx_id doesn't match an existing kxprocess.
        """
        if not self.kuix.is_process(kx_id):
            raise UnknownKxProcessError(UNKNOWN_KX_PROCESS_ERROR)
        return self.kuix.get_process(kx_id).is_worker(worker_identifier)

    def is_worker(self, worker_identifier):
        """
        Return True if the worker is added to KuiX.

        :param worker_identifier: The worker identifier to check.
        """
        return worker_identifier in self.kuix.workers

    @Lockable.locked
    def remove_worker(self, worker_identifier):
        """
        Remove a worker from the process.

        :param worker_identifier: The worker identifier as a string.

        :raises UnknownWorkerError: If the worker does not exist.
        :raises WorkerStateError: If the worker is opened and not closed.
        """
        with Context(KUIX_REMOVE_WORKER_CTX.format(self.kuix.prefix, worker_identifier)):
            self.kuix.get_process(self.get_process_id_of_worker(worker_identifier)).remove_worker(worker_identifier)
            self.kuix.workers.pop(worker_identifier)

    def is_worker_opened(self, worker_identifier):
        """
        Return True if the worker is opened.

        :param worker_identifier: The worker identifier as a string.

        :raises UnknownWorkerError: If the worker does not exist.
        """
        kx_id = self.get_process_id_of_worker(worker_identifier)
        return self.kuix.get_process(kx_id).is_worker_opened(worker_identifier)

    def is_worker_running(self, worker_identifier):
        """
        Return True if the worker is started.

        :param worker_identifier: The worker identifier as a string.

        :raises UnknownWorkerError: If the worker does not exist.
        """
        kx_id = self.get_process_id_of_worker(worker_identifier)
        return self.kuix.get_process(kx_id).is_worker_running(worker_identifier)

    def get_process_id_of_worker(self, worker_identifier):
        """
        Return the process id of the worker.

        :param worker_identifier: The worker identifier as a string.

        :raises UnknownWorkerError: If the worker does not exist.
        """
        if not self.is_worker(worker_identifier):
            raise UnknownWorkerError(UNKNOWN_WORKER_ERROR.format(self.kuix.prefix, worker_identifier))
        return self.kuix.workers[worker_identifier]

    # -- Workers State --
    @Lockable.locked
    def open_worker(self, worker_identifier: str):
        """
        Open a worker.

        :param worker_identifier: The worker identifier as a string.

        :raises UnknownWorkerError: If the worker does not exist.
        :raises WorkerStateError: If the worker is already opened.
        :raises WorkerMethodCallError: If the worker open method fails.
        """
        kx_id = self.get_process_id_of_worker(worker_identifier)
        self.get_process(kx_id).open_worker(worker_identifier)

    @Lockable.locked
    def start_worker(self, worker_identifier: str):
        """
        Start a worker.

        :param worker_identifier: The worker identifier as a string.

        :raises UnknownWorkerError: If the worker does not exist.
        :raises WorkerStateError: If the worker is already started, not opened or closed. You can access the initial exception
        type name through StateError.tracebacks[0]["type"].
        :raises WorkerMethodCallError: If the worker start method fails.
        """
        kx_id = self.get_process_id_of_worker(worker_identifier)
        self.kuix.get_process(kx_id).start_worker(worker_identifier)

    @Lockable.locked
    def stop_worker(self, worker_identifier: str):
        """
        Stop a worker.

        :param worker_identifier: The worker identifier as a string.

        :raises UnknownWorkerError: If the worker does not exist.
        :raises WorkerStateError: If the worker is already stopped, not opened or closed. You can access the initial exception
        type name through StateError.tracebacks[0]["type"].
        :raises WorkerMethodCallError: If the worker stop method fails.
        """
        kx_id = self.get_process_id_of_worker(worker_identifier)
        self.kuix.get_process(kx_id).stop_worker(worker_identifier)

    @Lockable.locked
    def close_worker(self, worker_identifier: str):
        """
        Close a worker and remove it.

        :param worker_identifier: The worker identifier as a string.

        :raises UnknownWorkerError: If the worker does not exist.
        :raises WorkerStateError: If the component is already closed, not opened or running. You can access the initial exception
        type name through StateError.tracebacks[0]["type"].
        :raises WorkerMethodCallError: If the worker close method fails.
        """
        kx_id = self.get_process_id_of_worker(worker_identifier)
        self.kuix.get_process(kx_id).close_worker(worker_identifier)
        self.kuix.workers.pop(worker_identifier)

    @Lockable.locked
    def kill_worker(self, worker_identifier: str):
        """
        Stop, close and remove a worker.

        :param worker_identifier: The worker identifier as a string.

        :raises UnknownWorkerError: If the worker does not exist.
        :raises WorkerMethodCallError: If the worker methods fails.
        """
        kx_id = self.get_process_id_of_worker(worker_identifier)
        self.kuix.get_process(kx_id).kill_worker(worker_identifier)

    # -- Components Base --
    def is_component(self, component_identifier):
        """
        Return True if the component exists.

        :param component_identifier: The component identifier as a string.
        """
        return component_identifier in self.kuix.components

    def get_component(self, component_identifier):
        """
        Return the component.

        :param component_identifier: The component identifier as a string.

        :raises UnknownComponentError: If the component does not exist.
        """
        if not self.is_component(component_identifier):
            raise UnknownComponentError(UNKNOWN_COMPONENT_ERROR.format(self.kuix.prefix, component_identifier))
        return self.kuix.components[component_identifier]

    def remove_component(self, component_identifier):
        """
        Remove a component.

        :param component_identifier: The component identifier as a string.

        :raises UnknownComponentError: If the component does not exist.
        """
        if not self.is_component(component_identifier):
            raise UnknownComponentError(UNKNOWN_COMPONENT_ERROR.format(self.kuix.prefix, component_identifier))
        self.kuix.components.pop(component_identifier)

    # -- Components State --
    def is_component_opened(self, component_identifier):
        """
        Return True if the component is opened.

        :param component_identifier: The component identifier as a string.

        :raises UnknownComponentError: If the component does not exist.
        """
        if not self.is_component(component_identifier):
            raise UnknownComponentError(UNKNOWN_COMPONENT_ERROR.format(self.kuix.prefix, component_identifier))
        return self.kuix.components[component_identifier].is_opened()

    def is_component_running(self, component_identifier):
        """
        Return True if the component is running.

        :param component_identifier: The component identifier as a string.

        :raises UnknownComponentError: If the component does not exist.
        """
        if not self.is_component(component_identifier):
            raise UnknownComponentError(UNKNOWN_COMPONENT_ERROR.format(self.kuix.prefix, component_identifier))
        return self.kuix.components[component_identifier].is_running()

    def is_component_closed(self, component_identifier):
        """
        Return True if the component is closed.

        :param component_identifier: The component identifier as a string.

        :raises UnknownComponentError: If the component does not exist.
        """
        if not self.is_component(component_identifier):
            raise UnknownComponentError(UNKNOWN_COMPONENT_ERROR.format(self.kuix.prefix, component_identifier))
        return self.kuix.components[component_identifier].is_closed()

    # -- Components Methods --
    @Lockable.locked
    def open_component(self, component_identifier: str):
        """
        Called only once to open the component.
        If the component is already opened, this method raises a StateError.

        :param component_identifier: The component identifier as a string.

        :return: The response of the __open__ method.

        :raises KuixComponentCoreMethodCallError: If an exception is raised by the __open__ method.
        :raise StateError: If the component is already opened.
        """
        if not self.is_component(component_identifier):
            raise UnknownComponentError(UNKNOWN_COMPONENT_ERROR.format(self.kuix.prefix, component_identifier))
        self.kuix.components[component_identifier].open()

    @Lockable.locked
    def start_component(self, component_identifier: str):
        """
        Called to start the component.
        If the component is already started, not opened or closed, this method raises a StateError.

        :param component_identifier: The component identifier as a string.

        :return: The response of the __start__ method.

        :raises UnknownComponentError: If the component does not exist.
        :raises KuixComponentCoreMethodCallError: If an exception is raised by the __start__ method.
        :raise StateError: If the component is already started, not opened or closed. You can access the initial exception
        type name through StateError.tracebacks[0]["type"].
        """
        if not self.is_component(component_identifier):
            raise UnknownComponentError(UNKNOWN_COMPONENT_ERROR.format(self.kuix.prefix, component_identifier))
        self.kuix.components[component_identifier].start()

    @Lockable.locked
    def stop_component(self, component_identifier: str):
        """
        Called to stop the component.
        If the component is already stopped, not opened or closed, this method raises a StateError.

        :param component_identifier: The component identifier as a string.

        :return: The response of the __stop__ method.

        :raises UnknownComponentError: If the component does not exist.
        :raises KuixComponentCoreMethodCallError: If an exception is raised by the __stop__ method.
        :raise StateError: If the component is already stopped, not opened or closed. You can access the initial exception
        type name through StateError.tracebacks[0]["type"].
        """
        if not self.is_component(component_identifier):
            raise UnknownComponentError(UNKNOWN_COMPONENT_ERROR.format(self.kuix.prefix, component_identifier))
        self.kuix.components[component_identifier].stop()

    @Lockable.locked
    def close_component(self, component_identifier: str):
        """
        Called only once to close the component.
        If the component is already closed, this method raises a StateError.

        :param component_identifier: The component identifier as a string.

        :return: The response of the __close__ method.

        :raises UnknownComponentError: If the component does not exist.
        :raises KuixComponentCoreMethodCallError: If an exception is raised by the __close__ method.
        :raise StateError: If the component is already closed. You can access the initial exception
        type name through StateError.tracebacks[0]["type"].
        """
        if not self.is_component(component_identifier):
            raise UnknownComponentError(UNKNOWN_COMPONENT_ERROR.format(self.kuix.prefix, component_identifier))
        self.kuix.components[component_identifier].close()

        # Remove the component from the components list
        self.remove_component(component_identifier)

    # -- Events --
    def subscribe(self, event_name: str, callback):
        """
        Subscribe to an event.
        :param str event_name: Event name
        :param callback: Callback

        :raises EventSubscriptionError: If the callback is not callable or if the callback signature is not valid.
        """
        self.kuix.connector.subscribe(event_name, callback)

    def unsubscribe(self, event_name: str, callback):
        """
        Unsubscribe from an event.
        :param str event_name: Event name
        :param callback: Callback
        """
        self.kuix.connector.unsubscribe(event_name, callback)

    def trigger_event(self, event_name: str, *args, **kwargs):
        """
        Trigger an event.
        :param str event_name: Event name
        :param args: Event arguments
        :param kwargs: Event keyword arguments
        """
        self.kuix.connector.trigger_event(event_name, *args, **kwargs)


class Kuix(Lockable):

    def __init__(self, path: str = "./"):
        """
        Instance the core of KuiX. This method will set up files and directories and create placeholders.
        Please consider calling Kuix.load_config() or Kuix.load_json_config to configure KuiX.

        :param path: The path to the KuiX root directory.

        :raises KuixSetupError: If an exception is raised while setting up the files.
        """
        super().__init__()
        # Args
        self.path = path

        # State
        self.prefix = "<KuiX Core>"

        # --- Placeholders ---
        # Core
        self.configured = True  # TODO: modify when a configuration is created;
        self.is_setup = False
        self.is_closed = False

        # Ipc
        self.api = KuixAPI(self)
        self.shared_hub = None
        self.connector = None

        # Components
        self.components = {}  # type dict[name: str, component: BaseKuixComponent]

        # Processes
        self.kx_processes = {}  # type dict[kx_id: str, process: KxProcessAPI]

        # Workers
        self.workers = {}  # type dict[worker_identifier: str, kx_id: str]

        # --- Setup ---
        self._setup_files()

        self.__created__ = None

    def add_component(self, component_identifier, component):
        """
        Add an instanced KuixComponent to KuiX.
        :param component_identifier: Unique string identifier for the component.
        :param component: Instance of a component, it's highly recommended to inherit from BaseKuixComponent.
        :return: the component.
        """

        if not isinstance(component, BaseKuixComponent):
            logger.warning(NOT_INHERITED_COMPONENT_WARNING.format(self.prefix, type(component).__name__,
                                                                  component_identifier), ROUTE)
        self.components[component_identifier] = component
        return component

    # --- Static Decorators ---
    @staticmethod
    def require_configured(func):
        def wrapper(self, *args, **kwargs):
            if not self.configured:
                raise NotConfiguredError(NOT_CONFIGURED_ERROR.format(self.prefix))
            return func(self, *args, **kwargs)

        return wrapper

    @staticmethod
    def require_not_configured(func):
        def wrapper(self, *args, **kwargs):
            if self.configured:
                raise AlreadyConfiguredError(ALREADY_CONFIGURED_ERROR.format(self.prefix))
            return func(self, *args, **kwargs)

        return wrapper

    @staticmethod
    def require_setup(func):
        def wrapper(self, *args, **kwargs):
            if not self.is_setup:
                raise NotSetupError(NOT_SETUP_ERROR.format(self.prefix))
            return func(self, *args, **kwargs)

        return wrapper

    @staticmethod
    def require_not_closed(func):

        def wrapper(self, *args, **kwargs):
            if self.is_closed:
                raise ClosedError(CLOSED_ERROR.format(self.prefix))
            return func(self, *args, **kwargs)

        return wrapper

    # --- Core Methods ---
    def get_api(self) -> KuixAPI:
        """
        Return the API of the KuiX core.

        :return: The API of the KuiX core.
        """
        return self.api

    def _setup_files(self):
        """
        Set up the files and directories of KuiX.

        :raises KuixSetupError: If an exception is raised while setting up the files.
        """
        try:
            if not self.path.endswith('/'):
                self.path += '/'
            os.makedirs(self.path, exist_ok=True)
            os.makedirs(self.path + 'kuix/', exist_ok=True)
            os.makedirs(self.path + 'kuix/logs', exist_ok=True)
            os.makedirs(self.path + 'kuix/persistence', exist_ok=True)
        except Exception as e:
            e = KuixSetupError(FILES_SETUP_ERROR.format(self.prefix)) + e
            raise e
        self.path = f"{self.path}kuix/"

    # -- Placeholders for future methods --
    @require_not_configured
    def _load_config(self):
        """
        Load the configuration of KuiX.
        """
        self.configured = True

    @require_not_configured
    def _load_json_config(self):
        """
        Load the configuration of KuiX.
        """
        self.configured = True

    # -- State Methods --
    @require_configured
    def setup(self):
        """
        Set up the core of KuiX and enable it to be used.
        """
        if self.is_setup:
            return
        # Open all components
        for name in self.components:
            try:
                self.components[name].open()
            except KuixComponentCoreMethodCallError as e:
                raise e.add_ctx(COMPONENT_OPEN_ERROR_CTX.format(self.prefix, self.components[name].prefix))
            except StateError:
                pass
        # --- Setup ---
        # IPC
        self.shared_hub = new_hub()
        self.connector = Connector("main", self.api, self.shared_hub)

        self.is_setup = True

    @require_setup
    @require_not_closed
    @Lockable.locked
    def close(self):
        """
        Close the core of KuiX.
        """
        if self.is_closed:
            return
        # Close all processes
        for kx_id in self.kx_processes:
            self.kx_processes[kx_id].close()

        # Close all components
        for name in self.components:
            try:
                self.components[name].close()
            except KuixComponentCoreMethodCallError as e:
                logger.warning(e.add_ctx(COMPONENT_CLOSE_ERROR_CTX.format(self.prefix, type(self.components[name]))),
                               route=ROUTE)

        # Close IPC
        self.connector.close()

        self.is_closed = True

    # -- Process Methods --
    @require_setup
    @require_not_closed
    @Lockable.locked
    def create_process(self, kx_id: str, *args, **kwargs):
        """
        Create a new KuiX process.

        :param kx_id: The identifier of the KuiX process.
        :param args: Additional arguments to pass to the KuiX process if it was overridden. For advanced usage only.
        :param kwargs: Additional keyword arguments to pass to the KuiX process if it was overridden. For advanced usage only.

        :raises KuixProcessAlreadyExistsError: If a process with the given identifier already exists.
        """
        self.__created__ = False

        def _callback(kx_id):
            self.__created__ = True

        self.connector.subscribe(Events.PROCESS_CREATED, _callback)

        if kx_id in self.kx_processes or kx_id == "main":
            raise KxProcessAlreadyExistsError(KX_PROCESS_ALREADY_EXISTS_ERROR.format(self.prefix, kx_id))
        new_kx_process(kx_id, self.path, self.shared_hub, *args, **kwargs)

        while not self.__created__:
            time.sleep(0.1)

        self.connector.unsubscribe(Events.PROCESS_CREATED, _callback)

        # Bind the API
        p_api = KxProcessAPI(None)
        p_api._enable_remote(kx_id, self.shared_hub)
        self.kx_processes[kx_id] = p_api
        self.connector.add_instanced_api(kx_id, p_api)

    @require_setup
    @require_not_closed
    def is_process(self, kx_id: str) -> bool:
        """
        Return True if the kx_id match an existing kx_process.
        """
        return kx_id in self.kx_processes

    @require_setup
    @require_not_closed
    def get_process(self, kx_id: str) -> KxProcessAPI:
        """
        Return the KxProcessAPI of the process matching the kx_id

        :param kx_id: The identifier  of the kxprocess.

        :raise UnknownKxProcessError: If the kx_id doesn't match any existing kxprocess.
        """
        if not self.is_process(kx_id):
            raise UnknownKxProcessError(UNKNOWN_KX_PROCESS_ERROR.format(self.prefix, kx_id))
        else:
            return self.kx_processes[kx_id]

    @require_setup
    @require_not_closed
    @Lockable.locked
    def close_process(self, kx_id: str, kill: bool = True):
        """
        Close a kxprocess. All running components and workers will be closed.

        :param kx_id: The identifier of the kxprocess.
        :param kill: Close the process without raising any exceptions if a worker or a component raise one.

        :raise UnknownKxProcessError: If the kx_id doesn't match any existing kxprocess.
        :raise WorkerMethodCallError: If you choose to don't kill the process, raise any exception raised by worker.close call.
        """
        with Context(KUIX_CLOSE_PROCESS_CTX.format(self.prefix, kx_id)):
            if kill:
                self.get_process(kx_id).kill()
            else:
                self.get_process(kx_id).close()
            time.sleep(0.1)
            self.kx_processes.pop(kx_id)
            # Clear all workers
            workers = self.workers.copy()
            for worker_id in workers:
                if self.workers[worker_id] == kx_id:
                    self.workers.pop(worker_id)
