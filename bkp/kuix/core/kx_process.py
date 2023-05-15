"""
Implementation of the KXProcess class. This class is used to manage workers in a process.
"""
import threading

from kuix.core.exception import GenericException, Context
from kuix.core.ipc import Connector, API
from kuix.core.event import Events
import os

# --- MESSAGES ---
ROUTE = "KX_PROCESS_'{}'"

WORKER_CLOSE_GENERIC_ERROR = "KxProcess<'{}'>: Error while closing worker<'{}'>, look at the logs for more details."
PROCESS_KILLED = "KxProcess<'{}'>: successfully killed."

WORKER_ALREADY_ADDED_ERROR = "KxProcess<'{}'>: worker '{}' is already added."

WORKER_DOES_NOT_EXIST_ERROR = "KxProcess<'{}'>: worker '{}' does not exist."

WORKER_NOT_CLOSED_ERROR = "KxProcess<'{}'>: worker '{}' is not closed."

UNKNOWN_WORKER_COMPONENT_ERROR = "KxProcess<'{}'>: unknown component '{}' for worker '{}'."
UNKNOWN_WORKER_COMPONENT_METHOD_ERROR = "KxProcess<'{}'>: unknown method '{}' for component '{}' of worker '{}'."

# State
WORKER_ALREADY_OPENED_ERROR = "KxProcess<'{}'>: worker '{}' is already opened."
WORKER_ALREADY_RUNNING_ERROR = "KxProcess<'{}'>: worker '{}' is already started."
WORKER_ALREADY_CLOSED_ERROR = "KxProcess<'{}'>: worker '{}' is already closed."
WORKER_RUNNING_ERROR = "KxProcess<'{}'>: worker '{}' is running."
WORKER_NOT_OPENED_ERROR = "KxProcess<'{}'>: worker '{}' is not opened."
WORKER_NOT_RUNNING_ERROR = "KxProcess<'{}'>: worker '{}' is not started."

# -- Context --
# Misc
CORE_CALL_FAILED_CTX = "KxProcess<'{}'>: This error occurred while calling a custom method of KuiX: {}"
# Worker State
WORKER_IS_OPEN_CTX = "KxProcess<'{}'>: This error occurred while checking if the worker '{}' is opened."
WORKER_IS_RUNNING_CTX = "KxProcess<'{}'>: This error occurred while checking if the worker '{}' is started."
WORKER_IS_CLOSED_CTX = "KxProcess<'{}'>: This error occurred while checking if the worker '{}' is closed."
WORKER_LOAD_ERROR_CTX = "KxProcess<'{}'>: This error occurred while loading the worker: {}"
WORKER_OPEN_ERROR_CTX = "KxProcess<'{}'>: This error occurred while opening the worker: {}"
WORKER_START_ERROR_CTX = "KxProcess<'{}'>: This error occurred while starting the worker: {}"
WORKER_STOP_ERROR_CTX = "KxProcess<'{}'>: This error occurred while stopping the worker: {}"
WORKER_CLOSE_ERROR_CTX = "KxProcess<'{}'>: This error occurred while closing the worker: {}"
WORKER_KILL_ERROR_CTX = "KxProcess<'{}'>: This error occurred while killing the worker: {}"
COMPONENT_CALL_ERROR_CTX = "KxProcess<'{}'>: This error occurred while calling the method '{}' of the component '{}' " \
                           "of the worker '{}'"


# --- EXCEPTIONS ---
class WorkerMethodCallError(GenericException):
    pass


class WorkerAlreadyAddedError(GenericException):
    pass


class UnknownWorkerError(GenericException):
    pass


class WorkerStateError(GenericException):
    pass


class UnknownComponentError(GenericException):
    pass


class UnknownComponentMethodError(GenericException):
    pass


# --- CLASSES ---


class KxProcessAPI(API):

    def __init__(self, kx_process):
        super().__init__()
        self.process = kx_process

    # --- Attr ---
    def get_kx_id(self):
        """
        Get the kxprocess id.
        """
        return self.process.kx_id

    # --- Core methods ---
    def close(self):
        """
        Close the process, its worker and their components.

        :raise WorkerMethodCallError: If the worker close method fails.
        """
        self.process.close()

    def kill(self):
        """
        Kill the process even if close methods of workers or components raised exceptions.
        """
        self.process.kill()

    # --- Worker base methods ---
    def load_worker(self, worker):
        """
        Add a worker, open and start it.

        :param worker: The worker to load.

        :raises WorkerAlreadyAddedError: If the worker is already added.
        :raises WorkerMethodCallError: If the worker open or start method fails.
        """
        with Context(WORKER_LOAD_ERROR_CTX.format(self.process.kx_id, worker.worker_identifier)):
            self.add_worker(worker)
            self.open_worker(worker.worker_identifier)
            self.start_worker(worker.worker_identifier)

    def is_worker(self, worker_identifier: str):
        """
        Check if the given id is a worker.

        :param worker_identifier: The id to check as a string.
        :return: True if the id is a worker, False otherwise.
        """
        return self.process.is_worker(worker_identifier)

    def add_worker(self, worker):
        """
        Add a worker to the process.

        :param worker: The worker to add.

        :raises WorkerAlreadyAddedError: If the worker is already added.
        """

        self.process.add_worker(worker)

    def remove_worker(self, worker_identifier: str):
        """
        Remove a worker from the process.

        :param worker_identifier: The worker identifier as a string.

        :raises UnknownWorkerError: If the worker does not exist.
        :raises WorkerStateError: If the worker is not closed.
        """

        self.process.remove_worker(worker_identifier)

    def get_worker(self, worker_identifier: str):
        """
        Get a worker from the process.

        :param worker_identifier: The worker identifier as a string.

        :raises UnknownWorkerError: If the worker does not exist.
        """

        return self.process.get_worker(worker_identifier)

    # --- Worker state methods ---
    def open_worker(self, worker_identifier: str):
        """
        Open a worker.

        :param worker_identifier: The worker identifier as a string.

        :raises UnknownWorkerError: If the worker does not exist.
        :raises WorkerStateError: If the worker is already opened.
        :raises WorkerMethodCallError: If the worker open method fails.
        """

        self.process.open_worker(worker_identifier)

    def start_worker(self, worker_identifier: str):
        """
        Start a worker.

        :param worker_identifier: The worker identifier as a string.

        :raises UnknownWorkerError: If the worker does not exist.
        :raises WorkerStateError: If the worker is already started, not opened or closed. You can access the initial exception
        type name through StateError.tracebacks[0]["type"].
        :raises WorkerMethodCallError: If the worker start method fails.
        """

        self.process.start_worker(worker_identifier)

    def stop_worker(self, worker_identifier: str):
        """
        Stop a worker.

        :param worker_identifier: The worker identifier as a string.

        :raises UnknownWorkerError: If the worker does not exist.
        :raises WorkerStateError: If the worker is already stopped, not opened or closed. You can access the initial exception
        type name through StateError.tracebacks[0]["type"].
        :raises WorkerMethodCallError: If the worker stop method fails.
        """

        self.process.stop_worker(worker_identifier)

    def close_worker(self, worker_identifier: str):
        """
        Close and remove a worker.

        :param worker_identifier: The worker identifier as a string.

        :raises UnknownWorkerError: If the worker does not exist.
        :raises WorkerStateError: If the component is already closed, not opened or running. You can access the initial exception
        type name through StateError.tracebacks[0]["type"].
        :raises WorkerMethodCallError: If the worker close method fails.
        """

        self.process.close_worker(worker_identifier)

    def kill_worker(self, worker_identifier: str):
        """
        Stop, close and remove a worker.

        :param worker_identifier: The worker identifier as a string.

        :raises UnknownWorkerError: If the worker does not exist.
        :raises WorkerMethodCallError: If the worker methods fails.
        """
        with Context(WORKER_KILL_ERROR_CTX.format(self.process.kx_id, worker_identifier)):
            if self.is_worker_opened(worker_identifier):
                if self.is_worker_running(worker_identifier):
                    self.stop_worker(worker_identifier)
                self.close_worker(worker_identifier)
            self.remove_worker(worker_identifier)

    # --- ABSTRACTIONS ---
    # -- Call --
    def call_worker_component(self, worker_identifier: str, component_identifier: str, method_name: str, *args,
                              **kwargs):
        """
        Call a method of a component of a worker. Allows interaction between kuix components and workers.
        :param worker_identifier: The worker identifier as a string.
        :param component_identifier: The component identifier as a string, as specified in the worker's definition
        when calling Worker.add_component method.
        :param method_name: The method name as a string.
        :param args: Additional method arguments.
        :param kwargs: Additional method keyword arguments.
        :return: The method return value.

        :raises UnknownWorkerError: If the worker does not exist.
        :raises UnknownComponentError: If the component does not exist.
        :raises UnknownComponentMethodError: If the method does not exist.
        :raises Exception: If the method call raises an exception.
        """
        with Context(
                COMPONENT_CALL_ERROR_CTX.format(self.process_id, method_name, component_identifier, worker_identifier)):
            worker = self.get_worker(worker_identifier)
            if component_identifier not in worker.components:
                raise UnknownComponentError(UNKNOWN_WORKER_COMPONENT_ERROR.format(self.process.prefix,
                                                                                  component_identifier,
                                                                                  worker_identifier))
            component = worker.components[component_identifier]
            if method_name not in dir(component):
                raise UnknownComponentMethodError(UNKNOWN_WORKER_COMPONENT_METHOD_ERROR.format(self.process.prefix,
                                                                                               method_name,
                                                                                               component_identifier,
                                                                                               worker_identifier))
        method = getattr(component, method_name)
        return method(*args, **kwargs)

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
        self.process.core_api.call_kuix_component(component_identifier, method_name, *args, **kwargs)

    # -- Workers --
    def is_worker_opened(self, worker_identifier: str):
        """
        Check if a worker is opened.

        :param worker_identifier: The worker identifier as a string.

        :return: True if the worker is opened, False otherwise.

        :raises UnknownWorkerError: If the worker does not exist.
        """
        with Context(WORKER_IS_OPEN_CTX.format(self.process_id, worker_identifier)):
            return self.get_worker(worker_identifier).is_opened()

    def is_worker_running(self, worker_identifier: str):
        """
        Check if a worker is running.

        :param worker_identifier: The worker identifier as a string.

        :return: True if the worker is running, False otherwise.

        :raises UnknownWorkerError: If the worker does not exist.
        """
        with Context(WORKER_IS_RUNNING_CTX.format(self.process_id, worker_identifier)):
            return self.get_worker(worker_identifier).is_running()

    def is_worker_closed(self, worker_identifier: str):
        """
        Check if a worker is closed.

        :param worker_identifier: The worker identifier as a string.

        :return: True if the worker is closed, False otherwise.

        :raises UnknownWorkerError: If the worker does not exist.
        """
        with Context(WORKER_IS_CLOSED_CTX.format(self.process_id, worker_identifier)):
            return self.get_worker(worker_identifier).is_closed()

    # -- Events --
    def trigger_event(self, event_name: str, *args, **kwargs):
        """
        Trigger an event.

        :param event_name: The event name as a string.
        :param args: The event arguments.
        :param kwargs: The event keyword arguments.
        """
        self.process.connector.trigger(event_name, *args, **kwargs)


class KxProcess:

    def __init__(self, kx_id: str, root_path: str, shared_hub, *args, **kwargs):
        """
        Instance a KxProcess to host workers

        :param kx_id: The id of the process as a string.
        :param root_path: The root path of KuiX as a string.
        :param shared_hub: The shared hub for IPC.
        """

        self.kx_id = kx_id
        self.root_path = root_path
        self.shared_hub = shared_hub

        # Initialize IPC
        self.api = KxProcessAPI(self)
        self.connector = Connector(self.kx_id, self.api, self.shared_hub)
        from kuix.core.kuix_core import KuixAPI
        self.connector.add_api("main", KuixAPI)
        self.core_api = self.connector.get_api("main")

        # Placeholders
        self.workers = {}  # type dict[identifier: str, worker: BaseWorker]

    # --- Core methods ---
    def close(self):
        """
        Close the process, its worker and their components.

        :raise WorkerMethodCallError: If the worker close method fails.
        """
        # Close all workers
        for worker in self.workers.copy().values():
            try:
                if worker.is_running():
                    worker.stop()
                if worker.is_opened():
                    worker.close()
                else:
                    self.remove_worker(worker.worker_identifier)
            except Exception as e:
                raise WorkerMethodCallError(WORKER_CLOSE_GENERIC_ERROR.format(self.kx_id, worker.worker_identifier)) + e

        # Close the connector and kill the process
        def final():
            self.api.trigger_event(Events.PROCESS_CLOSED, self.kx_id)
            self.connector.close()
            self.shared_hub.clear_process(self.kx_id)
            os.kill(os.getpid(), 0)

        threading.Thread(target=final).start()

    def kill(self):
        """
        Kill the process even if close methods of workers or components raised exceptions.
        """
        try:
            self.close()
        except:
            def final():
                self.api.trigger_event(Events.PROCESS_CLOSED, self.kx_id)
                self.connector.close()
                self.shared_hub.clear_process(self.kx_id)
                os.kill(os.getpid(), 0)

            threading.Thread(target=final).start()

    # --- Worker base methods ---
    def is_worker(self, worker_identifier: str):
        """
        Check if the given id is a worker.

        :param worker_identifier: The id to check as a string.
        :return: True if the id is a worker, False otherwise.
        """

        return worker_identifier in self.workers

    def add_worker(self, worker):
        """
        Add a worker to the process.

        :param worker: The worker to add.

        :raises WorkerAlreadyAddedError: If the worker is already added.
        """
        if self.is_worker(worker.worker_identifier):
            raise WorkerAlreadyAddedError(WORKER_ALREADY_ADDED_ERROR.format(self.kx_id, worker.worker_identifier))

        worker.process_api = self.api
        self.workers[worker.worker_identifier] = worker

        # Trigger the event
        self.connector.trigger(Events.WORKER_ADDED, self.kx_id, worker.worker_identifier)

    def remove_worker(self, worker_identifier: str):
        """
        Remove a worker from the process.

        :param worker_identifier: The worker identifier as a string.

        :raises UnknownWorkerError: If the worker does not exist.
        :raises WorkerStateError: If the worker is opened and not closed.
        """

        if not self.is_worker(worker_identifier):
            raise UnknownWorkerError(WORKER_DOES_NOT_EXIST_ERROR.format(self.kx_id, worker_identifier))

        if self.workers[worker_identifier].is_opened() and not self.workers[worker_identifier].is_closed():
            raise WorkerStateError(WORKER_NOT_CLOSED_ERROR.format(self.kx_id, worker_identifier))

        del self.workers[worker_identifier]
        self.connector.trigger(Events.WORKER_REMOVED, self.kx_id, worker_identifier)

    def get_worker(self, worker_identifier: str):
        """
        Get a worker from the process.

        :param worker_identifier: The worker identifier as a string.

        :raises UnknownWorkerError: If the worker does not exist.
        """

        if not self.is_worker(worker_identifier):
            raise UnknownWorkerError(WORKER_DOES_NOT_EXIST_ERROR.format(self.kx_id, worker_identifier))

        return self.workers[worker_identifier]

    # --- Worker state methods ---
    def open_worker(self, worker_identifier: str):
        """
        Open a worker.

        :param worker_identifier: The worker identifier as a string.

        :raises UnknownWorkerError: If the worker does not exist.
        :raises WorkerStateError: If the worker is already opened.
        :raises WorkerMethodCallError: If the worker open method fails.
        """
        with Context(WORKER_OPEN_ERROR_CTX.format(self.kx_id, worker_identifier)):
            worker = self.get_worker(worker_identifier)
            worker.open()

    def start_worker(self, worker_identifier: str):
        """
        Start a worker.

        :param worker_identifier: The worker identifier as a string.

        :raises UnknownWorkerError: If the worker does not exist.
        :raises WorkerStateError: If the worker is already started, not opened or closed. You can access the initial exception
        type name through StateError.tracebacks[0]["type"].
        :raises WorkerMethodCallError: If the worker start method fails.
        """
        with Context(WORKER_START_ERROR_CTX.format(self.kx_id, worker_identifier)):
            worker = self.get_worker(worker_identifier)
            worker.start()

    def stop_worker(self, worker_identifier: str):
        """
        Stop a worker.

        :param worker_identifier: The worker identifier as a string.

        :raises UnknownWorkerError: If the worker does not exist.
        :raises WorkerStateError: If the worker is already stopped, not opened or closed. You can access the initial exception
        type name through StateError.tracebacks[0]["type"].
        :raises WorkerMethodCallError: If the worker stop method fails.
        """
        with Context(WORKER_STOP_ERROR_CTX.format(self.kx_id, worker_identifier)):
            worker = self.get_worker(worker_identifier)
            worker.stop()

    def close_worker(self, worker_identifier: str):
        """
        Close and remove a worker.

        :param worker_identifier: The worker identifier as a string.

        :raises UnknownWorkerError: If the worker does not exist.
        :raises WorkerStateError: If the component is already closed, not opened or running. You can access the initial exception
        type name through StateError.tracebacks[0]["type"].
        :raises WorkerMethodCallError: If the worker close method fails.
        """
        with Context(WORKER_CLOSE_ERROR_CTX.format(self.kx_id, worker_identifier)):
            worker = self.get_worker(worker_identifier)
            worker.close()
            self.remove_worker(worker_identifier)


def new_kx_process(kx_id: str, root_path: str, shared_hub, *args, **kwargs):
    """
    Create a new KxProcess instance.

    :param kx_id: The id of the process as a string.
    :param root_path: The root path of KuiX as a string.
    :param shared_hub: The shared hub for IPC.
    :return: The KxProcess instance.
    """

    KxProcess(kx_id, root_path, shared_hub, *args, **kwargs).connector.trigger(Events.PROCESS_CREATED, kx_id)
