"""
Implements event handling.
"""
from dataclasses import dataclass
from inspect import signature

from src.core.Exceptions import EventCallbackError, EventSubscriptionError
from src.core.Logger import LOGGER, CORE


@dataclass
class ProcessEvent:
    # --- Socket Events ---
    SOCKET_CONNECTION_ACCEPTED = "socket_connection_accepted"
    SOCKET_CONNECTION_REFUSED = "socket_connection_refused"
    SOCKET_CONNECTION_CLOSED = "client_socket_connection_closed"
    SOCKET_CLIENT_CLOSED = "socket_client_closed"
    SOCKET_MESSAGE_RECEIVED = "socket_message_received"
    SOCKET_MESSAGE_SENT = "socket_message_sent"
    # --- IPC Events ---
    IPC_FAF_REQUEST_RECEIVED = "ipc_faf_request_received"
    IPC_FAF_REQUEST_EXCEPTION = "ipc_faf_request_exception"
    IPC_FAF_REQUEST_HANDLED = "ipc_faf_request_handled"
    IPC_BLOCKING_REQUEST_RECEIVED = "ipc_blocking_request_received"
    IPC_BLOCKING_REQUEST_EXCEPTION = "ipc_blocking_request_exception"
    IPC_BLOCKING_REQUEST_HANDLED = "ipc_blocking_request_handled"
    IPC_RESPONSE_RECEIVED = "ipc_response_received"
    IPC_RESPONSE_EXCEPTION = "ipc_response_exception"
    IPC_RESPONSE_HANDLED = "ipc_response_handled"
    IPC_FAF_REQUEST_SENT = "ipc_faf_request_sent"
    IPC_BLOCKING_REQUEST_SENT = "ipc_blocking_request_sent"
    IPC_RESPONSE_SENT = "ipc_response_sent"
    IPC_HANDLER_EXCEPTION = "ipc_handler_exception"

    # --- Process Events ---
    PROCESS_SCHEDULED_TO_CLOSE = "process_scheduled_to_close"
    STRATEGY_addED = "strategy_added"
    WORKER_CREATED = "worker_created"
    WORKER_STARTED = "worker_started"
    WORKER_STOPPED = "worker_stopped"
    WORKER_CLOSED = "worker_destroyed"


@dataclass
class CoreEvent:
    # --- Socket Events ---
    SOCKET_CONNECTION_ACCEPTED = "socket_connection_accepted"
    SOCKET_CONNECTION_REFUSED = "socket_connection_refused"
    SOCKET_CONNECTION_CLOSED = "server_socket_connection_closed"
    SOCKET_SERVER_CLOSED = "socket_client_closed"
    SOCKET_MESSAGE_RECEIVED = "socket_message_received"
    SOCKET_MESSAGE_SENT = "socket_message_sent"
    # --- IPC Events ---
    IPC_FAF_REQUEST_RECEIVED = "ipc_faf_request_received"
    IPC_FAF_REQUEST_EXCEPTION = "ipc_faf_request_exception"
    IPC_FAF_REQUEST_HANDLED = "ipc_faf_request_handled"
    IPC_BLOCKING_REQUEST_RECEIVED = "ipc_blocking_request_received"
    IPC_BLOCKING_REQUEST_EXCEPTION = "ipc_blocking_request_exception"
    IPC_BLOCKING_REQUEST_HANDLED = "ipc_blocking_request_handled"
    IPC_RESPONSE_RECEIVED = "ipc_response_received"
    IPC_RESPONSE_EXCEPTION = "ipc_response_exception"
    IPC_RESPONSE_HANDLED = "ipc_response_handled"
    IPC_FAF_REQUEST_SENT = "ipc_faf_request_sent"
    IPC_BLOCKING_REQUEST_SENT = "ipc_blocking_request_sent"
    IPC_RESPONSE_SENT = "ipc_response_sent"
    IPC_HANDLER_EXCEPTION = "ipc_handler_exception"

    # --- Core Events ---
    CORE_STARTED = "core_started"


CALLBACK_REQUIREMENTS = {
    # --- Process Socket ---
    ProcessEvent.SOCKET_CONNECTION_ACCEPTED: ["identifier"],
    ProcessEvent.SOCKET_CONNECTION_REFUSED: ["identifier"],
    ProcessEvent.SOCKET_CONNECTION_CLOSED: ["identifier", "from_client"],
    ProcessEvent.SOCKET_CLIENT_CLOSED: ["identifier"],
    ProcessEvent.SOCKET_MESSAGE_RECEIVED: ["identifier", "data"],
    ProcessEvent.SOCKET_MESSAGE_SENT: ["identifier", "data"],

    # --- Process IPC ---
    ProcessEvent.IPC_FAF_REQUEST_RECEIVED: ["identifier", "data"],
    ProcessEvent.IPC_FAF_REQUEST_EXCEPTION: ["identifier", "data", "exception"],
    ProcessEvent.IPC_FAF_REQUEST_HANDLED: ["identifier", "data"],
    ProcessEvent.IPC_FAF_REQUEST_SENT: ["identifier", "data"],
    ProcessEvent.IPC_BLOCKING_REQUEST_RECEIVED: ["identifier", "data"],
    ProcessEvent.IPC_BLOCKING_REQUEST_EXCEPTION: ["identifier", "data", "exception"],
    ProcessEvent.IPC_BLOCKING_REQUEST_HANDLED: ["identifier", "data"],
    ProcessEvent.IPC_BLOCKING_REQUEST_SENT: ["identifier", "data"],
    ProcessEvent.IPC_RESPONSE_RECEIVED: ["identifier", "data"],
    ProcessEvent.IPC_RESPONSE_EXCEPTION: ["identifier", "data", "exception"],
    ProcessEvent.IPC_RESPONSE_HANDLED: ["identifier", "data"],
    ProcessEvent.IPC_RESPONSE_SENT: ["identifier", "data"],
    ProcessEvent.IPC_HANDLER_EXCEPTION: ["identifier", "data", "exception"],

    # --- Process Events ---
    ProcessEvent.PROCESS_SCHEDULED_TO_CLOSE: [],
    ProcessEvent.STRATEGY_addED: ["strategy_name"],
    ProcessEvent.WORKER_CREATED: ["worker_identifier"],
    ProcessEvent.WORKER_STARTED: ["worker_identifier"],
    ProcessEvent.WORKER_STOPPED: ["worker_identifier"],
    ProcessEvent.WORKER_CLOSED: ["worker_identifier"],

    # --- Core Socket ---
    # We redefine just the ones that are different from the process events
    CoreEvent.SOCKET_CONNECTION_CLOSED: ["identifier", "from_server"],
    CoreEvent.SOCKET_SERVER_CLOSED: ["identifier"],
}


class EventHandler:
    """
    Base class for event handlers.
    """

    def __init__(self):
        """
        Constructor of an event handler.
        """
        self.events = {}  # {event_name: [event_handler, ...]}

    def new_event(self, event_name):
        """
        Create a new event field with the given name.
        :param event_name:
        """
        self.events[event_name] = []

    def subscribe(self, event_name, callback):
        """
        Subscribe to an event. The callback will be called when the event is triggered.
        :param event_name: name of the event
        :param callback: callback function
        :raises EventSubscriptionError: if the callback is not callable or if the signature is invalid
        """
        # We check for the callback validity
        if not callable(callback):
            raise EventSubscriptionError(f"Error while subscribing to '{event_name}' event: callback is not callable.")
        # We check if each callback parameter has the same name as the corresponding requirement
        if event_name in CALLBACK_REQUIREMENTS:
            for param_name, param in signature(callback).parameters.items():
                if param_name not in CALLBACK_REQUIREMENTS[event_name]:
                    raise EventSubscriptionError(f"Error while subscribing to '{event_name}' event: {event_name}\n"
                                                 f"Expected signature: {CALLBACK_REQUIREMENTS[event_name]}\n"
                                                 f"Actual signature: {signature(callback).parameters}")

        if event_name not in self.events:
            self.new_event(event_name)
        self.events[event_name].append(callback)

    def unsubscribe(self, event_name, callback):
        """
        Unsubscribe from an event.
        :param event_name:
        :param callback:
        :return:
        """
        if event_name in self.events:
            self.events[event_name].remove(callback)

    def trigger(self, event_name, event_ctx=None, *args, **kwargs):
        """
        Trigger an event.
        :param event_name:
        :param event_ctx: Optional event context if an exception occurs.
        :param args: Arguments for the callback
        :param kwargs: Keyword arguments for the callback
        :return:
        """
        if event_name in self.events:
            for callback in self.events[event_name]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    _e = EventCallbackError(f"Callback for event '{event_name}' raised an exception.\nArgs: "
                                            f"{args}\nKwargs: {kwargs}") + e
                    if event_ctx is not None:
                        _e.add_ctx(event_ctx)
                    LOGGER.warning_exception(_e, CORE)
