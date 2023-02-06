"""
This module implements an IPC custom protocol using sockets.
"""
import select
import threading
from json import JSONDecodeError

from src.core.Exceptions import *
from src.core.Logger import LOGGER, CORE
from src.core.messages.SocketServerMessages import *
from src.core.event import EventHandler, CoreEvent
from src.core.Utils import nonblocking, EOT, IGNORE
import socket
import json
import time


class SocketServer:
    """
    Implementation of a custom socket server used for IPC (Inter Process Communication).
    """

    # Constructor
    def __init__(self, auth_key: str, host: str = "localhost", port: int = 6969,
                 artificial_latency: float = 0.1, event_handler: EventHandler = None):
        """
        Instance a socket server used for inter process communication (IPC).
        :param auth_key: The key clients will use to authenticate themselves.
        :param port (optional): The port to listen on. Default is 6969.
        :param host (optional): The host to listen on. Default is localhost.
        :param artificial_latency (optional): Time in s between each .recv call for a connection. Default is 0.1s.
        This is used to prevent the CPU from being overloaded. Change this value if you know what you're doing.
        :param event_handler (optional): The event handler to use. If None, a new one will be created.

        :raise SocketServerBindError: If the socket cannot be bound to the specified host and port.
        """
        # Args
        self.auth_key = auth_key
        self.host = host
        self.port = port
        self.artificial_latency = artificial_latency

        # Events
        self.event_handler = event_handler if event_handler else EventHandler()
        # adding events
        self.event_handler.new_event(CoreEvent.SOCKET_CONNECTION_ACCEPTED)
        self.event_handler.new_event(CoreEvent.SOCKET_CONNECTION_REFUSED)
        self.event_handler.new_event(CoreEvent.SOCKET_CONNECTION_CLOSED)
        self.event_handler.new_event(CoreEvent.SOCKET_SERVER_CLOSED)
        self.event_handler.new_event(CoreEvent.SOCKET_MESSAGE_RECEIVED)
        self.event_handler.new_event(CoreEvent.SOCKET_MESSAGE_SENT)
        # Base connection accepted callback
        self.event_handler.subscribe(CoreEvent.SOCKET_CONNECTION_ACCEPTED,
                                     lambda identifier: threading.Thread(target=self.listen_for_connection,
                                                                         args=(identifier,),
                                                                         name=f"SERVER_CONNECTION_LISTENER_"
                                                                              f"{identifier}").start())
        # Alias
        self.__trigger__ = self.event_handler.trigger

        # Socket
        self.connections = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(0.2)
        try:
            self.socket.bind((self.host, self.port))
        except Exception as e:
            raise SocketServerBindError(SOCKET_SRV_ERROR.format(host, port)) + e
        self.socket.listen()

        # To close the IPC server
        self.ipc_server_closed = False
        # To stop accepting new connections, for optimization purposes
        self.accepting_new_connections = True

        LOGGER.trace(SOCKET_SRV_TRACE.format(host, port), CORE)

    # accept new connections from clients until self.accepting_new_connections is set to False
    @nonblocking("ipc_server_new_connection_listener")
    def accept_new_connections(self):
        """
        This method launches a new thread that will let the server accept new connections.
        """

        self.accepting_new_connections = True  # Assume we really want to accept new connections
        LOGGER.trace(SOCKET_SRV_ACCEPT_TRACE_LISTENING.format(self.host, self.port), CORE)
        while self.accepting_new_connections:
            try:
                # Accept connection
                connection, address = self.socket.accept()
                LOGGER.trace(SOCKET_SRV_ACCEPT_TRACE_DETECTED.format(address), CORE)

                # Authentication
                authentication_payload = connection.recv(1024)  # We assume that the payload is less than 1024 bytes
                authentication_payload = json.loads(authentication_payload.decode("utf-8"))

                # Check if the key is correct
                if authentication_payload["key"] == self.auth_key:
                    # Validate a new connection
                    LOGGER.trace(SOCKET_SRV_ACCEPT_TRACE_VALIDATED.format(authentication_payload['identifier']), CORE)
                    connection.sendall(json.dumps({"status": "valid"}).encode("utf-8"))
                    self.connections[authentication_payload["identifier"]] = connection
                    self.__trigger__(CoreEvent.SOCKET_CONNECTION_ACCEPTED,
                                     event_ctx=SOCKET_SRV_ACCEPT_CTX_VALIDATED.format(
                                         authentication_payload['identifier']),
                                     identifier=authentication_payload["identifier"])
                else:
                    # Invalid creds
                    LOGGER.trace(SOCKET_SRV_ACCEPT_TRACE_INVALID.format(authentication_payload["identifier"]), CORE)
                    connection.sendall(json.dumps({"status": "invalid"}).encode("utf-8"))
                    connection.close()
                    self.__trigger__(CoreEvent.SOCKET_CONNECTION_REFUSED,
                                     event_ctx=SOCKET_SRV_ACCEPT_CTX_INVALID.format(
                                         authentication_payload["identifier"]),
                                     identifier=authentication_payload["identifier"])
            except socket.timeout or OSError:
                # Expected exception, just ignore it
                pass
            except OSError:
                if not self.accepting_new_connections:
                    LOGGER.trace(SOCKET_SRV_ACCEPT_TRACE_STOPPED, CORE)
            except Exception as e:
                LOGGER.warning_exception(SocketServerAcceptError(SOCKET_SRV_ACCEPT_WARNING), e, CORE)

    # Blocking call, handle requests from a specific connection
    def listen_for_connection(self, identifier: str):
        """
        Listens for a client connection and triggers the on_message_received event when a message is received.
        This method is blocking and called automatically when a new connection is accepted.
        :param identifier: The identifier of the connection (client) to listen for.
        """

        def flush_buffer():
            nonlocal buffer
            buffer.replace("PING_TEST_TO_BE_IGNORED".encode("utf-8"), "".encode("utf-8"))
            LOGGER.trace(SOCKET_SRV_LISTEN_TRACE_FLUSHING.format(identifier, buffer), CORE)
            if buffer != IGNORE:
                self.__trigger__(CoreEvent.SOCKET_MESSAGE_RECEIVED,
                                 event_ctx=SOCKET_SRV_LISTEN_CTX_RECEIVED.format(identifier, buffer),
                                 identifier=identifier,
                                 data=json.loads(buffer.decode("utf-8")))
            buffer = b''

        # Pre test
        if identifier not in self.connections:
            e = SocketServerClientNotFound(SOCKET_SRV_LISTEN_ERROR_CLI_NOT_FOUND.format(identifier))
            LOGGER.error_exception(e, CORE)
            return

        connection = self.connections[identifier]
        connection_closed = False

        # Listening for multiple requests
        while not connection_closed and not self.ipc_server_closed:
            # Buffering one request
            buffer = b''
            while not connection_closed and not self.ipc_server_closed:
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
                        # Check if the client closed the connection
                        if not data:
                            connection_closed = True
                            break

                        LOGGER.trace(
                            SOCKET_SRV_LISTEN_TRACE_RECEIVED_DATA.format(identifier, data.decode("utf-8")),
                            CORE)

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
                except JSONDecodeError:
                    LOGGER.warning(SOCKET_SRV_LISTEN_WARNING_JSON_DECODE.format(identifier, buffer.decode("utf-8")),
                                CORE)
                except socket.timeout or OSError:
                    connection_closed = True
                    break
                except Exception as e:
                    LOGGER.warning_exception(SocketServerListeningConnectionError(
                        SOCKET_SRV_LISTEN_WARNING.format(identifier)) + e, CORE)

            time.sleep(self.artificial_latency)  # Artificial latency for optimization purposes

        if connection_closed:
            LOGGER.trace(SOCKET_SRV_LISTEN_TRACE_CLOSED.format(identifier, "client"), CORE)
            try:
                connection.close()
            except OSError:
                pass
            try:
                self.connections.pop(identifier)
            except KeyError:
                pass
            self.__trigger__(CoreEvent.SOCKET_CONNECTION_CLOSED,
                             event_ctx=SOCKET_SRV_LISTEN_TRACE_CLOSED.format(identifier, "client"),
                             identifier=identifier, from_server=False)
        else:
            LOGGER.trace(SOCKET_SRV_LISTEN_TRACE_CLOSED.format(identifier, "server"), CORE)
            try:
                connection.close()
            except OSError:
                pass
            try:
                self.connections.pop(identifier)
            except KeyError:
                pass
            self.__trigger__(CoreEvent.SOCKET_CONNECTION_CLOSED,
                             event_ctx=SOCKET_SRV_LISTEN_TRACE_CLOSED.format(identifier, "server"),
                             identifier=identifier, from_server=True)

    # Non blocking call, send given data to a specific connection
    def send_data(self, identifier: str, data: dict):
        """
        Sends data to a connection (client).
        :param identifier: The identifier of the connection (client) to send data to.
        :param data: The data to send as a dict.

        :raises SocketServerClientNotFound: If the connection (client) is not found, if the client is not
        connected or the identifier is wrong.
        :raises SocketServerSendError: If an error occurred while sending data to the client, you can access the initial
        exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised exception.
        """

        # Pre test
        if identifier not in self.connections:
            raise SocketServerClientNotFound(SOCKET_SRV_SEND_ERROR_CLI_NOT_FOUND.format(identifier))

        connection = self.connections[identifier]
        try:
            connection.sendall(json.dumps(data).encode("utf-8") + bytes([int(EOT, 16)]))
            LOGGER.trace(SOCKET_SRV_SEND_TRACE.format(identifier, data), CORE)
            self.__trigger__(CoreEvent.SOCKET_MESSAGE_SENT,
                             event_ctx=SOCKET_SRV_SEND_TRACE.format(identifier, data),
                             identifier=identifier, data=data)
        except Exception as e:
            raise SocketServerSendError(SOCKET_SRV_SEND_ERROR.format(identifier, data)) + e

    # Close the server
    def close(self):
        """
        Closes the socket server.
        :raises SocketServerCloseError: If an error occurred while closing the server, you can access the initial
        exception type and msg by accessing 'initial_type' and 'initial_msg' attributes of the raised exception.
        """
        self.accepting_new_connections = False
        self.ipc_server_closed = True
        try:
            self.socket.close()
        except Exception as e:
            raise SocketServerCloseError(SOCKET_SRV_CLOSE_ERROR) + e
        LOGGER.trace(SOCKET_SRV_CLOSE_TRACE, CORE)
        self.__trigger__(CoreEvent.SOCKET_SERVER_CLOSED,
                         event_ctx=SOCKET_SRV_CLOSE_TRACE)
