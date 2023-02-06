from src.core.event import CoreEvent
from src.core.network.SocketServer import SocketServer
from src.core.Logger import LOGGER, CORE
from src.core.messages.IPCServerMessages import *
from src.core.Exceptions import *
import threading
import time
import uuid

# Request types
FIRE_AND_FORGET = "FIRE_AND_FORGET"
BLOCKING = "BLOCKING"
RESPONSE = "RESPONSE"


class IpcServer(SocketServer):

    def __init__(self, auth_key: str, host: str = "localhost", port: int = 6969,
                artificial_latency: float = 0.1, event_handler=None):
        """
                Instance an ipc server used for inter process communication (IPC).
                This server extends the SocketServer class and add the ability to add endpoints and send
                requests to them.
                :param auth_key: The key to authenticate clients.
                :param port (optional): The port to connect on. Default is 6969.
                :param host (optional): The host to connect  on. Default is localhost.
                :param artificial_latency (optional): Time in s between each .recv call for a connection. Default is 0.1s.
                This is used to prevent the CPU from being overloaded. Change this value if you know what you're doing.
                :param event_handler (optional): The event handler to use. Default is None.

                Communication protocol:

                I-) FireAndForget request:
                1) Client or server sends a request to an endpoint of the other party.
                2) Client or server returns directly after sending the request.
                3) The other party processes the request and can send another request if necessary.
                request = {rtype: "FIRE_AND_FORGET", endpoint: "endpoint", data: {...}}

                II-) Blocking request:
                1) Client or server sends a request to an endpoint of the other party, the sender add a unique id to the request.
                2) Client or server locks on a new semaphore.
                3) The other party processes the request and send the response with a "rid" field.
                4) Client or server socket threads unlock the semaphore.
                5) Client or server request call unlocks and return the response
                request = {rtype: "BLOCKING", endpoint: "endpoint", data: {...}, rid: "unique_id"}

                III-) Response:
                1) Other party receives a blocking request on an endpoint.
                2) Other party processes the request and send the response as a RESPONSE request with a "rid" field.
                3) Client or server receives the response, save it, and release the lock.
                4) Client or server initial blocking request call return the response.
                request = {rtype: "RESPONSE", endpoint: "endpoint", data: {...}, rid: "unique_id"}

                :raise SocketServerBindError: If the server fails to bind to the specified host and port.
                """
        # Super call
        try:
            super().__init__(auth_key, host, port, artificial_latency, event_handler)
        except SocketServerBindError as e:
            raise e.add_ctx(IPC_SRV_INIT_ERROR)

        # Placeholder for endpoints
        self.endpoints = {}  # type dict[str, Callable]
        self.blocking_endpoints = {}  # type dict[str, Callable]

        # Placeholder for blocking requests
        self.blocking_requests = {}  # type dict[str: id, list [semaphore, response]]

        # Subscribe to the request handler
        self.event_handler.subscribe(CoreEvent.SOCKET_MESSAGE_RECEIVED, self.handle_request)

        # add IPC events
        self.event_handler.new_event(CoreEvent.IPC_FAF_REQUEST_RECEIVED)
        self.event_handler.new_event(CoreEvent.IPC_BLOCKING_REQUEST_RECEIVED)
        self.event_handler.new_event(CoreEvent.IPC_RESPONSE_RECEIVED)
        self.event_handler.new_event(CoreEvent.IPC_FAF_REQUEST_EXCEPTION)
        self.event_handler.new_event(CoreEvent.IPC_BLOCKING_REQUEST_EXCEPTION)
        self.event_handler.new_event(CoreEvent.IPC_RESPONSE_EXCEPTION)
        self.event_handler.new_event(CoreEvent.IPC_FAF_REQUEST_HANDLED)
        self.event_handler.new_event(CoreEvent.IPC_BLOCKING_REQUEST_HANDLED)
        self.event_handler.new_event(CoreEvent.IPC_RESPONSE_HANDLED)
        self.event_handler.new_event(CoreEvent.IPC_FAF_REQUEST_SENT)
        self.event_handler.new_event(CoreEvent.IPC_BLOCKING_REQUEST_SENT)
        self.event_handler.new_event(CoreEvent.IPC_RESPONSE_SENT)

    # Requests handler, triggered when a message is received
    def handle_request(self, identifier: str, data: dict):
        """
        Handle a request received from a client.
        Automatically called when a message is received.
        :param identifier: identifier of the client.
        :param data: The data received from the client as a dict.
        """
        try:
            # Fire and forget request
            if data["rtype"] == FIRE_AND_FORGET:
                # Received
                LOGGER.trace(IPC_SRV_HANDLE_TRACE_RECEIVED_FAF.format(identifier, data), CORE)
                self.__trigger__(CoreEvent.IPC_FAF_REQUEST_RECEIVED,
                                event_ctx=IPC_SRV_HANDLE_TRACE_RECEIVED_FAF.format(identifier, data),
                                identifier=identifier, data=data)

                # Error 1
                if data["endpoint"] not in self.endpoints:
                    e = UnknownEndpoint(IPC_SRV_HANDLE_ERROR_FAF_ENDPOINT_NOT_FOUND
                                        .format(identifier, data["endpoint"]))
                    LOGGER.error_exception(e, CORE)
                    self.__trigger__(CoreEvent.IPC_FAF_REQUEST_EXCEPTION,
                                    event_ctx=IPC_SRV_HANDLE_ERROR_FAF_ENDPOINT_NOT_FOUND
                                    .format(identifier, data["endpoint"]),
                                    identifier=identifier, data=data, exception=e)
                    return

                self.endpoints[data["endpoint"]](identifier, data["data"])  # CALL
                # Handled
                LOGGER.trace(IPC_SRV_HANDLE_TRACE_HANDLED_FAF.format(identifier, data), CORE)
                self.__trigger__(CoreEvent.IPC_FAF_REQUEST_HANDLED,
                                event_ctx=IPC_SRV_HANDLE_TRACE_HANDLED_FAF.format(identifier, data["endpoint"]),
                                identifier=identifier, data=data)

            # Blocking request
            elif data["rtype"] == BLOCKING:
                # Received
                LOGGER.trace(IPC_SRV_HANDLE_TRACE_RECEIVED_BLOCK.format(identifier, data), CORE)
                self.__trigger__(CoreEvent.IPC_BLOCKING_REQUEST_RECEIVED,
                                event_ctx=IPC_SRV_HANDLE_TRACE_RECEIVED_BLOCK.format(identifier, data),
                                identifier=identifier, data=data)

                # Error 1
                if data["endpoint"] not in self.blocking_endpoints:
                    e = UnknownEndpoint(IPC_SRV_HANDLE_ERROR_BLOCK_ENDPOINT_NOT_FOUND.format(identifier,
                                                                                            data["endpoint"]))
                    LOGGER.error_exception(e, CORE)
                    self.__trigger__(CoreEvent.IPC_BLOCKING_REQUEST_EXCEPTION,
                                    event_ctx=IPC_SRV_HANDLE_ERROR_BLOCK_ENDPOINT_NOT_FOUND.format(identifier,
                                                                                            data["endpoint"]),
                                    identifier=identifier, data=data, exception=e)
                    return

                self.blocking_endpoints[data["endpoint"]](identifier, data["rid"], data["data"])  # CALL
                # Handled
                LOGGER.trace(IPC_SRV_HANDLE_TRACE_HANDLED_BLOCK.format(identifier, data["endpoint"]), CORE)
                self.__trigger__(CoreEvent.IPC_BLOCKING_REQUEST_HANDLED,
                                event_ctx=IPC_SRV_HANDLE_TRACE_HANDLED_BLOCK.format(identifier, data["endpoint"]),
                                identifier=identifier, data=data)

            # Response request
            elif data["rtype"] == RESPONSE:
                # Received
                LOGGER.trace(IPC_SRV_HANDLE_TRACE_RECEIVED_RESPONSE.format(identifier, data), CORE)
                self.__trigger__(CoreEvent.IPC_RESPONSE_RECEIVED,
                                event_ctx=IPC_SRV_HANDLE_TRACE_RECEIVED_RESPONSE.format(identifier, data),
                                identifier=identifier, data=data)

                for i in range(2):
                    if data["rid"] not in self.blocking_requests:
                        time.sleep(0.2)

                # Error 1
                if data["rid"] not in self.blocking_requests:
                    e = UnknownRid(IPC_SRV_HANDLE_ERROR_RESPONSE_RID_NOT_FOUND.format(identifier, data["rid"]))
                    LOGGER.error_exception(e, CORE)
                    self.__trigger__(CoreEvent.IPC_RESPONSE_EXCEPTION,
                                    event_ctx=IPC_SRV_HANDLE_ERROR_RESPONSE_RID_NOT_FOUND.format(identifier,
                                                                                                data["rid"]),
                                    identifier=identifier, data=data, exception=e)
                    return

                self.blocking_requests[data["rid"]][1] = data["data"]
                self.blocking_requests[data["rid"]][0].release()
                # Handled
                LOGGER.trace(IPC_SRV_HANDLE_TRACE_HANDLED_RESPONSE.format(identifier, data["rid"]), CORE)
                self.__trigger__(CoreEvent.IPC_RESPONSE_HANDLED,
                                event_ctx=IPC_SRV_HANDLE_TRACE_HANDLED_RESPONSE.format(identifier, data["rid"]),
                                identifier=identifier, data=data)

            # Unknown request type
            else:
                e = UnknownRequestType(IPC_SRV_HANDLE_ERROR_UNKNOWN_REQUEST_TYPE.format(identifier, data["rtype"]))
                LOGGER.error_exception(e, CORE)
                self.__trigger__(CoreEvent.IPC_HANDLER_EXCEPTION,
                                event_ctx=IPC_SRV_HANDLE_ERROR_UNKNOWN_REQUEST_TYPE.format(identifier, data["rtype"]),
                                identifier=identifier, data=data, exception=e)

        except KeyError as e:
            _e = IpcServerRequestHandlerError(IPC_SRV_HANDLE_ERROR_MALFORMED_REQUEST.format(identifier, data)) + e
            LOGGER.error_exception(e, CORE)
            self.__trigger__(CoreEvent.IPC_HANDLER_EXCEPTION,
                            event_ctx=IPC_SRV_HANDLE_ERROR_MALFORMED_REQUEST.format(identifier, data),
                            identifier=identifier, data=data, exception=_e)

        except Exception as e:
            _e = IpcServerRequestHandlerError(IPC_SRV_HANDLE_ERROR.format(identifier, data)) + e
            LOGGER.error_exception(e, CORE)
            self.__trigger__(CoreEvent.IPC_HANDLER_EXCEPTION,
                            event_ctx=IPC_SRV_HANDLE_ERROR.format(identifier, data),
                            identifier=identifier, data=data, exception=_e)

    def add_endpoint(self, endpoint: str, callback):
        """
        add an endpoint to the server.
        :param endpoint: endpoint as a str.
        :param callback: callback function to call when a request is received on this endpoint.
        """
        self.endpoints[endpoint] = callback

    # --- Sending ---

    # Fire and forget
    def send_fire_and_forget_request(self, identifier: str, endpoint: str, data: dict):
        """
        Send data through a fire and forget request to a client.
        This method will directly return after sending the request.
        :param identifier: identifier of the client.
        :param endpoint: endpoint as a str, this endpoint must be added.
        :param data: data to send as a dict.

        :raise ClientIdentifierNotFound: If the client is not found. This can happen if the client is not connected
        or is the identifier is wrong.
        :raise SocketServerSendError: If the server fails to send the data, you can access the initial
        exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised exception.
        """
        try:
            self.send_data(identifier, {"rtype": FIRE_AND_FORGET, "endpoint": endpoint, "data": data})
            self.__trigger__(CoreEvent.IPC_FAF_REQUEST_SENT,
                            event_ctx=IPC_SRV_SEND_FAF_CTX.format(identifier, endpoint, data),
                            identifier=identifier, data=data)
        except SocketServerClientNotFound as e:
            raise ClientIdentifierNotFoundError(IPC_SRV_SEND_FAF_ERROR_CLI_NOT_FOUND
                                                .format(identifier, endpoint, data)) + e

        except SocketServerSendError as e:
            raise e.add_ctx(IPC_SRV_SEND_FAF_ERROR.format(identifier, endpoint, data))

    # blocking request
    def send_blocking_request(self, identifier: str, endpoint: str, data: dict):
        """
        Send data through a blocking request to a client.
        This method will block until the server send the response.
        Warning, if the server doesn't send the response, this method will block forever.
        Be sure to add the endpoint on the client side with a correct response.
        :param identifier: identifier of the client.
        :param endpoint: endpoint as a str, this endpoint must be added.
        :param data: data to send as a dict.

        :raise ClientIdentifierNotFound: If the client is not found. This can happen if the client is not connected
        or is the identifier is wrong.
        :raise SocketServerSendError: If the server fails to send the data, you can access the initial
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
            self.send_data(identifier, {"rtype": BLOCKING, "endpoint": endpoint, "data": data, "rid": rid})
            self.__trigger__(CoreEvent.IPC_BLOCKING_REQUEST_SENT,
                             event_ctx=IPC_SRV_SEND_BLOCK_CTX.format(identifier, endpoint, data),
                             identifier=identifier, data=data)
        except SocketServerClientNotFound as e:
            raise ClientIdentifierNotFoundError(IPC_SRV_SEND_BLOCK_ERROR_CLI_NOT_FOUND
                                            .format(identifier, endpoint, data)) + e
        except SocketServerSendError as e:
            raise e.add_ctx(IPC_SRV_SEND_BLOCK_ERROR.format(identifier, endpoint, data))
        # Wait for the response
        semaphore.acquire()
        # Return the response
        resp = self.blocking_requests[rid][1]
        del self.blocking_requests[rid]
        return resp

    # responses
    def send_response(self, identifier: str, endpoint: str, data: dict, rid: str):
        """
        Send response to a blocking request to a client.
        This method will directly return after sending the response.
        :param identifier: identifier of the client.
        :param endpoint: endpoint as a str.
        :param data: data to send as a dict.
        :param rid: request id as a str, this id must be the same as the one received in the initial blocking request.

        :raise ClientIdentifierNotFound: If the client is not found. This can happen if the client is not connected
        or is the identifier is wrong.
        :raise SocketServerSendError: If the server fails to send the data, you can access the initial
        exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised exception.
        """
        try:
            self.send_data(identifier, {"rtype": RESPONSE, "endpoint": endpoint, "data": data, "rid": rid})
        except SocketServerClientNotFound as e:
            raise ClientIdentifierNotFoundError(IPC_SRV_SEND_RESPONSE_ERROR_CLI_NOT_FOUND
                                              .format(identifier, endpoint, rid, data)) + e
        except SocketServerSendError as e:
            raise e.add_ctx(IPC_SRV_SEND_RESPONSE_ERROR.format(identifier, endpoint, rid, data))
        self.__trigger__(CoreEvent.IPC_RESPONSE_SENT,
                         event_ctx=IPC_SRV_SEND_RESPONSE_CTX.format(identifier, endpoint, rid, data),
                         identifier=identifier, data=data)
