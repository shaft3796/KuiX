"""
Event handling system.
"""
from kuix.core.exception import GenericException

# --- MESSAGES ---
ROUTE = "EVENT_HANDLER_<{}>"  # Deprecated

CALLBACK_NOT_CALLABLE_ERROR = "{}: error while subscribing to '{}' event: callback is not callable."
BAD_SIGNATURE_ERROR = "{}: error while subscribing to '{}' event:\nExpected signature: {}\nActual signature: {}"
CALLBACK_EXECUTION_ERROR = "{}: error while executing callback for '{}' event:\n *args: {}\n **kwargs: {}\n" \
                           "Look at the traceback for more information."


# --- EXCEPTIONS ---
class EventSubscriptionError(GenericException):
    pass


class EventCallbackError(GenericException):
    pass


# --- EVENTS ---
class Events:
    UNITTEST_EVENT = "UNITTEST_EVENT"

    # --- KxProcess ---
    PROCESS_CLOSED = 'process_closed'
    WORKER_ADDED = 'worker_added'
    WORKER_REMOVED = 'worker_removed'
    WORKER_OPENED = 'worker_opened'
    WORKER_STARTED = 'worker_started'
    WORKER_STOPPED = 'worker_stopped'
    WORKER_CLOSED = 'worker_closed'

    # --- Core ---
    PROCESS_CREATED = 'process_created'


class CallbackRequirements:
    req = {
        # --- KxProcess --
        Events.PROCESS_CLOSED: ['kx_id'],
        Events.WORKER_ADDED: ['kx_id', 'worker_identifier'],
        Events.WORKER_REMOVED: ['kx_id', 'worker_identifier'],
        Events.WORKER_OPENED: ['kx_id', 'worker_identifier'],
        Events.WORKER_STARTED: ['kx_id', 'worker_identifier'],
        Events.WORKER_STOPPED: ['kx_id', 'worker_identifier'],
        Events.WORKER_CLOSED: ['kx_id', 'worker_identifier'],

        # --- Core ---
        Events.PROCESS_CREATED: ['kx_id'],
    }

    @classmethod
    def add(cls, event_name, callback_requirement):
        cls.req[event_name] = callback_requirement
