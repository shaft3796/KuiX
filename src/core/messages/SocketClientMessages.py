SOCKET_CLI_INIT_TRACE = "SocketClient<'{}'>.__init__: Socket client successfully initialized and ready to connect to "\
                        "the server."

SOCKET_CLI_CONNECT_TRACE_CONNECTED = "SocketClient<'{}'>.connect: Socket client successfully connected to the server, "\
                                "sending the auth request."
SOCKET_CLI_CONNECT_TRACE_VALIDATED = "SocketClient<'{}'>.connect: The server has validated the client, the client is "\
                                    "now connected."
SOCKET_CLI_CONNECT_TRACE_INVALID = "SocketClient<'{}'>.connect: The server has not validated the client, the client "\
                                    "will be disconnected."
SOCKET_CLI_CONNECT_ERROR = "SocketClient<'{}'>.connect: Error while connecting to the server, look at the initial "\
                            "exception for more details."

SOCKET_CLI_LISTEN_TRACE_FLUSHING = "SocketClient<'{}'>.listen: Flushing the buffer."\
                                    "\nBuffer: '{}'"
SOCKET_CLI_LISTEN_TRACE_RECEIVED_DATA = "SocketClient<'{}'>.listen: Received data from the server: '{}'"
SOCKET_CLI_LISTEN_WARNING_JSON_DECODE = "SocketClient<'{}'>.listen: The data received from the server is not a valid "\
                                        "JSON, the data will be ignored.\nBuffer: '{}'"
SOCKET_CLI_LISTEN_WARNING = "SocketClient<'{}'>.listen: Non critical error was detected while listening the server, "\
                            "look at the initial exception for more details."
SOCKET_CLI_LISTEN_TRACE_CLOSED = "SocketClient<'{}'>.listen: The connection with the server has been closed by the {}."

SOCKET_CLI_SEND_TRACE = "SocketClient<'{}'>.send: Data sent to the server: '{}'"
SOCKET_CLI_SEND_ERROR = "SocketClient<'{}'>.send: Error while sending data to the server, look at the initial "\
                        "exception for more details.\nData: '{}'"

SOCKET_CLI_CLOSE_ERROR = "SocketClient<'{}'>.close: Error while closing the socket client, look at the initial "\
                        "exception for more details."
SOCKET_CLI_CLOSE_TRACE = "SocketClient<'{}'>.close: Socket client successfully closed."
