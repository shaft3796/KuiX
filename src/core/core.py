"""
Core module of KuiX.
"""
import inspect
import json
import multiprocessing
import os
import time

from src.core.ipc.IpcServer import IpcServer
from src.core.process.KxProcess import __launch__ as launch
from src.core.event import CoreEvent, EventHandler
from src.core.Logger import LOGGER, CORE
from src.core.messages.CoreMessages import *
from src.core.Exceptions import *
from src.core_components.BaseCoreComponent import BaseCoreComponent
from src.core.BuiltInLoader import get_builtin_types


class KuiX:

    @staticmethod
    def __setup_files__(path: str):
        """
        Setup filesystem for KuiX.
        :param path: Root path of KuiX.
        :return: the root path of KuiX folders.

        :raises CoreSetupError: if an error occurred while setting up KuiX files, you can access the initial
        exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised exception.
        """
        try:
            if not path.endswith('/') and path != "":
                path += '/'
            os.makedirs(path + 'kuiX', exist_ok=True)
            os.makedirs(path + 'kuiX/Logs', exist_ok=True)
            os.makedirs(path + 'kuiX/Strategies', exist_ok=True)
            os.makedirs(path + 'kuiX/Components', exist_ok=True)
        except Exception as e:
            raise CoreSetupError(SETUP_FILES_ERROR) + e
        LOGGER.trace(SETUP_FILES_TRACE, CORE)
        return path + 'kuiX/'

    @staticmethod
    def configured(func):

        def wrapper(self, *args, **kwargs):
            if self.configured:
                return func(self, *args, **kwargs)
            else:
                raise CoreNotConfigured(CORE_NOT_CONFIGURED_ERROR.format(func.__name__))

        return wrapper

    @staticmethod
    def not_configured(func):

            def wrapper(self, *args, **kwargs):
                if not self.configured:
                    return func(self, *args, **kwargs)
                else:
                    raise CoreAlreadyConfigured(CORE_ALREADY_CONFIGURED_ERROR.format(func.__name__))

            return wrapper

    @staticmethod
    def started(func):

        def wrapper(self, *args, **kwargs):
            if self.started:
                return func(self, *args, **kwargs)
            else:
                raise CoreNotStarted(CORE_NOT_STARTED_ERROR.format(func.__name__))

        return wrapper

    @staticmethod
    def not_started(func):

        def wrapper(self, *args, **kwargs):
            if not self.started:
                return func(self, *args, **kwargs)
            else:
                raise CoreAlreadyStarted(CORE_ALREADY_STARTED_ERROR.format(func.__name__))

        return wrapper

    def __init__(self, path: str = ""):
        """
        Instance a KuiX Core, this method will set up the filesystem for KuiX and create placeholders.
        :param path: root path of KuiX, if not specified, the current working directory will be used.

        :raises CoreSetupError: if an error occurred while setting up KuiX files, you can access the initial
        exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised exception.
        """
        try:
            self.root_path = self.__setup_files__(path)
        except CoreSetupError as e:
            raise e.add_ctx(CORE_INIT_ERROR)

        # --- PLACEHOLDERS ---
        # Core
        self.configured = False
        self.started = False

        # Ipc
        self.ipc_server = None

        # Configuration
        self.ipc_host = None
        self.ipc_port = None
        self.auth_key = None
        self.artificial_latency = None

        # Components
        self.components = {}  # type dict[name: str, component: CoreComponent]

        # Process
        self.process_count = None
        self.kx_processes = []  # type list[identifiers: str]

        # Workers
        self.workers = {}  # type dict[identifier: str, process_identifier: str]

        # Strategies
        self.strategies = {}  # type dict[name: str, [import_path: str, config: dict]]

        # Events
        self.event_handler = EventHandler()

        LOGGER.trace(CORE_INIT_TRACE, CORE)

    # --- CONFIGURATION ---
    @not_configured
    def configure(self, ipc_host: str = "localhost", ipc_port: int = 6969, auth_key: str = "",
                  socket_artificial_latency: int = 0.1, process_count: int = -1):
        """
        Configure KuiX core directly from a python function call.
        :param ipc_host: Host used for the local inter process communication socket server.
        :param ipc_port: Port used for the local inter process communication socket server.
        :param auth_key: Authentication key used for the local inter process communication socket server to
        authenticate clients, "" by default,
        this will automatically create an auth key.
        :param socket_artificial_latency: Artificial latency added to the local inter process communication socket
        server for optimization purposes.
        :param process_count: Number of processes to use. Set this number above available cpu count will lead to
        performance degradation. Set this number to -1 to automatically use all available cpu count.

        :raises SocketServerBindError: if an error occurred while binding the local inter process communication
        socket server.
        """
        self.ipc_host = ipc_host
        self.ipc_port = ipc_port
        self.auth_key = auth_key
        self.process_count = process_count
        self.configured = True

        # Instance IPC server
        try:
            self.ipc_server = IpcServer(self.auth_key, self.ipc_host, self.ipc_port, socket_artificial_latency,
                                        self.event_handler)
        except SocketServerBindError as e:
            raise e.add_ctx(CORE_CONFIGURE_ERROR)
        # Placeholder, add endpoints and events
        # add Built In types
        try:
            builtin = get_builtin_types()
            for name, t in builtin:
                self.add_strategy(name, t)
        except Exception as e:
            raise CoreSetupError(CORE_CONFIGURE_ERROR_BUILTIN) + e
        LOGGER.info(CORE_CONFIGURE_TRACE, CORE)

    @not_configured
    def load_json_config(self, path: str = "config.json"):
        """
        Load KuiX configuration from a json file.
        :param path: Path to the json file.

        :raises SocketServerBindError: if an error occurred while binding the local inter process communication
        socket server.
        :raises CoreConfigLoadError: if an error occurred while loading KuiX configuration from json, you can access
        the initial exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised
        exception.
        """
        try:
            with open(path) as f:
                config = json.load(f)
            self.configure(**config)
        except SocketServerBindError as e:
            raise e.add_ctx(CORE_JSON_CONFIG_ERROR)
        except Exception as e:
            raise CoreConfigLoadError(CORE_JSON_CONFIG_ERROR) + e

    @staticmethod
    def generate_json_config(path: str = "config.json"):
        """
        Generate a json configuration with default values.
        :param path: path to the json file.

        :raises CoreConfigGenerationError: if an error occurred while generating KuiX configuration, you can access
        the initial exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised
        exception.
        """
        try:
            with open(path, "w") as f:
                json.dump({
                    "ipc_host": "localhost",
                    "ipc_port": 6969,
                    "auth_key": "",
                    "process_count": -1
                }, f, indent=1)
        except Exception as e:
            raise CoreConfigGenerationError(CORE_GENERATE_CONFIG_ERROR) + e

    @configured
    @not_started
    def start(self):
        """
        Start KuiX. (non blocking)
        """
        self.event_handler.subscribe(CoreEvent.SOCKET_CONNECTION_ACCEPTED,
                                     lambda identifier: self.kx_processes.append(identifier))
        # Accepts connection from processes
        self.ipc_server.accept_new_connections()

        # Update status
        self.started = True
        LOGGER.info(CORE_START_TRACE, CORE)

    @configured
    @started
    def close(self):
        """
        Close KuiX.
        """
        # Start by killing all workers
        workers = self.workers.copy()
        for identifier in workers:
            try:
                self.close_worker(identifier)
            except Exception as e:
                _e = CoreClosingError(CORE_CLOSE_ERROR) + e
                LOGGER.warning_exception(_e, CORE)
        # Then kill all processes
        identifiers = self.kx_processes.copy()
        for identifier in identifiers:
            try:
                self.close_process(identifier)
            except Exception as e:
                _e = CoreClosingError(CORE_CLOSE_ERROR) + e
                LOGGER.warning_exception(_e, CORE)
        # Then kill all components
        names = self.components.copy()
        for name in names:
            try:
                self.close_component(name)
            except Exception as e:
                _e = CoreClosingError(CORE_CLOSE_ERROR) + e
                LOGGER.warning_exception(_e, CORE)
        # Then kill the ipc server
        try:
            self.ipc_server.close()
        except Exception as e:
            _e = CoreClosingError(CORE_CLOSE_ERROR) + e
            LOGGER.warning_exception(_e, CORE)
        # Update status
        self.started = False

        LOGGER.info(CORE_CLOSE_INFO, CORE)

    @staticmethod
    def generate_auth_key():
        """
        Generate a random 256b auth key.
        """
        return os.urandom(256).hex()

    # --- COMPONENTS ---
    @configured
    def add_component(self, name, instance: BaseCoreComponent):
        """
        Add a component to KuiX.
        :param name: Name of the component.
        :param instance: Instance of the component.
        """
        if name in self.components:
            LOGGER.warning(CORE_ADD_COMPONENT_WARNING.format(name), CORE)
        self.components[name] = instance

    @configured
    def get_component(self, name):
        """
        Get a component from KuiX.
        :param name: Name of the component.
        :return: Instance of the component.
        """
        return self.components[name]

    @configured
    def remove_component(self, name):
        """
        Remove a component from KuiX.
        :param name: Name of the component.
        """
        self.components[name].__close__()
        del self.components[name]
        # TODO: add error handling

    @configured
    def open_component(self, name):
        """
        Open a component from KuiX.
        :param name: Name of the component.
        """
        self.components[name].__open__()
        # TODO: add error handling

    @configured
    def start_component(self, name):
        """
        Start a component from KuiX.
        :param name: Name of the component.
        """
        self.components[name].__start__()
        # TODO: add error handling

    @configured
    def stop_component(self, name):
        """
        Stop a component from KuiX.
        :param name: Name of the component.
        """
        self.components[name].__stop__()
        # TODO: add error handling

    @configured
    def close_component(self, name):
        """
        Close a component from KuiX.
        :param name: Name of the component.
        """
        self.components[name].__close__()
        # TODO: add error handling

    # --- ENDPOINTS ---
    @configured
    def add_endpoint(self, name: str, callback: callable):
        """
        add an endpoint, a method accessible from sub processes through IPC.
        :param name: Name of the endpoint.
        :param callback: Callback function to call when the endpoint is called.
        """
        if name in self.ipc_server.endpoints:
            LOGGER.warning(CORE_ADD_ENDPOINT_WARNING, CORE)
        self.ipc_server.endpoints[name] = callback

    @configured
    def add_blocking_endpoint(self, name: str, callback: callable):
        """
        add a blocking endpoint, a method accessible from sub processes through the IPC.
        This endpoint is blocking, the core will wait for the endpoint to send a response the
        'self.send_response' method.
        WARNING: This is a blocking method, it will block the sub processes until the endpoint returns a value, if your
        method does not send a response using the 'self.send_response' method, some methods will block forever !
        :param name: Name of the endpoint.
        :param callback: Callback function to call when the endpoint is called. This function must absolutely
        call only one time the 'self.send_response' method.
        """
        if name in self.ipc_server.endpoints:
            LOGGER.warning(CORE_ADD_BLOCKING_ENDPOINT_WARNING.format(name), CORE)
        self.ipc_server.blocking_endpoints[name] = callback

    # --- IPC ---
    def send(self, process_identifier, endpoint: str, data: dict):
        """
        Send data as a dict to a process through the IPC.
        :param process_identifier: Identifier of the process to send the data to.
        :param endpoint: Name of the endpoint to call on the process as added with the 'add_endpoint'
        method of the client.
        :param data: Data to send as a dict

        :raises SocketServerSendError: if an error occurred while sending the data to the process, you can access
        the initial exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised
        exception.
        """
        try:
            self.ipc_server.send_fire_and_forget_request(endpoint, data)
        except SocketServerSendError as e:
            raise e.add_ctx(CORE_SEND_ERROR.format(endpoint, process_identifier))

    def send_blocking(self, process_identifier, endpoint: str, data: dict):
        """
        Send data as a dict to a process through the IPC and wait for the response.
        :param process_identifier: Identifier of the process to send the data to.
        :param endpoint: Name of the endpoint to call on the process as added with the 'add_endpoint'
        method of the client.
        :param data: Data to send as a dict

        :raises SocketServerSendError: if an error occurred while sending the data to the process, you can access
        the initial exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised
        exception.
        """
        try:
            return self.ipc_server.send_blocking_request(endpoint, data)
        except SocketServerSendError as e:
            raise e.add_ctx(CORE_SEND_BLOCKING_ERROR.format(endpoint, process_identifier))

    def send_response(self, process_identifier, endpoint: str, data: dict, rid: str):
        """
        Send the response of a blocking request.
        :param process_identifier: Identifier of the process to send the data to.
        :param endpoint: Name of the endpoint to call on the process as added with the 'add_endpoint'
        :param data: Data to send as a dict
        :param rid: Request id of the request to respond to.

        :raises SocketServerSendError: if an error occurred while sending the data to the process, you can access
        the initial exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised
        exception.
        """
        try:
            self.ipc_server.send_response(endpoint, data, rid)
        except SocketServerSendError as e:
            raise e.add_ctx(CORE_SEND_RESPONSE_ERROR.format(endpoint, process_identifier))

    # --- PROCESS ---
    @configured
    @started
    def create_process(self, identifier: str, additional_kwargs: dict = None):
        """
        Launch a new KxProcess running in a separate process. (non-blocking)
        :param identifier: Identifier of the new process.
        :param additional_kwargs: Additional kwargs to pass to the KxProcess constructor, if you decided to override it.

        :raises ProcessAlreadyExists: if a process with the same identifier already exists.
        """
        if identifier in self.kx_processes:
            raise ProcessAlreadyExists(CORE_CREATE_PROCESS_ERROR.format(identifier))

        multiprocessing.Process(target=launch, args=(identifier, self.root_path, self.auth_key, self.ipc_host,
                                                     self.ipc_port, additional_kwargs)).start()

    @configured
    @started
    def create_process_and_wait(self, identifier: str, additional_kwargs: dict = None):
        """
        Launch a new KxProcess running in a separate process. (blocking)
        Wait for the process to be created before returning and push all existing strategies to the new process.
        :param identifier: Identifier of the new process.
        :param additional_kwargs: Additional kwargs to pass to the KxProcess constructor, if you decided to override it.

        :raises ProcessAlreadyExists: if a process with the same identifier already exists.
        :raises ProcessLaunchError: if the process timed out.
        :raises SocketServerSendError: if an error occurred while sending the data to the process, you can access
        the initial exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised
        exception.
        :raises SocketServerClientNotFound: if the process is not connected to the IPC server.
        :raises KxProcessStrategyImportError: if the process failed to import a strategy.
        :raises StrategyNotadded: if the process failed to add a strategy.
        :raises ProcessNotFound: if the process is not found in the process list (should not happen).
        """
        self.create_process(identifier, additional_kwargs)
        acc = 0
        while identifier not in self.kx_processes and acc < 30:
            time.sleep(0.1)
            acc += 0.1
        if identifier not in self.kx_processes:
            raise ProcessLaunchError(CORE_CREATE_PROCESS_AND_WAIT_ERROR_TIMEOUT.format(identifier))
        try:
            self.push_all_strategies(identifier)
        except (SocketServerSendError, SocketServerClientNotFound, KxProcessStrategyImportError,
                StrategyNotAdded, ProcessNotFound) as e:
            raise e.add_ctx(CORE_CREATE_PROCESS_AND_WAIT_ERROR_PUSH.format(identifier))

    @configured
    @started
    def close_process(self, kx_process_identifier: str):
        """
        Close a KxProcess.
        :param kx_process_identifier: Identifier of the process to close.

        :raises ProcessNotFound: if the KxProcess was not found.
        :raises SocketServerSendError: if an error occurred while sending the data to the process, you can access
        the initial exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised
        exception.
        :raises SocketServerClientNotFound: if the client was not found.
        :raises GenericException: if an error occurred while closing the process.
        """
        if kx_process_identifier not in self.kx_processes:
            raise ProcessNotFound(CORE_CLOSE_PROCESS_ERROR_NOT_FOUND.format(kx_process_identifier))
        try:
            response = self.ipc_server.send_blocking_request(kx_process_identifier, "close_process", {})
            if response["status"] == "error":
                ex = deserialize(response["return"])
                raise ex
        except (SocketServerSendError, SocketServerClientNotFound, GenericException) as e:
            raise e.add_ctx(CORE_CLOSE_PROCESS_ERROR.format(kx_process_identifier))

    # --- STRATEGIES ---
    @configured
    def add_strategy(self, name: str, import_path: str):
        """
        add a strategy to be used by all KxProcesses.
        :param name: Name of the strategy, this have to be the name of the class to import.
        :param import_path: Absolute path of the module file where the strategy is located.
        """
        if name in self.strategies:
            LOGGER.warning(CORE_ADD_STRATEGY_WARNING.format(name), CORE)
        self.strategies[name] = import_path
        # Push the strategy to all processes
        self.push_strategy_to_all(name)

    @configured
    def add_strategy_from_type(self, strategy):
        """
        add a strategy to be used by all KxProcesses.
        :param strategy: Strategy class to add.

        :raises StrategyAlreadyadded: if a strategy with the same name already exists.
        """
        self.add_strategy(strategy.__name__, inspect.getfile(strategy))

    @configured
    def push_strategy(self, name, process_identifier):
        """
        Push a previously added strategy to a KxProcess.
        :param name: Name of the strategy to push.
        :param process_identifier: Identifier of the KxProcess to push the strategy to.

        :raises SocketServerSendError: if an error occurred while sending the data to the process, you can access
        the initial exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised
        exception.
        :raises SocketServerClientNotFound: if the client was not found.
        :raises KxProcessStrategyImportError: if an error occurred while importing the strategy on the KxProcess.
        :raises StrategyNotadded: if the strategy was not added.
        :raises ProcessNotFound: if the KxProcess was not found.
        """
        # Check if the strategy is added
        if name not in self.strategies:
            raise StrategyNotAdded(PUSH_STRATEGY_ERROR_NOT_ADDED.format(name))
        if process_identifier not in self.kx_processes:
            raise ProcessNotFound(PUSH_STRATEGY_ERROR_PROCESS_NOT_FOUND.format(process_identifier))

        try:
            response = self.ipc_server.send_blocking_request(process_identifier, "add_strategy",
                                                             {"name": name, "import_path": self.strategies[name]})
            if response["status"] == "error":
                # deserialize exception
                ex = deserialize(response["return"])
                raise ex
        except (SocketServerSendError, SocketServerClientNotFound,
                KxProcessStrategyImportError) as e:
            raise e.add_ctx(PUSH_STRATEGY_ERROR.format(name, process_identifier))

    @configured
    def push_strategy_to_all(self, name):
        """
        Push a previously added strategy to all KxProcesses.
        :param name: name of the strategy to push.
        """
        for process in self.kx_processes:
            try:
                self.push_strategy(name, process)
            except (StrategyNotAdded, ProcessNotFound, SocketServerSendError, SocketServerClientNotFound,
                    KxProcessStrategyImportError) as e:
                LOGGER.error_exception(e.add_ctx(PUSH_STRATEGY_TO_ALL_ERROR), CORE)

    @configured
    def push_all_strategies(self, process_identifier):
        """
        Push all previously added strategies to a KxProcess.
        :param process_identifier: Identifier of the KxProcess to push the strategies to.

        :raises SocketServerSendError: if an error occurred while sending the data to the process, you can access
        the initial exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised
        exception.
        :raises SocketServerClientNotFound: if the client was not found.
        :raises KxProcessStrategyImportError: if an error occurred while importing the strategy on the KxProcess.
        :raises StrategyNotadded: if the strategy was not added.
        :raises ProcessNotFound: if the KxProcess was not found.
        """
        for strategy in self.strategies:
            try:
                self.push_strategy(strategy, process_identifier)
            except (SocketServerSendError, SocketServerClientNotFound,
                    KxProcessStrategyImportError) as e:
                raise e.add_ctx(PUSH_ALL_STRATEGIES_ERROR.format(process_identifier))

    @configured
    def push_all_strategies_to_all(self):
        """
        Push all previously added strategies to all KxProcesses.
        """
        for process in self.kx_processes:
            try:
                self.push_all_strategies(process)
            except (StrategyNotAdded, ProcessNotFound, SocketServerSendError, SocketServerClientNotFound,
                    KxProcessStrategyImportError) as e:
                LOGGER.error_exception(e.add_ctx(PUSH_ALL_STRATEGIES_TO_ALL_ERROR), CORE)

    @configured
    @started
    def create_worker(self, kx_process_identifier, strategy_name: str, worker_identifier: str, config=None):
        """
        Instance a new worker from a strategy class. When instancing a worker, you have to choose a KxProcess to
        use. The worker will be created in the KxProcess and will not be accessible directly from the KuiX core or
        another process.
        :param kx_process_identifier: Identifier of the KX process to use.
        :param strategy_name: Name of the strategy to use.
        :param worker_identifier: Identifier of the worker.
        :param config: Arguments to pass to the strategy '__init__' method.

        :raises ProcessNotFound: if the KxProcess was not found.
        :raises StrategyNotadded: if the strategy was not added.
        :raises SocketServerSendError: if an error occurred while sending the request to the KxProcess.
        :raises SocketServerClientNotFound: if the KxProcess was not found.
        :raises StrategyNotFoundError: if the strategy was not found in the KxProcess.
        :raises WorkerAlreadyExistsError: if a worker with the same identifier already exists in the KxProcess.
        :raises GenericException: if an error occurred while creating the worker in the KxProcess.
        To get more details as a developer, look at the 'initial_type' and 'initial_msg' attributes of the
        raised exception.
        """
        if kx_process_identifier not in self.kx_processes:
            raise ProcessNotFound(CORE_CREATE_WORKER_ERROR_PROCESS_NOT_FOUND.format(kx_process_identifier))
        if config is None:
            config = {}
        if strategy_name not in self.strategies:
            raise StrategyNotAdded(CORE_CREATE_WORKER_ERROR_STRATEGY_NOT_ADDED.format(strategy_name))
        if worker_identifier in self.workers:
            raise WorkerAlreadyExistsError(CORE_CREATE_WORKER_ERROR_WORKER_ALREADY_CREATED.format(worker_identifier))
        try:
            response = self.ipc_server.send_blocking_request(kx_process_identifier, "create_worker",
                                                             {"strategy_name": strategy_name,
                                                              "identifier": worker_identifier,
                                                              "config": config})
            if response["status"] == "error":
                ex = deserialize(response["return"])
                raise ex
            # Add the worker to the list of workers
            self.workers[worker_identifier] = kx_process_identifier
        except (SocketServerSendError, SocketServerClientNotFound, StrategyNotFoundError,
                WorkerAlreadyExistsError, GenericException) as e:
            raise e.add_ctx(CORE_CREATE_WORKER_ERROR.format(worker_identifier, strategy_name, kx_process_identifier))

    @configured
    @started
    def start_worker(self, worker_identifier: str):
        """
        Call the '__start__' method of a worker.
        :param worker_identifier: Identifier of the worker.

        :raises ProcessNotFound: if the KxProcess was not found.
        :raises SocketServerSendError: if an error occurred while sending the request to the KxProcess.
        :raises SocketServerClientNotFound: if the KxProcess was not found.
        :raises WorkerNotFoundError: if the worker doesn't exist.
        :raises WorkerMethodCallError: if an error occurred while calling the '__start__' method of the worker.
        :raises GenericException: if an error occurred while starting the worker in the KxProcess.
        To get more details as a developer, look at the 'initial_type' and 'initial_msg' attributes of the
        raised exception.
        """
        if worker_identifier not in self.workers:
            raise WorkerNotFoundError(CORE_START_WORKER_ERROR_WORKER_NOT_FOUND.format(worker_identifier))
        kx_process_identifier = self.workers[worker_identifier]
        try:
            response = self.ipc_server.send_blocking_request(kx_process_identifier, "start_worker",
                                                             {"identifier": worker_identifier})
            if response["status"] == "error":
                ex = deserialize(response["return"])
                raise ex
        except (SocketServerSendError, SocketServerClientNotFound, WorkerNotFoundError, GenericException,
                WorkerMethodCallError) as e:
            raise e.add_ctx(CORE_START_WORKER_ERROR.format(worker_identifier, kx_process_identifier))

    @configured
    @started
    def stop_worker(self, worker_identifier: str):
        """
        Call the '__stop__' method of a worker.
        :param worker_identifier: Identifier of the worker.

        :raises ProcessNotFound: if the KxProcess was not found.
        :raises SocketServerSendError: if an error occurred while sending the request to the KxProcess.
        :raises SocketServerClientNotFound: if the KxProcess doesn't exist.
        :raises WorkerNotFoundError: if the worker was not found in the KxProcess.
        :raises WorkerMethodCallError: if an error occurred while calling the '__stop__' method of the worker.
        :raises GenericException: if an error occurred while starting the worker in the KxProcess.
        To get more details as a developer, look at the 'initial_type' and 'initial_msg' attributes of the
        raised exception.
        """
        if worker_identifier not in self.workers:
            raise WorkerNotFoundError(CORE_STOP_WORKER_ERROR_WORKER_NOT_FOUND.format(worker_identifier))
        kx_process_identifier = self.workers[worker_identifier]
        try:
            response = self.ipc_server.send_blocking_request(kx_process_identifier, "stop_worker",
                                                             {"identifier": worker_identifier})
            if response["status"] == "error":
                ex = deserialize(response["return"])
                raise ex
        except (SocketServerSendError, SocketServerClientNotFound, WorkerNotFoundError, GenericException,
                WorkerMethodCallError) as e:
            raise e.add_ctx(CORE_STOP_WORKER_ERROR.format(worker_identifier, kx_process_identifier))

    @configured
    @started
    def close_worker(self, worker_identifier: str):
        """
        Call the '__close__' method of a worker.
        :param worker_identifier: Identifier of the worker.

        :raises ProcessNotFound: if the KxProcess was not found.
        :raises SocketServerSendError: if an error occurred while sending the request to the KxProcess.
        :raises SocketServerClientNotFound: if the KxProcess doesn't exist.
        :raises WorkerNotFoundError: if the worker was not found in the KxProcess.
        :raises WorkerMethodCallError: if an error occurred while calling the '__close__' method of the worker.
        :raises GenericException: if an error occurred while starting the worker in the KxProcess.
        To get more details as a developer, look at the 'initial_type' and 'initial_msg' attributes of the
        raised exception.
        """
        if worker_identifier not in self.workers:
            raise WorkerNotFoundError(CORE_CLOSE_WORKER_ERROR_WORKER_NOT_FOUND.format(worker_identifier))
        kx_process_identifier = self.workers[worker_identifier]
        try:
            response = self.ipc_server.send_blocking_request(kx_process_identifier, "close_worker",
                                                             {"identifier": worker_identifier})
            if response["status"] == "error":
                ex = deserialize(response["return"])
                raise ex
            # Remove the worker from the list of workers
            del self.workers[worker_identifier]
        except (SocketServerSendError, SocketServerClientNotFound, WorkerNotFoundError, GenericException,
                WorkerMethodCallError) as e:
            raise e.add_ctx(CORE_CLOSE_WORKER_ERROR.format(worker_identifier, kx_process_identifier))

    @configured
    @started
    def get_worker_status(self, worker_identifier: str):
        """
        Get the status of a worker.
        :param worker_identifier: Identifier of the worker.

        :return: The status of the worker. (WorkerStatus.STARTED, WorkerStatus.STOPPED, WorkerStatus.CLOSED)

        :raises ProcessNotFound: if the KxProcess doesn't exist.
        :raises SocketServerSendError: if an error occurred while sending the request to the KxProcess.
        :raises SocketServerClientNotFound: if the KxProcess was not found.

        :raises GenericException: if an error occurred while starting the worker in the KxProcess.
        To get more details as a developer, look at the 'initial_type' and 'initial_msg' attributes of the
        raised exception.
        """
        if worker_identifier not in self.workers:
            raise WorkerNotFoundError(CORE_WORKER_GET_STATUS_ERROR_WORKER_NOT_FOUND.format(worker_identifier))
        kx_process_identifier = self.workers[worker_identifier]
        try:
            response = self.ipc_server.send_blocking_request(kx_process_identifier, "get_worker_status",
                                                             {"identifier": worker_identifier})
            if response["status"] == "error":
                ex = deserialize(response["return"])
                raise ex
            return response["return"]
        except (SocketServerSendError, SocketServerClientNotFound, GenericException, WorkerMethodCallError) as e:
            raise e.add_ctx(CORE_WORKER_GET_STATUS_ERROR.format(worker_identifier, kx_process_identifier))
