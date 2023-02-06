IPC_SRV_INIT_ERROR = "IPCServer.__init__: Error while initializing the IPC server, look at the initial exception for "\
                    "more details."

IPC_SRV_HANDLE_TRACE_RECEIVED_FAF = "IPCServer.handle_request: The server received a fire and forget request from "\
                                    "client '{}': '{}'"
IPC_SRV_HANDLE_ERROR_FAF_ENDPOINT_NOT_FOUND = "IPCServer.handle_request: The server received a fire and forget "\
                                            "request from client '{}' to the endpoint '{}' but this endpoint is not "\
                                            "added to the server."
IPC_SRV_HANDLE_TRACE_HANDLED_FAF = "IPCServer.handle_request: The server handled a fire and forget request from "\
                                    "client '{}' to the endpoint '{}'."

IPC_SRV_HANDLE_TRACE_RECEIVED_BLOCK = "IPCServer.handle_request: The server received a blocking request from client "\
                                    "'{}': '{}'"
IPC_SRV_HANDLE_ERROR_BLOCK_ENDPOINT_NOT_FOUND = "IPCServer.handle_request: The server received a blocking request from"\
                                                " client '{}' to the endpoint '{}' but this endpoint is not added to "\
                                                "the server.\nCRITICAL WARNING, this error should never happen and "\
                                                "will result to an infinite function call on the client side."
IPC_SRV_HANDLE_TRACE_HANDLED_BLOCK = "IPCServer.handle_request: The server handled a blocking request from client "\
                                    "'{}' to the endpoint '{}'."

IPC_SRV_HANDLE_TRACE_RECEIVED_RESPONSE = "IPCServer.handle_request: The server received a response from client '{}': "\
                                        "'{}'"
IPC_SRV_HANDLE_ERROR_RESPONSE_RID_NOT_FOUND = "IPCServer.handle_request: The server received a response from "\
                                            "client '{}' with the request id '{}' but this request id is not found."\
                                            "\nCRITICAL WARNING, this error should never happen and will result to "\
                                            "an infinite function call on the server side"
IPC_SRV_HANDLE_TRACE_HANDLED_RESPONSE = "IPCServer.handle_request: The server handled a response from client '{}' with"\
                                        " the request id '{}'."

IPC_SRV_HANDLE_ERROR_UNKNOWN_REQUEST_TYPE = "IPCServer.handle_request: The server received an unknown request type "\
                                            "from client '{}': '{}', only 'FIRE_AND_FORGET', 'BLOCKING' and 'RESPONSE'"\
                                            " are allowed."
IPC_SRV_HANDLE_ERROR_MALFORMED_REQUEST = "IPCServer.handle_request: The server received a malformed request from "\
                                        "client '{}': '{}', the request must be a valid JSON with all required fields."
IPC_SRV_HANDLE_ERROR = "IPCServer.handle_request: Non critical error was detected while handling a request from "\
                        "client '{}', look at the initial exception for more details.\n Request: '{}'"

IPC_SRV_SEND_FAF_ERROR_CLI_NOT_FOUND = "IPCServer.send_fire_and_forget: This method was call to send a fire and forget"\
                                    " request to a client but this client is not connected or the identifier '{}', is "\
                                    "wrong.\nEndpoint: '{}'\nData: '{}'"
IPC_SRV_SEND_FAF_ERROR = "IPCServer.send_fire_and_forget: Error while sending a fire and forget request to client '{}'"\
                        ", look at the initial exception for more details.\nEndpoint: '{}'\nData: '{}'"
IPC_SRV_SEND_FAF_CTX = "IPCServer.send_fire_and_forget: Fire and forget request sent to client '{}':\nEndpoint: "\
                        "'{}'\nData: '{}'"

IPC_SRV_SEND_BLOCK_ERROR_CLI_NOT_FOUND = "IPCServer.send_blocking: This method was call to send a blocking request to "\
                                        "a client but this client is not connected or the identifier '{}', is wrong."\
                                        "\nEndpoint: '{}'\nData: '{}'"
IPC_SRV_SEND_BLOCK_ERROR = "IPCServer.send_blocking: Error while sending a blocking request to client '{}', look at "\
                            "the initial exception for more details.\nEndpoint: '{}'\nData: '{}'"
IPC_SRV_SEND_BLOCK_CTX = "IPCServer.send_blocking: Blocking request sent to client '{}':\nEndpoint: '{}'\nData: "\
                        "'{}'"

IPC_SRV_SEND_RESPONSE_ERROR_CLI_NOT_FOUND = "IPCServer.send_response: This method was call to send a response to a "\
                                            "client but this client is not connected or the identifier '{}', is wrong."\
                                            "\nEndpoint: '{}'\nRequest id: '{}'\nData: '{}'"
IPC_SRV_SEND_RESPONSE_ERROR = "IPCServer.send_response: Error while sending a response to client '{}', look at the "\
                                "initial exception for more details.\nEndpoint: '{}'\nRequest id: '{}'\nData: '{}'"
IPC_SRV_SEND_RESPONSE_CTX = "IPCServer.send_response: Response sent to client '{}':\nEndpoint: '{}'\nRequest id: "\
                            "'{}'\nData: '{}'"



