from src.core.network.SocketClient import SocketClient
from src.core.Logger import LOGGER, KX_PROCESS
from src.core.messages.IPCClientMessages import *
from src.core.event import ProcessEvent
from src.core.Exceptions import *
import threading
import time
import uuid

# Request types
FIRE_AND_FORGET = "FIRE_AND_FORGET"
BLOCKING = "BLOCKING"
RESPONSE = "RESPONSE"


class IpcClient(SocketClient):

    def __init__(self, identifier: str, auth_key: str, host: str = "localhost", port: int = 6969,
                artificial_latency: float = 0.1, event_handler=None):
        """
        Instance an ipc client used for inter process communication (IPC).
        This client extends the SocketClient class and add the ability to add endpoints and send requests to them.
        :param identifier: The identifier of the client.
        :param auth_key: The key to authenticate the client.
        :param port: The port to connect on. Default is 6969.
        :param host: The host to connect  on. Default is localhost.
        :param artificial_latency: Time in s between each .recv call for a connection. Default is 0.1s. This is used to
        prevent the CPU from being overloaded. Change this value if you know what you're doing.
        :param event_handler: The event handler to use. Default is None.

        :raise SocketClientConnectionError: If the client failed to connect to the server, you can access the initial
        exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised exception.
        """
        # Super call
        super().__init__(identifier, auth_key, host, port, artificial_latency, event_handler)
        try:
            self.connect()
        except SocketClientConnectionError as e:
            raise e.add_ctx(IPC_CLI_INIT_ERROR.format(identifier))

        # Placeholder for endpoints
        self.endpoints = {}  # type dict[str, Callable]
        self.blocking_endpoints = {}  # type dict[str, Callable]

        # Placeholder for blocking requests
        self.blocking_requests = {}  # type dict[str: id, list [semaphore, response]]

        # Subscribe to the request handler
        self.event_handler.subscribe(ProcessEvent.SOCKET_MESSAGE_RECEIVED, self.handle_request)

        # add IPC events
        self.event_handler.new_event(ProcessEvent.IPC_FAF_REQUEST_RECEIVED)
        self.event_handler.new_event(ProcessEvent.IPC_BLOCKING_REQUEST_RECEIVED)
        self.event_handler.new_event(ProcessEvent.IPC_RESPONSE_RECEIVED)
        self.event_handler.new_event(ProcessEvent.IPC_FAF_REQUEST_EXCEPTION)
        self.event_handler.new_event(ProcessEvent.IPC_BLOCKING_REQUEST_EXCEPTION)
        self.event_handler.new_event(ProcessEvent.IPC_RESPONSE_EXCEPTION)
        self.event_handler.new_event(ProcessEvent.IPC_FAF_REQUEST_HANDLED)
        self.event_handler.new_event(ProcessEvent.IPC_BLOCKING_REQUEST_HANDLED)
        self.event_handler.new_event(ProcessEvent.IPC_RESPONSE_HANDLED)
        self.event_handler.new_event(ProcessEvent.IPC_FAF_REQUEST_SENT)
        self.event_handler.new_event(ProcessEvent.IPC_BLOCKING_REQUEST_SENT)
        self.event_handler.new_event(ProcessEvent.IPC_RESPONSE_SENT)

    # Requests handler, triggered when a message is received
    def handle_request(self, identifier: str, data: dict):
        """
        Handle a request received from the server.
        Automatically called when a message is received.
        :param identifier: identifier of the client (same as self.identifier)
        :param data: The data received from the server as a dict.
        """
        try:
            # Fire and forget request
            if data["rtype"] == FIRE_AND_FORGET:
                self.__trigger__(ProcessEvent.IPC_FAF_REQUEST_RECEIVED,
                                 event_ctx=IPC_CLI_HANDLE_TRACE_RECEIVED_FAF.format(identifier, data),
                                 identifier=identifier, data=data)
                if data["endpoint"] not in self.endpoints:
                    e = UnknownEndpoint(IPC_CLI_HANDLE_ERROR_FAF_ENDPOINT_NOT_FOUND
                                        .format(identifier, data["endpoint"]))
                    LOGGER.error_exception(e, KX_PROCESS)
                    self.__trigger__(ProcessEvent.IPC_FAF_REQUEST_EXCEPTION,
                                     event_ctx=IPC_CLI_HANDLE_ERROR_FAF_ENDPOINT_NOT_FOUND
                                     .format(identifier, data["endpoint"]),
                                     identifier=identifier, data=data, exception=e)
                    return
                self.endpoints[data["endpoint"]](data["data"])
                self.__trigger__(ProcessEvent.IPC_FAF_REQUEST_HANDLED,
                                 event_ctx=IPC_CLI_HANDLE_TRACE_HANDLED_FAF.format(identifier, data["endpoint"]),
                                 identifier=identifier, data=data)

            # Blocking request
            elif data["rtype"] == BLOCKING:
                self.__trigger__(ProcessEvent.IPC_BLOCKING_REQUEST_RECEIVED,
                                 event_ctx=IPC_CLI_HANDLE_TRACE_RECEIVED_BLOCK.format(identifier, data),
                                 identifier=identifier, data=data)
                if data["endpoint"] not in self.blocking_endpoints:
                    e = UnknownEndpoint(IPC_CLI_HANDLE_ERROR_BLOCK_ENDPOINT_NOT_FOUND
                                        .format(identifier, data["endpoint"]))
                    LOGGER.error_exception(e, KX_PROCESS)
                    self.__trigger__(ProcessEvent.IPC_BLOCKING_REQUEST_EXCEPTION,
                                     event_ctx=IPC_CLI_HANDLE_ERROR_BLOCK_ENDPOINT_NOT_FOUND
                                     .format(identifier, data["endpoint"]),
                                     identifier=identifier, data=data, exception=e)
                    return
                self.blocking_endpoints[data["endpoint"]](data["rid"], data["data"])
                self.__trigger__(ProcessEvent.IPC_BLOCKING_REQUEST_HANDLED,
                                 event_ctx=IPC_CLI_HANDLE_TRACE_HANDLED_BLOCK.format(identifier, data["endpoint"]),
                                 identifier=identifier, data=data)

            # Response request
            elif data["rtype"] == RESPONSE:
                self.__trigger__(ProcessEvent.IPC_RESPONSE_RECEIVED,
                                 event_ctx=IPC_CLI_HANDLE_TRACE_RECEIVED_RESPONSE.format(identifier, data),
                                 identifier=identifier, data=data)
                for i in range(2):
                    if data["rid"] not in self.blocking_requests:
                        time.sleep(0.2)
                if data["rid"] not in self.blocking_requests:
                    e = UnknownRid(IPC_CLI_HANDLE_ERROR_RESPONSE_RID_NOT_FOUND
                                   .format(identifier, data["rid"]))
                    LOGGER.error_exception(e, KX_PROCESS)
                    self.__trigger__(ProcessEvent.IPC_RESPONSE_EXCEPTION,
                                     event_ctx=IPC_CLI_HANDLE_ERROR_RESPONSE_RID_NOT_FOUND
                                     .format(identifier, data["rid"]),
                                     identifier=identifier, data=data, exception=e)
                    return
                self.blocking_requests[data["rid"]][1] = data["data"]
                self.blocking_requests[data["rid"]][0].release()
                self.__trigger__(ProcessEvent.IPC_RESPONSE_HANDLED,
                                 event_ctx=IPC_CLI_HANDLE_TRACE_HANDLED_RESPONSE.format(identifier, data["rid"]),
                                 identifier=identifier, data=data)

            # Unknown request type
            else:
                e = UnknownRequestType(IPC_CLI_HANDLE_ERROR_UNKNOWN_REQUEST_TYPE.format(identifier, data["rtype"]))
                LOGGER.error_exception(e, KX_PROCESS)
                self.__trigger__(ProcessEvent.IPC_HANDLER_EXCEPTION,
                                 event_ctx=IPC_CLI_HANDLE_ERROR_UNKNOWN_REQUEST_TYPE.format(identifier, data["rtype"]),
                                 identifier=identifier, data=data, exception=e)

        except KeyError as e:
            _e = IpcServerRequestHandlerError(IPC_CLI_HANDLE_ERROR.format(identifier, data)) + e
            LOGGER.error_exception(e, KX_PROCESS)
            self.__trigger__(ProcessEvent.IPC_HANDLER_EXCEPTION,
                             event_ctx=IPC_CLI_HANDLE_ERROR.format(identifier, data),
                             identifier=identifier, data=data, exception=_e)

        except Exception as e:
            _e = IpcServerRequestHandlerError(IPC_CLI_HANDLE_ERROR.format(identifier, data)) + e
            LOGGER.error_exception(_e, KX_PROCESS)
            self.__trigger__(ProcessEvent.IPC_HANDLER_EXCEPTION,
                             event_ctx=IPC_CLI_HANDLE_ERROR.format(identifier, data),
                             identifier=identifier, data=data, exception=_e)

    def add_endpoint(self, endpoint: str, callback):
        """
        add an endpoint to the client.
        :param endpoint: endpoint as a str.
        :param callback: callback function to call when a request is received on this endpoint.
        """
        self.endpoints[endpoint] = callback

    # --- Sending ---

    # Fire and forget
    def send_fire_and_forget_request(self, endpoint: str, data: dict):
        """
        Send data through a fire and forget request to the server.
        This method will directly return after sending the request.
        :param endpoint: endpoint as a str, this endpoint must be added.
        :param data: data to send as a dict.

        :raise SocketClientSendError: If the client failed to send the request, you can access the initial
        exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised exception.
        """
        try:
            self.send_data({"rtype": FIRE_AND_FORGET, "endpoint": endpoint, "data": data})
            self.__trigger__(ProcessEvent.IPC_FAF_REQUEST_SENT,
                            event_ctx=IPC_CLI_SEND_FAF_CTX.format(self.identifier, endpoint, data),
                            identifier=self.identifier, data=data)
        except SocketClientSendError as e:
            raise e.add_ctx(IPC_CLI_SEND_FAF_ERROR.format(self.identifier, endpoint, data))

    # blocking request
    def send_blocking_request(self, endpoint: str, data: dict):
        """
        Send data through a blocking request to the server.
        This method will block until the server send the response.
        Warning, if the server doesn't send the response, this method will block forever.
        Be sure to add the endpoint on the server side with a correct response.
        :param endpoint: endpoint as a str, this endpoint must be added.
        :param data: data to send as a dict.

        :raise SocketClientSendError: If the client failed to send the request, you can access the initial
        exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised exception.
        """
        # Create a unique id for the request
        rid = str(uuid.uuid4())
        # Create a locked semaphore
        semaphore = threading.Semaphore(0)
        # Create a placeholder for the response
        response = None
        # Fill the response placeholder
        self.blocking_requests[rid] = [semaphore, response]
        # Send the request
        try:
            self.send_data({"rtype": BLOCKING, "endpoint": endpoint, "data": data, "rid": rid})
            self.__trigger__(ProcessEvent.IPC_BLOCKING_REQUEST_SENT,
                            event_ctx=IPC_CLI_SEND_BLOCK_CTX.format(self.identifier, endpoint, data, rid),
                            identifier=self.identifier, data=data)
        except SocketClientSendError as e:
            raise e.add_ctx(IPC_CLI_SEND_BLOCK_ERROR.format(self.identifier, endpoint, data, rid))
        # Wait for the response
        semaphore.acquire()
        # Return the response
        resp = self.blocking_requests[rid][1]
        del self.blocking_requests[rid]
        return resp

    # responses
    def send_response(self, endpoint: str, data: dict, rid: str):
        """
        Send response to a blocking request to the server.
        This method will directly return after sending the response.
        :param endpoint: endpoint as a str.
        :param data: data to send as a dict.
        :param rid: request id as a str, this id must be the same as the one received in the initial blocking request.

        :raise SocketClientSendError: If the client failed to send the request, you can access the initial
        exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised exception.
        """
        try:
            self.send_data({"rtype": RESPONSE, "endpoint": endpoint, "data": data, "rid": rid})
        except SocketClientSendError as e:
            raise e.add_ctx(IPC_CLI_SEND_RESPONSE_ERROR.format(self.identifier, endpoint, rid, data))
        self.__trigger__(ProcessEvent.IPC_RESPONSE_SENT,
                        event_ctx=IPC_CLI_SEND_RESPONSE_CTX.format(self.identifier, endpoint, rid, data),
                        identifier=self.identifier, data=data)
