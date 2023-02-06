"""
This module implements an IPC custom protocol using sockets.
"""
import select
import threading
from json import JSONDecodeError

from src.core.Exceptions import *
from src.core.Logger import LOGGER, KX_PROCESS
from src.core.messages.SocketClientMessages import *
from src.core.event import EventHandler, ProcessEvent
from src.core.Utils import EOT, IGNORE
import socket
import json
import time


class SocketClient:
    """
    Implementation of a custom socket client used for IPC (Inter Process Communication).
    """

    # Constructor
    def __init__(self, _identifier: str, auth_key: str, host: str = "localhost", port: int = 6969,
                 artificial_latency: float = 0.1, event_handler: EventHandler = None):
        """
        Instance a socket client used for inter process communication (IPC).
        :param _identifier: The identifier of the client.
        :param auth_key: The key to authenticate the client.
        :param port (optional): The port to connect on. Default is 6969.
        :param host (optional): The host to connect  on. Default is localhost.
        :param artificial_latency (optional): Time in s between each .recv call for a connection. Default is 0.1s.
        This is used to prevent the CPU from being overloaded. Change this value if you know what you're doing.
        :param event_handler (optional): The event handler to use. Default is None.
        """
        # Args
        self.identifier = _identifier
        self.auth_key = auth_key
        self.host = host
        self.port = port
        self.artificial_latency = artificial_latency

        # Events
        self.event_handler = event_handler if event_handler else EventHandler()
        # adding events
        self.event_handler.new_event(ProcessEvent.SOCKET_CONNECTION_ACCEPTED)
        self.event_handler.new_event(ProcessEvent.SOCKET_CONNECTION_REFUSED)
        self.event_handler.new_event(ProcessEvent.SOCKET_CONNECTION_CLOSED)
        self.event_handler.new_event(ProcessEvent.SOCKET_CLIENT_CLOSED)
        self.event_handler.new_event(ProcessEvent.SOCKET_MESSAGE_RECEIVED)
        self.event_handler.new_event(ProcessEvent.SOCKET_MESSAGE_SENT)
        # Base connection accepted callback
        self.event_handler.subscribe(ProcessEvent.SOCKET_CONNECTION_ACCEPTED, lambda identifier:
                                    threading.Thread(target=self.listen_for_connection,
                                    name=identifier).start())

        # Alias
        self.__trigger__ = self.event_handler.trigger

        # Socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(5)

        # To close the IPC client
        self.ipc_client_closed = False

        LOGGER.trace(SOCKET_CLI_INIT_TRACE.format(self.identifier), KX_PROCESS)

    # --- Low level methods ---

    # Connect to the server
    def connect(self):
        """
        Connects the client to the server.

        :raises SocketClientConnectionError: If the client failed to connect to the server, you can access the initial
        exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised exception.
        """
        try:
            # Accept connection
            self.socket.connect((self.host, self.port))
            LOGGER.trace(SOCKET_CLI_CONNECT_TRACE_CONNECTED.format(self.identifier), KX_PROCESS)

            # Authentication
            authentication_payload = {"identifier": self.identifier, "key": self.auth_key}
            self.socket.sendall(json.dumps(authentication_payload).encode("utf-8"))

            # Wait for response
            data = json.loads(self.socket.recv(1024).decode("utf-8"))

            if data["status"] == "valid":
                # Connection validated
                LOGGER.trace(SOCKET_CLI_CONNECT_TRACE_VALIDATED.format(self.identifier), KX_PROCESS)
                self.__trigger__(ProcessEvent.SOCKET_CONNECTION_ACCEPTED,
                                 event_ctx=SOCKET_CLI_CONNECT_TRACE_VALIDATED.format(self.identifier),
                                 identifier=authentication_payload["identifier"])
            else:
                LOGGER.trace(SOCKET_CLI_CONNECT_TRACE_INVALID, KX_PROCESS)
                self.__trigger__(ProcessEvent.SOCKET_CONNECTION_REFUSED.format(self.identifier),
                                 event_ctx=ProcessEvent.SOCKET_CONNECTION_REFUSED.format(self.identifier),
                                 identifier=authentication_payload["identifier"])
        except Exception as e:
            raise SocketClientConnectionError(SOCKET_CLI_CONNECT_ERROR.format(self.identifier)) + e

    # Blocking call, handle requests from the server
    def listen_for_connection(self):
        """
        Listens the server connection, trigger the on_message_received event when a message is received.
        This method is blocking and called automatically when the connection is accepted by the server.
        """

        def flush_buffer():
            nonlocal buffer
            buffer.replace("PING_TEST_TO_BE_IGNORED".encode("utf-8"), "".encode("utf-8"))
            LOGGER.trace(SOCKET_CLI_LISTEN_TRACE_FLUSHING.format(self.identifier, buffer), KX_PROCESS)
            # Check if the request is a ping from the server
            if buffer != IGNORE:
                self.__trigger__(ProcessEvent.SOCKET_MESSAGE_RECEIVED,
                                 event_ctx=SOCKET_CLI_LISTEN_TRACE_FLUSHING.format(self.identifier, buffer),
                                 identifier=self.identifier,
                                 data=json.loads(buffer.decode("utf-8")))
            buffer = b''

        connection = self.socket
        connection_closed = False

        # Listening for multiple requests
        while not connection_closed and not self.ipc_client_closed:
            # Buffering one request
            buffer = b''
            while not connection_closed and not self.ipc_client_closed:
                try:
                    # Receive data
                    ready_to_read, _, _ = select.select([connection], [], [], 1)
                    if ready_to_read:
                        data = connection.recv(1024)
                        if data == IGNORE:
                            continue
                        # Sometimes when closing KuiX, a request can being merged with ping test,
                        # so we remove all artifacts
                        data.replace("PING_TEST_TO_BE_IGNORED".encode("utf-8"), "".encode("utf-8"))
                        # Check if the server closed the connection
                        if not data:
                            connection_closed = True
                            break

                        LOGGER.trace(
                            SOCKET_CLI_LISTEN_TRACE_RECEIVED_DATA.format(self.identifier, data.decode("utf-8")),
                            KX_PROCESS)

                        # Buffering data
                        for byte in data:
                            if byte == int(EOT, 16):
                                flush_buffer()
                                break
                            else:
                                buffer += bytes([byte])

                    else:
                        try:
                            connection.send(IGNORE)
                        except socket.error:
                            connection_closed = True
                            break
                except OSError or socket.timeout:
                    connection_closed = True
                    break
                except JSONDecodeError:
                    LOGGER.warning(SOCKET_CLI_LISTEN_TRACE_RECEIVED_DATA.format(self.identifier,
                                                                                buffer.decode('utf-8')), KX_PROCESS)
                except Exception as e:
                    LOGGER.warning_exception(SocketClientListeningError(
                        SOCKET_CLI_LISTEN_WARNING.format(self.identifier)) + e, KX_PROCESS)

            time.sleep(self.artificial_latency)  # Artificial latency for optimization purposes

        if connection_closed:
            LOGGER.trace(SOCKET_CLI_LISTEN_TRACE_CLOSED.format(self.identifier, "server"), KX_PROCESS)
            connection.close()
            self.__trigger__(ProcessEvent.SOCKET_CONNECTION_CLOSED,
                             event_ctx=SOCKET_CLI_LISTEN_TRACE_CLOSED.format(self.identifier, "server"),
                             identifier=self.identifier, from_client=False)
        else:
            LOGGER.info(SOCKET_CLI_LISTEN_TRACE_CLOSED.format(self.identifier, "client"), KX_PROCESS)
            connection.close()
            self.__trigger__(ProcessEvent.SOCKET_CONNECTION_CLOSED,
                             event_ctx=SOCKET_CLI_LISTEN_TRACE_CLOSED.format(self.identifier, "client"),
                             identifier=self.identifier, from_client=True)

    # Non blocking call, send given data to a specific connection
    def send_data(self, data: dict):
        """
        Sends data to the server.
        :param data: The data to send as a dict.

        :raises SocketClientSendError: If an error occurred while sending data to the server, you can access the initial
        exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised exception.
        """
        connection = self.socket
        try:
            connection.sendall(json.dumps(data).encode("utf-8") + bytes([int(EOT, 16)]))
            LOGGER.trace(SOCKET_CLI_SEND_TRACE.format(self.identifier, data), KX_PROCESS)
            self.__trigger__(ProcessEvent.SOCKET_MESSAGE_SENT,
                             event_ctx=SOCKET_CLI_SEND_TRACE.format(self.identifier, data),
                             identifier=self.identifier, data=data)
        except Exception as e:
            raise SocketClientSendError(SOCKET_CLI_SEND_ERROR.format(self.identifier, data)) + e

    # Close the server
    def close(self):
        """
        Closes the socket client.
        """
        self.ipc_client_closed = True
        try:
            self.socket.close()
        except Exception as e:
            raise SocketClientCloseError(SOCKET_CLI_CLOSE_ERROR.format(self.identifier)) + e

        LOGGER.trace(SOCKET_CLI_CLOSE_TRACE.format(self.identifier), KX_PROCESS)
        self.__trigger__(ProcessEvent.SOCKET_CLIENT_CLOSED,
                         event_ctx=SOCKET_CLI_CLOSE_TRACE.format(self.identifier),
                         identifier=self.identifier)
