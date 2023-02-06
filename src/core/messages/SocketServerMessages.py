SOCKET_SRV_ERROR = "SocketServer.__init__: Error while binding the socket server to {}:{}, "\
                    "look at the initial exception for more details."
SOCKET_SRV_TRACE = "SocketServer.__init__: Socket server successfully bound to {}:{}."

SOCKET_SRV_ACCEPT_TRACE_LISTENING = "SocketServer.accept_new_connections: Socket server is listening on {}:{}."
SOCKET_SRV_ACCEPT_TRACE_DETECTED = "SocketServer.accept_new_connections: A new client has been detected on {}."
SOCKET_SRV_ACCEPT_TRACE_VALIDATED = "SocketServer.accept_new_connections: The client '{}' creds has been validated."
SOCKET_SRV_ACCEPT_CTX_VALIDATED = "SocketServer.accept_new_connections: The client '{}' has been accepted."
SOCKET_SRV_ACCEPT_TRACE_INVALID = "SocketServer.accept_new_connections: The client '{}' creds has not been validated, "\
                                "the client will be disconnected."
SOCKET_SRV_ACCEPT_CTX_INVALID = "SocketServer.accept_new_connections: The client '{}' has been disconnected."
SOCKET_SRV_ACCEPT_TRACE_STOPPED = "SocketServer.accept_new_connections: The socket server has stopped accepting new "\
                                    "connections."
SOCKET_SRV_ACCEPT_WARNING = "SocketServer.accept_new_connections: Non critical error was detected while accepting a "\
                            "new client, look at the initial exception for more details."

SOCKET_SRV_LISTEN_TRACE_FLUSHING = "SocketServer.listen_for_connection: Flushing the buffer for client '{}'."\
                                    "\n Buffer: '{}'"
SOCKET_SRV_LISTEN_CTX_RECEIVED = "SocketServer.listen_for_connection: Received message from client '{}': '{}'"
SOCKET_SRV_LISTEN_ERROR_CLI_NOT_FOUND = "SocketServer.listen_for_connection: This method was call to listen the "\
                                        "connection of a client but this client is not connected or the identifier "\
                                        "'{}', is wrong."
SOCKET_SRV_LISTEN_TRACE_RECEIVED_DATA = "SocketServer.listen_for_connection: Received data from client '{}': '{}'"
SOCKET_SRV_LISTEN_WARNING_JSON_DECODE = "SocketServer.listen_for_connection: The data received from client '{}' is "\
                                        "not a valid JSON, the data will be ignored.\nBuffer: '{}'"
SOCKET_SRV_LISTEN_WARNING = "SocketServer.listen_for_connection: Non critical error was detected while listening the "\
                            "connection of client '{}', look at the initial exception for more details."
SOCKET_SRV_LISTEN_TRACE_CLOSED = "SocketServer.listen_for_connection: The connection of client '{}' has been closed " \
                                "by the {}."

SOCKET_SRV_SEND_ERROR_CLI_NOT_FOUND = "SocketServer.send: This method was call to send a message to a client but this "\
                                    "client is not connected or the identifier '{}', is wrong."
SOCKET_SRV_SEND_TRACE = "SocketServer.send: Data sent to client '{}': '{}'"
SOCKET_SRV_SEND_ERROR = "SocketServer.send: Error while sending data to client '{}', look at the initial exception for"\
                        " more details.\nData: '{}'"

SOCKET_SRV_CLOSE_ERROR = "SocketServer.close: Error while closing the socket server, look at the initial exception "\
                        "for more details."
SOCKET_SRV_CLOSE_TRACE = "SocketServer.close: Socket server successfully closed."
