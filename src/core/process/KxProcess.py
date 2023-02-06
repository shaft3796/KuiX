"""
This file implements a class to manage a KxProcess running process components and workers.
"""
import multiprocessing
import os
import signal

from src.core.Utils import BlockingEndpoint, Respond, WorkerStatus
from src.core.event import ProcessEvent, EventHandler
from src.core.ipc.IpcClient import IpcClient
from src.core.Exceptions import *
from src.core.Logger import LOGGER, CORE
from src.strategies.BaseStrategy import StrategyStatus
import importlib.util
import sys


class KxProcess:

    def __init__(self, identifier: str, root_path: str, auth_key: str, host: str = "localhost", port: int = 6969,
                 artificial_latency: float = 0.1, **kwargs):
        """
        Instance a KxProcess to host workers.
        :param identifier: Unique identifier of the process.
        :param root_path: Root path of KuiX.
        :param auth_key: Authentication key to connect to the server.
        :param host: host of the server.
        :param port: port of the server.
        :param artificial_latency: Time in s between each .recv call for a connection. Default is 0.1s.
        This is used to prevent the CPU from being overloaded. Change this value if you know what you're doing.

        :raise SocketClientConnectionError: If the client failed to connect to the server, you can access the initial
        exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised exception.
        """

        # Process
        self.pid = multiprocessing.current_process().pid

        # Args
        self.identifier = identifier
        self.root_path = root_path
        self.auth_key = auth_key
        self.host = host
        self.port = port
        self.artificial_latency = artificial_latency

        # Events
        self.event_handler = EventHandler()
        # add events
        self.event_handler.new_event(ProcessEvent.PROCESS_SCHEDULED_TO_CLOSE)
        self.event_handler.new_event(ProcessEvent.WORKER_CREATED)
        self.event_handler.new_event(ProcessEvent.WORKER_STARTED)
        self.event_handler.new_event(ProcessEvent.WORKER_STOPPED)
        self.event_handler.new_event(ProcessEvent.WORKER_CLOSED)

        # IPC setup
        try:
            self.ipc = IpcClient(identifier, auth_key, host, port, artificial_latency, event_handler=self.event_handler)
        except SocketClientConnectionError as e:
            raise e.add_ctx(f"KxProcess '{identifier}' setup error.")

        # Strategies
        # Hold strategies classes to instance workers
        self.strategies = {}  # type dict[name: str, type]

        # Workers
        # Hold workers (strategies instances)
        self.workers = {}  # type dict[identifier: str, instance of strategy]

        # add native remote endpoint.
        for method in [getattr(self, method_name) for method_name in dir(self)
                       if callable(getattr(self, method_name))]:
            if hasattr(method, "faf_endpoint"):
                self.ipc.endpoints[getattr(method, "faf_endpoint")] = method
            if hasattr(method, "blocking_endpoint"):
                self.ipc.blocking_endpoints[getattr(method, "blocking_endpoint")] = method

        LOGGER.info(f"KxProcess '{identifier}' setup complete.", CORE)

        # Placeholder for worker endpoints
        self.worker_endpoints = {}  # dict[name: str, dict[worker_id: str, callback: function]]
        self.worker_blocking_endpoints = {}  # dict[name: str, dict[worker_id: str, callback: function]]

    def __close_process__(self, rid):
        """
        This method try to close and close properly all workers and components of the process.
        Then the process is self-killed.
        """
        # Trigger event
        self.event_handler.trigger(ProcessEvent.PROCESS_SCHEDULED_TO_CLOSE, event_ctx=f"KxProcess '{self.identifier}': "
                                                                                      f"process scheduled to close.")
        # Try to close properly the process and all components
        for worker in self.workers.values():
            try:
                worker.close_worker()
            except Exception as e:
                LOGGER.error_exception(cast(e, f"KxProcess '{self.identifier}': "
                                               f"error while closing a worker "
                                               f"during"
                                               f"_close_process, look at the initial exception for more details.",
                                            WorkerMethodCallError), CORE)

        # Final response
        self.ipc.send_response("close_process", {"status": "success", "return": "Successfully killed process."}, rid)

        try:
            self.ipc.close()
        except SocketClientCloseError as e:
            LOGGER.error_exception(e.add_ctx(f"KxProcess '{self.identifier}': "
                                             f"error while closing the IPC client during _close_process."), CORE)
        # Finally, kill the process
        LOGGER.info(f"KxProcess '{self.identifier}': killing the process.", CORE)
        os.kill(os.getpid(), signal.SIGKILL)

    # --- Workers and strategies management ---
    def add_strategy(self, name: str, import_path: str):
        """
        add a strategy to be used by the process.
        :param name: Name of the strategy, this have to be the name of the class to import.
        :param import_path: Absolute path of the module file where the strategy is located.

        :raise KxProcessStrategyImportError: If the strategy can't be imported, you can access the initial
        exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised exception.
        """
        try:
            spec = importlib.util.spec_from_file_location("ExternalStrategy", import_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules["ExternalStrategy"] = module
            spec.loader.exec_module(module)
            strategy = getattr(module, name)
        except Exception as e:
            raise KxProcessStrategyImportError(f"KxProcess {self.identifier} _add_strategy: "
                                               f"unable to import strategy at {import_path}, "
                                               f"look at the initial exception for more details.") + e
        # add strategy
        self.strategies[name] = strategy
        LOGGER.trace(f"KxProcess '{self.identifier}': strategy '{name}' added.", CORE)

    def create_worker(self, strategy_name: str, identifier: str, config: dict):
        """
        Instance a worker from a strategy class.
        :param strategy_name: name of the strategy to use.
        Actually the name of the class you passed to add_strategy.
        :param identifier: Unique identifier of the worker.
        :param config: A dictionary containing all arguments to pass to the strategy __init__ method.

        :raise StrategyNotFoundError: If the strategy is not added.
        :raise WorkerAlreadyExistsError: If the worker already exists.
        :raise WorkerInitError: If the worker can't be initialized, you can access the initial
        exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised exception.
        :raise GenericException: If the worker can't be initialized, you can access the initial
        exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised exception.
        """
        # Create worker
        try:
            # Check if strategy is added
            if strategy_name not in self.strategies:
                raise StrategyNotFoundError(f"KxProcess {self.identifier} _create_worker: strategy "
                                            f"'{strategy_name}' not found.")

            # Check if the worker already exists
            if identifier in self.workers:
                raise WorkerAlreadyExistsError(f"KxProcess {self.identifier} _create_worker: worker "
                                               f"'{identifier}' already exists.")
            if config != {}:
                worker = self.strategies[strategy_name](self, identifier, config)
            else:
                worker = self.strategies[strategy_name](self, identifier)
            # trigger event
            self.event_handler.trigger(ProcessEvent.WORKER_CREATED, event_ctx=f"KxProcess '{self.identifier}': "
                                                                              f"worker '{identifier}' created.",
                                       worker_identifier=identifier)
        except Exception as e:
            raise cast(e, e_type=WorkerInitError, msg=f"KxProcess {self.identifier} _create_worker: worker "
                                                      f"'{identifier}' failed to init.")

        # add worker
        self.workers[identifier] = worker
        LOGGER.trace(f"KxProcess '{self.identifier}': worker '{identifier}' created.", CORE)

    def start_worker(self, identifier: str):
        """
        Call the __start__ method of a worker.
        :param identifier: Identifier of the worker.

        :raise WorkerNotFoundError: If the worker is not added.
        :raise WorkerMethodCallError: If the worker can't be started, you can access the initial
        exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised exception.
        :raise GenericException: If the worker can't be started, you can access the initial
        exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised exception.
        """
        # Start worker
        try:
            # Check if worker exists
            if identifier not in self.workers:
                raise WorkerNotFoundError(f"KxProcess {self.identifier} _start_worker: worker "
                                          f"'{identifier}' not found.")
            self.workers[identifier].__start__()
            # trigger event
            self.event_handler.trigger(ProcessEvent.WORKER_STARTED, event_ctx=f"KxProcess '{self.identifier}': "
                                                                              f"worker '{identifier}' started.",
                                       worker_identifier=identifier)
        except Exception as e:
            raise cast(e, e_type=WorkerMethodCallError, msg=f"KxProcess {self.identifier} _start_worker: "
                                                            f"worker '{identifier}' failed to start.")

        LOGGER.trace(f"KxProcess '{self.identifier}': worker '{identifier}' started.", CORE)

    def stop_worker(self, identifier: str):
        """
        Call the __stop__ method of a worker.
        :param identifier: Identifier of the worker.

        :raise WorkerNotFoundError: If the worker is not added.
        :raise WorkerMethodCallError: If the worker can't be stopped, you can access the initial
        exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised exception.
        :raise GenericException: If the worker can't be stopped, you can access the initial
        exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised exception.
        """
        # Stop worker
        try:
            # Check if worker exists
            if identifier not in self.workers:
                raise WorkerNotFoundError(f"KxProcess {self.identifier} _stop_worker: worker "
                                          f"'{identifier}' not found.")
            self.workers[identifier].__stop__()
            # trigger event
            self.event_handler.trigger(ProcessEvent.WORKER_STOPPED, event_ctx=f"KxProcess '{self.identifier}': "
                                                                              f"worker '{identifier}' stopped.",
                                       worker_identifier=identifier)
        except Exception as e:
            raise cast(e, e_type=WorkerMethodCallError, msg=f"KxProcess {self.identifier} _stop_worker: worker "
                                                            f"'{identifier}' failed to stop.")

        LOGGER.trace(f"KxProcess '{self.identifier}': worker '{identifier}' stopped.", CORE)

    def close_worker(self, identifier: str):
        """
        Call the __close__ method of a worker.
        :param identifier: Identifier of the worker.

        :raise WorkerNotFoundError: If the worker is not added.
        :raise WorkerMethodCallError: If the worker can't be closed, you can access the initial
        exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised exception.
        :raise GenericException: If the worker can't be closed, you can access the initial
        exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised exception.
        """
        # close worker
        try:
            # Check if worker exists
            if identifier not in self.workers:
                raise WorkerNotFoundError(f"KxProcess {self.identifier} _start_worker: worker "
                                          f"'{identifier}' not found.")
            self.workers[identifier].__close__()
            # trigger event
            self.event_handler.trigger(ProcessEvent.WORKER_CLOSED, event_ctx=f"KxProcess '{self.identifier}': "
                                                                             f"worker '{identifier}' closed.",
                                       worker_identifier=identifier)
            del self.workers[identifier]
        except Exception as e:
            raise cast(e, e_type=WorkerMethodCallError, msg=f"KxProcess {self.identifier} _close_worker: worker "
                                                            f"'{identifier}' failed to being closed.")

        LOGGER.trace(f"KxProcess '{self.identifier}': worker '{identifier}' closed.", CORE)

    def get_worker_status(self, identifier: str) -> str:
        """
        Get the status of a worker.
        :param identifier: Identifier of the worker.

        :return: The status of the worker. (WorkerStatus.RUNNING, WorkerStatus.STOPPED, WorkerStatus.CLOSED)

        :raise WorkerMethodCallError: if accessing the worker status failed, you can access the initial
        exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised exception.
        """
        try:
            status = ""
            # Check if worker exists
            if identifier not in self.workers:
                status = WorkerStatus.CLOSED
            else:
                status = WorkerStatus.RUNNING if self.workers[identifier].get_status() == StrategyStatus.RUNNING \
                                                 or self.workers[identifier].get_status() == StrategyStatus.STOPPING \
                    else WorkerStatus.STOPPED
        except AttributeError as e:
            raise WorkerMethodCallError(f"KxProcess {self.identifier} _get_worker_status: worker "
                                        f"'{identifier}' failed to get status.") + e
        return status

    # --- IPC ---
    def add_endpoint(self, name: str, callback: callable):
        """
        add an endpoint, a method accessible from the core through the IPC.
        :param name: Name of the endpoint.
        :param callback: Callback function to call when the endpoint is called. The callback must only have one
        parameter which is the data sent by the core as a dict.
        """
        if name in self.ipc.endpoints:
            LOGGER.warning(f"KxProcess {self.identifier} add_endpoint: endpoint '{name}' already exists, "
                           f"the first endpoint will be overwritten but this is probably an unexpected behavior.", CORE)
        self.ipc.endpoints[name] = callback

        LOGGER.trace(f"KxProcess '{self.identifier}': endpoint '{name}' added.", CORE)

    def add_blocking_endpoint(self, name: str, callback: callable):
        """
        add a blocking endpoint, a method accessible from the core through the IPC.
        This endpoint is blocking, the core will wait for a response.
        To send a response, decorate your callback with 'Respond('endpoint_name')' from utils module and return a
        dictionary or use directly the 'self.send_response' method.
        WARNING: This is a blocking method, it will block the core until the endpoint returns a value, if your method
        does not send a response using the 'self.send_response' method, some methods will block forever !
        :param name: Name of the endpoint.
        :param callback: Callback function to call when the endpoint is called. This function must absolutely
        call only one time the 'self.send_response' method, directly or by being decorated using the 'Respond'
        decorator.
        The callback must only have two parameters:
        'rid' which is the request id as a str and 'data' which is the data sent by the core as a dict.
        """
        if name in self.ipc.endpoints:
            LOGGER.warning(f"KxProcess {self.identifier} add_blocking_endpoint: endpoint '{name}' already exists, "
                           f"the first endpoint will be overwritten but this is probably an unexpected behavior.", CORE)
        self.ipc.blocking_endpoints[name] = callback

        LOGGER.trace(f"KxProcess '{self.identifier}': blocking endpoint '{name}' added.", CORE)

    def add_worker_endpoint(self, name: str, worker_id: str, callback: callable):
        """
        add a worker endpoint, a method accessible from the core through the IPC.
        This endpoint can be added multiple times with different worker_id, when this endpoint is called by
        the core, a worker_id must being specified to call the correct callback.
        :param name: Name of the endpoint.
        :param worker_id: Unique worker identifier.
        :param callback: Callback function to call when the endpoint is called. This function must absolutely
        call only one time the 'self.send_response' method. The callback must only have two parameters:
        'rid' which is the request id as a str and 'data' which is the data sent by the core as a dict.
        """
        # If new endpoint, initialize the routing function and the callback dict.
        if name not in self.worker_endpoints:
            self.worker_endpoints[name] = {}

            # routing
            def __routing__(data: dict):
                try:
                    self.worker_endpoints[name][data["worker_id"]](data)
                except Exception as e:
                    LOGGER.error_exception(cast(e, e_type=WorkerMethodCallError, msg="KxProcess error while calling "
                                                                                     "worker endpoint"), CORE)

            if worker_id in self.worker_endpoints[name]:
                LOGGER.warning(f"KxProcess {self.identifier} add_worker_endpoint: endpoint '{name}' already "
                               f"exists for the worker '{worker_id}', the first endpoint will be overwritten but "
                               f"this is probably an unexpected behavior.", CORE)
            self.ipc.endpoints[name] = __routing__  # adding routing function as the endpoint.

        # add the worker callback
        self.worker_endpoints[name][worker_id] = callback

        LOGGER.trace(f"KxProcess '{self.identifier}': worker endpoint '{name}' added.", CORE)

    def add_worker_blocking_endpoint(self, name: str, worker_id: str, callback: callable):
        """
        add a worker blocking endpoint, a method accessible from the core through the IPC.
        This endpoint can be added multiple times with different worker_id, when this endpoint is called by
        the core, a worker_id must being specified to call the correct callback.
        This endpoint is blocking, the core will wait for the endpoint to send a response.
        To send a response, decorate your callback with 'Respond('endpoint_name')' from utils module and return a
        dictionary or use directly the 'self.send_response' method.
        WARNING: This is a blocking method, it will block the core until the endpoint returns a value, if your method
        does not send a response using the 'self.send_response' method, some methods will block forever !
        :param name: Name of the endpoint.
        :param worker_id: Unique worker identifier.
        :param callback: Callback function to call when the endpoint is called. This function must absolutely
        call only one time the 'self.send_response' method, directly or by being decorated using the 'Respond'
        decorator.
        The callback must only have two parameters: 'rid' which is the request id as a str and 'data' which is the
        data sent by the core as a dict.
        """
        # If new endpoint, initialize the routing function and the callback dict.
        if name not in self.worker_blocking_endpoints:
            self.worker_blocking_endpoints[name] = {}

            # routing
            def __routing__(rid: str, data: dict):
                try:
                    self.worker_blocking_endpoints[name][data["worker_id"]](rid, data)
                except Exception as e:
                    LOGGER.error_exception(cast(e, e_type=WorkerMethodCallError, msg=f"KxProcess '{self.identifier}' "
                                                                                     f"error while calling "
                                                                                     "worker blocking endpoint"), CORE)

            if worker_id in self.worker_endpoints[name]:
                LOGGER.warning(f"KxProcess {self.identifier} add_worker_blocking_endpoint: endpoint '{name}' "
                               f"already"
                               f"exists for the worker '{worker_id}', the first endpoint will be overwritten but "
                               f"this is probably an unexpected behavior.", CORE)
            self.ipc.blocking_endpoints[name] = __routing__  # adding routing function as the endpoint.

        # add the worker callback
        self.worker_blocking_endpoints[name][worker_id] = callback

        LOGGER.trace(f"KxProcess '{self.identifier}': worker blocking endpoint '{name}' added.", CORE)

    def send(self, endpoint: str, data: dict):
        """
        Send data as a dict to the core through the IPC.
        :param endpoint: Name of the endpoint to call on the core as added with the 'add_endpoint'
        method of the core.
        :param data: Data to send as a dict

        :raises SocketClientSendError: if an error occurred while sending the data to the core, you can access
        the initial exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised
        exception.
        """
        try:
            self.ipc.send_fire_and_forget_request(endpoint, data)
        except SocketClientSendError as e:
            raise e.add_ctx(f"KxProcess {self.identifier} _ipc_send: error while sending data to "
                            f"endpoint '{endpoint}'.")

        LOGGER.trace(f"KxProcess '{self.identifier}': data sent to endpoint '{endpoint}'.", CORE)

    def send_blocking(self, endpoint: str, data: dict):
        """
        Send data as a dict to the core through the IPC and wait for the response.
        :param endpoint: Name of the endpoint to call on the core as added with the 'add_endpoint'
        method of the core.
        :param data: Data to send as a dict

        :raises SocketClientSendError: if an error occurred while sending the data to the core, you can access
        the initial exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised
        exception.
        """
        try:
            return self.ipc.send_blocking_request(endpoint, data)
        except SocketClientSendError as e:
            raise e.add_ctx(f"KxProcess {self.identifier} _ipc_send: error while sending data to blocking "
                            f"endpoint '{endpoint}'.")

    def send_response(self, endpoint: str, data: dict, rid: str):
        """
        Send the response of a blocking request.
        :param endpoint: Name of the endpoint to call on the core as added with the 'add_endpoint'
        :param data: Data to send as a dict
        :param rid: Request id of the request to respond to.

        :raises SocketClientSendError: if an error occurred while sending the data to the core, you can access
        the initial exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised
        exception.
        """
        try:
            self.ipc.send_response(endpoint, data, rid)
        except SocketClientSendError as e:
            raise e.add_ctx(f"KxProcess {self.identifier} _ipc_send_response: error while sending response to blocking "
                            f"endpoint '{endpoint}'.")

        LOGGER.trace(f"KxProcess '{self.identifier}': response sent to endpoint '{endpoint}'.", CORE)

    # --- Native Endpoints ---
    # Workers and Strategies
    @BlockingEndpoint("add_strategy")
    @Respond("add_strategy")
    def __remote_add_strategy__(self, rid: str, data: dict):
        try:
            self.add_strategy(data["name"], data["import_path"])
            ret_data = {"status": "success", "return": "Successfully added strategy."}
        except KxProcessStrategyImportError as e:
            ret_data = {"status": "error", "return": e.serialize()}
        return ret_data

    @BlockingEndpoint("create_worker")
    @Respond("create_worker")
    def __remote_create_worker__(self, rid: str, data: dict):
        try:
            self.create_worker(data["strategy_name"], data["identifier"], data["config"])
            ret_data = {"status": "success", "return": "Successfully created worker."}
        except (StrategyNotFoundError, WorkerAlreadyExistsError, GenericException) as e:
            ret_data = {"status": "error", "return": e.serialize()}
        return ret_data

    @BlockingEndpoint("start_worker")
    @Respond("start_worker")
    def __remote_start_worker__(self, rid: str, data: dict):
        try:
            self.start_worker(data["identifier"])
            ret_data = {"status": "success", "return": "Successfully started worker."}
        except (WorkerNotFoundError, GenericException, WorkerMethodCallError) as e:
            ret_data = {"status": "error", "return": e.serialize()}
        return ret_data

    @BlockingEndpoint("stop_worker")
    @Respond("stop_worker")
    def __remote_stop_worker__(self, rid: str, data: dict):
        try:
            self.stop_worker(data["identifier"])
            ret_data = {"status": "success", "return": "Successfully stopped worker."}
        except (WorkerNotFoundError, GenericException, WorkerMethodCallError) as e:
            ret_data = {"status": "error", "return": e.serialize()}
        return ret_data

    @BlockingEndpoint("close_worker")
    @Respond("close_worker")
    def __remote_close_worker__(self, rid: str, data: dict):
        try:
            self.close_worker(data["identifier"])
            ret_data = {"status": "success", "return": "Successfully closed worker."}
        except (WorkerNotFoundError, GenericException, WorkerMethodCallError) as e:
            ret_data = {"status": "error", "return": e.serialize()}
        return ret_data

    @BlockingEndpoint("get_worker_status")
    @Respond("get_worker_status")
    def __remote_get_worker_status__(self, rid: str, data: dict):
        try:
            ret_data = {"status": "success", "return": self.get_worker_status(data["identifier"])}
        except WorkerMethodCallError as e:
            ret_data = {"status": "error", "return": e.serialize()}
        return ret_data

    # Process
    @BlockingEndpoint("close_process")
    def __remote_close_process__(self, rid: str, data: dict):
        self.__close_process__(rid)


def __launch__(identifier: str, root_path: str, auth_key: str, host: str = "localhost", port: int = 6969,
               artificial_latency: float = 0.1, additional_args: dict = None):
    # IN A SUBPROCESS
    if additional_args is None:
        additional_args = {}
    try:
        # Create process
        process = KxProcess(identifier, root_path, auth_key, host, port, artificial_latency, **additional_args)
    except SocketClientConnectionError as e:
        e.add_ctx(f"KxProcess '{identifier}' launch: error while creating the KxProcess.")
        LOGGER.error_exception(e, CORE)
