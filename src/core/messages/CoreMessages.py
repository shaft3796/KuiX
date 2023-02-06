SETUP_FILES_ERROR = "core.__setup_files__: Error while setting up files, look at the initial exception for more details"
SETUP_FILES_TRACE = "core.__setup_files__: Files setup successfully"

CORE_NOT_CONFIGURED_ERROR = "core.{}: Core is not configured, please configure it using 'core.configure()' or "\
                            "'core.load_json_config()' before calling this method."
CORE_ALREADY_CONFIGURED_ERROR = "core.{}: Core is already configured, please restart KuiX before configuring the core "\
                            "again."
CORE_NOT_STARTED_ERROR = "core.{}: Core is not started, please start it using 'core.start()' before calling this "\
                    "method."
CORE_ALREADY_STARTED_ERROR = "core.{}: Core is already started, please stop it using 'core.stop()' before starting it "\
                    "again."

CORE_INIT_ERROR = "core.__init__: Error while initializing the core, look at the initial exception for more details."
CORE_INIT_TRACE = "core.__init__: Core initialized successfully."

CORE_CONFIGURE_ERROR = "core.configure: Error while configuring the core, look at the initial exception for more "\
                        "details."
CORE_CONFIGURE_ERROR_BUILTIN = "core.configure: Error while configuring the core, an error occurred while loading "\
                                "built-in types, look at the initial exception for more details. "\
                                "If the error persists try to reinstall KuiX."
CORE_CONFIGURE_TRACE = "core.configure: Core configured successfully."

CORE_JSON_CONFIG_ERROR = "core.load_json_config: Error while loading the JSON configuration, look at the initial "\
                            "exception for more details."

CORE_GENERATE_CONFIG_ERROR = "core.generate_json_config: Error while generating the JSON configuration, look at the "\
                                "initial exception for more details."

CORE_START_TRACE = "core.start: Core started successfully."

CORE_CLOSE_ERROR = "core.close: Error while closing the core, look at the initial exception for more details."
CORE_CLOSE_INFO = "core.close: Core closed successfully."

CORE_ADD_COMPONENT_WARNING = "core.add_component: Component '{}' already exists, it will be replaced by the new one "\
                                "but this can be an unexpected behaviour."

CORE_ADD_ENDPOINT_WARNING = "core.add_endpoint: Endpoint '{}' already exists, it will be replaced by the new one but "\
                            "this can be an unexpected behaviour."

CORE_ADD_BLOCKING_ENDPOINT_WARNING = "core.add_blocking_endpoint: Blocking endpoint '{}' already exists, it will be "\
                                    "replaced by the new one but this can be an unexpected behaviour."

CORE_SEND_ERROR = "core.send: Error while sending data to the endpoint '{}' and to process '{}', look at the initial "\
                    "exception for more details."

CORE_SEND_BLOCKING_ERROR = "core.send_blocking: Error while sending data to the blocking endpoint '{}' and to process "\
                            "'{}', look at the initial exception for more details."

CORE_SEND_RESPONSE_ERROR = "core.send_response: Error while sending response to the endpoint '{}' and to process '{}',"\
                            " look at the initial exception for more details."

CORE_CREATE_PROCESS_ERROR = "core.create_process: Error while creating the process '{}', a process with the same name "\
                            "already exists."

CORE_CREATE_PROCESS_AND_WAIT_ERROR_TIMEOUT = "core.create_process_and_wait: Error while launching the process '{}' "\
                                                "the process timeout, check the logs for more details."
CORE_CREATE_PROCESS_AND_WAIT_ERROR_PUSH = "core.create_process_and_wait: Error while pushing strategies to process " \
                                            "'{}', look at the exception for mor details, WARNING the process has " \
                                            "started !"

CORE_CLOSE_PROCESS_ERROR_NOT_FOUND = "core.close_process: Error while closing the process '{}', the process is not "\
                                    "found, if you haven't launched it yet please launch it using "\
                                    "'core.create_process_and_wait()' before closing it. The process can also be "\
                                    "disconnected, please check the logs for more details."
CORE_CLOSE_PROCESS_ERROR = "core.close_process: Error while closing the process '{}', look at the initial exception "\
                            "for more details."

CORE_ADD_STRATEGY_WARNING = "core.add_strategy: Strategy '{}' already exists, it will be replaced by the new one but "\
                            "this can be an unexpected behaviour."


PUSH_STRATEGY_ERROR_NOT_ADDED = "core.push_strategy: Error while pushing the strategy '{}', the strategy is not "\
                                "added to the core, please add it using 'core.add_strategy()' before pushing it."
PUSH_STRATEGY_ERROR_PROCESS_NOT_FOUND = "core.push_strategy: Error while pushing the strategy '{}', the process '{}' "\
                                        "is not found, if you haven't launched it yet please launch it using "\
                                        "'core.create_process_and_wait()' before pushing the strategy. "\
                                        "The process can also be disconnected, please check the logs for more details."
PUSH_STRATEGY_ERROR = "core.push_strategy: Error while pushing the strategy '{}' to the process '{}', look at the "\
                        "initial exception for more details."

PUSH_STRATEGY_TO_ALL_ERROR = "core.push_strategy_to_all: Error while pushing the strategy '{}' to all processes, look "\
                                "at the initial exception for more details."

PUSH_ALL_STRATEGIES_ERROR = "core.push_all_strategies: Error while pushing all strategies to the process '{}', look at"\
                            " the initial exception for more details."

PUSH_ALL_STRATEGIES_TO_ALL_ERROR = "core.push_all_strategies_to_all: Error while pushing all strategies to process "\
                                    "'{}', look at the initial exception for more details."

CORE_CREATE_WORKER_ERROR_PROCESS_NOT_FOUND = "core.create_worker: Error while creating the worker, the process '{}' "\
                                            "is not found, if you haven't launched it yet please launch it using "\
                                            "'core.create_process_and_wait()' before creating the worker. "\
                                            "The process can also be disconnected, please check the logs for more " \
                                            "details."
CORE_CREATE_WORKER_ERROR_STRATEGY_NOT_ADDED = "core.create_worker: Error while creating the worker, the strategy '{}' "\
                                            "is not added to the core, please add it using 'core.add_strategy()' " \
                                            "before creating the worker."
CORE_CREATE_WORKER_ERROR_WORKER_ALREADY_CREATED = "core.create_worker: Error while creating the worker, a worker for "\
                                                "the strategy '{}' and the process '{}' already exists with the name " \
                                                "'{}'."
CORE_CREATE_WORKER_ERROR = "core.create_worker: Error while creating the worker '{}' for the strategy '{}' and the " \
                            "process '{}', look at the initial exception for more details."

CORE_START_WORKER_ERROR_WORKER_NOT_FOUND = "core.start_worker: Error while starting the worker '{}', the worker is not"\
                                        " found, if you haven't created it yet please create it using "\
                                        "'core.create_worker()' before starting it."
CORE_START_WORKER_ERROR = "core.start_worker: Error while starting the worker '{}' on process '{}', look at the "\
                            "initial exception for more details."

CORE_STOP_WORKER_ERROR_WORKER_NOT_FOUND = "core.stop_worker: Error while stopping the worker '{}', the worker is not "\
                                        "found, if you haven't created it yet please create it using "\
                                        "'core.create_worker()' before stopping it."
CORE_STOP_WORKER_ERROR = "core.stop_worker: Error while stopping the worker '{}' on process '{}', look at the initial "\
                            "exception for more details."

CORE_CLOSE_WORKER_ERROR_WORKER_NOT_FOUND = "core.close_worker: Error while closing the worker '{}', the worker is not "\
                                        "found, if you haven't created it yet please create it using "\
                                        "'core.create_worker()' before closing it."
CORE_CLOSE_WORKER_ERROR = "core.close_worker: Error while closing the worker '{}' on process '{}', look at the initial"\
                            " exception for more details."

CORE_WORKER_GET_STATUS_ERROR_WORKER_NOT_FOUND = "core.worker_get_status: Error while getting the status of the worker "\
                                                "'{}', the worker is not found, if you haven't created it yet please "\
                                                "create it using 'core.create_worker()' before getting its status."
CORE_WORKER_GET_STATUS_ERROR = "core.worker_get_status: Error while getting the status of the worker '{}' on process "\
                                "'{}', look at the initial exception for more details."
