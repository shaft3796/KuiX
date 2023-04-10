"""
Set of classes to implement inter-process communication between kuix and the processes.
"""
from inspect import signature

from kuix.core.event import *

from multiprocessing.managers import BaseManager
import multiprocessing
import threading
import time

from kuix.core.logger import logger

# --- MESSAGES ---
HUB_ROUTE = "IPC-Shared-Hub"
CONNECTOR_ROUTE = "IPC-Connector<'{}'>"

ALREADY_REGISTERED_WARNING = "WARNING: The process '{}' is already registered to the hub. " \
                             "If the process was removed and recreated, call <SharedHub>.unregister_process('{}') " \
                             "before registering it again."
UNKNOWN_CALL_ID = "ERROR: The call ID '{}' is unknown. Make a call first to get a call ID."

API_NOT_REMOTE_ERROR = "ERROR: The API '{}' is set as remote.\n If your in the process of the target object you can " \
                       "access it through API.target\n If your in another process, enable remote through "
UNKNOWN_CUSTOM_CALL = "{}: The method {} was call through a raw call from a remote API, however this methods doesn't " \
                      "exits, you can register it through API.register_raw_call method on this process."


# --- EXCEPTIONS ---
class NotRemoteError(GenericException):
    pass


class UnknownCustomCallError(GenericException):
    pass


# --- CLASSES ---


class SharedHub:
    """
    Store all function calls and responses.
    """

    def __init__(self):
        """
        Constructor of the SharedHub class.
        """
        self.calls = {}  # {process_id: {call_id: {call-data}, ...}, ...}
        self.events = {}  # {process_id: {event_name: [event-data, event-data, ...]}, ...}
        self.responses = {}  # {process_id: {call_id: {response-data}, ...}, ...}

        self.semaphore = multiprocessing.Semaphore(1)  # Semaphore to let a thread make a call

    def clear_process(self, process_id: str):
        """
        Unregister a process.
        :param str process_id: Process ID
        """
        if process_id not in self.calls or process_id not in self.responses:
            return
        self.calls.pop(process_id)
        self.responses.pop(process_id)

    def call(self, process_id: str, method_name: str, *args, **kwargs):
        """
        Call a method of a process.
        :param str process_id: Process ID
        :param str method_name: Method name
        :param args: Method arguments
        :param kwargs: Method keyword arguments

        :return: The return value of the called method.
        """
        self.semaphore.acquire()

        # Set the response placeholder
        self.responses[process_id] = {"semaphore": multiprocessing.Semaphore(0), "response": None}

        # Call
        self.calls[process_id] = {
            'method': method_name,
            'args': args,
            'kwargs': kwargs,
        }

        self.semaphore.release()

        # Wait for the response
        self.responses[process_id]["semaphore"].acquire()
        self.semaphore.acquire()
        response = self.responses[process_id]["response"]
        self.responses[process_id] = None
        self.semaphore.release()

        return response

    def get_call(self, process_id: str):
        """
        Get a call.
        :param str process_id: Process ID
        :return: Call data
        """
        if process_id not in self.calls:
            return None
        call = self.calls[process_id]
        self.calls[process_id] = None
        return call

    def set_response(self, process_id: str, response):
        """
        Set the response for a given call.
        :param str process_id: Process ID
        :param response: Response data
        """
        if process_id not in self.responses:
            return
        self.responses[process_id]["response"] = response
        self.responses[process_id]["semaphore"].release()

    # --- EVENTS ---
    def subscribe(self, process_id: str, event_name: str):
        """
        Subscribe to an event.
        :param str process_id: Process ID
        :param str event_name: Event name
        """
        if process_id not in self.events:
            self.events[process_id] = {}
        if event_name not in self.events[process_id]:
            self.events[process_id][event_name] = []

    def unsubscribe(self, process_id: str, event_name: str):
        """
        Unsubscribe to an event.
        :param str process_id: Process ID
        :param str event_name: Event name
        """
        self.events[process_id].pop(event_name)
        if len(self.events[process_id]) == 0:
            self.events.pop(process_id)

    def trigger(self, event_name: str, *args, **kwargs):
        """
        Trigger an event.
        :param str event_name: Event name
        :param args: Event arguments
        :param kwargs: Event keyword arguments
        """
        for process_id in self.events:
            if event_name not in self.events[process_id]:
                continue
            self.events[process_id][event_name].append((args, kwargs))

    def get_events(self, process_id: str, event_name: str):
        """
        Flush a part of the event cache.
        :param str process_id: Process ID
        :param str event_name: Event name
        """
        res = []
        if process_id not in self.events or event_name not in self.events[process_id]:
            return res
        while len(self.events[process_id][event_name]) > 0:
            res.append(self.events[process_id][event_name].pop())

        return res


class API:
    """
    Define tha base class for all APIs.
    This class can call methods directly on the object on the same process, or it can forward the calls to a remote
    process in remote mode.
    """

    def __init__(self, target=None):
        """
        Constructor of the API class.
        :param target: Target object
        """
        self.target = target
        self.process_id = None
        self.shared_hub = None
        self.remote = False

    def _raw_remote_call(self, func_name):
        def wrapper(*args, **kwargs):
            # We call the method remotely
            response = self.shared_hub.call(self.process_id, func_name, *args, **kwargs)
            if isinstance(response, Exception):
                raise response
            return response

        return wrapper

    def _enable_remote(self, process_id: str, shared_hub: SharedHub):
        self.remote = True
        self.process_id = process_id
        self.shared_hub = shared_hub

        # Override all methods to forward them to the remote process
        for method_name in dir(self):
            if method_name.startswith('_') or method_name in ['_raw_call', '_enable_remote', '_register_raw_call',
                                                              'is_raw_call_registered', '_unregister_raw_call',
                                                              'shared_hub', 'process_id', 'target', 'remote']:
                continue
            # Check if the method is a function
            if not callable(getattr(self, method_name)):
                continue
            # We override the method
            setattr(self, method_name, self._raw_remote_call(method_name))

        return self

    def _raw_call(self, func_name, *args, **kwargs):
        """
        Call a method of the target API. This method must be registered in the API.
        :param str func_name: Method name
        :param args: Method arguments
        :param kwargs: Method keyword arguments

        :raises NotRemoteError: If the API is not in remote mode while calling the raw_call method.
        :return: Method return value
        """
        if self.remote:
            return self._raw_remote_call(func_name)(*args, **kwargs)
        else:
            raise NotRemoteError(API_NOT_REMOTE_ERROR.format(self.__class__.__name__))

    def _register_raw_call(self, func_name, callback):
        """
        Register a method to be callable remotely by another API in remote mode through the raw_call method.
        :param str func_name: Method name
        :param callback: Method callback
        """
        if not self.remote:
            setattr(self, func_name, callback)

    def _unregister_raw_call(self, func_name):
        """
        Unregister a method to be callable remotely by another API in remote mode through the raw_call method.
        :param str func_name: Method name
        """
        if not self.remote and hasattr(self, func_name):
            delattr(self, func_name)

    def _is_raw_call_registered(self, func_name):
        """
        Check if a method is registered to be callable remotely by another API in remote mode through the raw_call method.
        :param str func_name: Method name
        """
        if not self.remote:
            return hasattr(self, func_name)
        return False


class Connector:
    """
    Connect a class from a process to the SharedHub.
    """

    def __init__(self, process_id: str, api, shared_hub: SharedHub, prefix=""):
        """
        Constructor of the Connector class.
        :param str process_id: Process ID
        :param SharedHub shared_hub: SharedHub instance
        """
        self.process_id = process_id
        self.api = api
        self.shared_hub = shared_hub
        self.prefix = prefix if prefix != "" else "Process {}".format(process_id)

        self.alive = True

        self.remote_apis = {}

        # events
        self.callbacks = {}

        threading.Thread(target=self._listen, name=f"listener_{self.process_id}").start()

    def _listen(self):
        """
        Listen for calls & events. (Blocking)
        """
        while self.alive:
            # Events
            for event_name in self.callbacks.copy():
                events = self.shared_hub.get_events(self.process_id, event_name)
                for event in events:
                    for callback in self.callbacks[event_name]:
                        threading.Thread(target=self._call_event, args=(event_name, callback, *event[0]),
                                         kwargs=event[1],
                                         name=f"event_{event_name}_{self.process_id}").start()

            # IPC calls
            call = self.shared_hub.get_call(self.process_id)
            if call is not None:
                method_name = call["method"]
                args = call["args"]
                kwargs = call["kwargs"]
                self._call_api(method_name, *args, **kwargs)
            else:
                time.sleep(0.0001)  # Max 10k calls per second, wide enough for IO tasks.
        self.alive = True

    def _call_api(self, method_name: str, *args, **kwargs, ):
        """
        Call a method of the API.
        :param str method_name: Method name
        :param args: Method arguments
        :param kwargs: Method keyword arguments

        :return: Response data
        """
        try:
            response = getattr(self.api, method_name)(*args, **kwargs)
        except AttributeError as e:
            response = UnknownCustomCallError(UNKNOWN_CUSTOM_CALL.format(self.prefix, method_name)) + e
        except Exception as e:
            response = e

        self.shared_hub.set_response(self.process_id, response)

    def _call_event(self, event_name: str, callback: callable, *args, **kwargs):
        """
        Call an event.
        :param callback: Callback
        :param args: Event arguments
        :param kwargs: Event keyword arguments
        """
        try:
            callback(*args, **kwargs)
        except Exception as e:
            e = EventCallbackError(CALLBACK_EXECUTION_ERROR.format(self.prefix, event_name, args, kwargs)) + e
            logger.error(e, CONNECTOR_ROUTE.format(self.process_id))

    def close(self):
        """
        Kill the connector.
        """
        self.alive = False
        while not self.alive:
            time.sleep(0.01)
        self.alive = False

    # -- Remote APIs --
    def add_api(self, target_process_id: str, api_type: type):
        """
        Add a remote API to the connector.
        :param str target_process_id: Process ID
        :param type api_type: API type
        """
        self.remote_apis[target_process_id] = api_type(None)._enable_remote(target_process_id, self.shared_hub)

    def add_instanced_api(self, target_process_id: str, api: API):
        """
        Add a remote API to the connector.
        :param str target_process_id: Process ID
        :param API api: API instance
        """
        if not api.remote:
            api._enable_remote(target_process_id, self.shared_hub)
        self.remote_apis[target_process_id] = api

    def remove_api(self, target_process_id: str):
        """
        Remove a pipe to a process.
        :param str target_process_id: Process ID
        """
        del self.remote_apis[target_process_id]

    def get_api(self, target_process_id: str):
        """
        Get a remote API.
        :param str target_process_id: Process ID
        :return: Remote API
        """
        return self.remote_apis[target_process_id]

    # --- Events ---
    def subscribe(self, event_name: str, callback):
        """
        Subscribe to an event.
        :param str event_name: Event name
        :param callback: Callback

        :raises EventSubscriptionError: If the callback is not callable or if the callback signature is not valid.
        """
        # We check for the callback validity
        if not callable(callback):
            raise EventSubscriptionError(CALLBACK_NOT_CALLABLE_ERROR.format(self.prefix, event_name))
        # We check if each callback parameter has the same name as the corresponding requirement
        if event_name in CallbackRequirements.req:
            for param_name, param in signature(callback).parameters.items():
                if param_name not in CallbackRequirements.req[event_name]:
                    raise EventSubscriptionError(BAD_SIGNATURE_ERROR.format(self.prefix, event_name,
                                                                            CallbackRequirements.req[event_name],
                                                                            signature(callback).parameters))

        if event_name not in self.callbacks:
            self.callbacks[event_name] = []
        self.callbacks[event_name].append(callback)
        self.shared_hub.subscribe(self.process_id, event_name)

    def unsubscribe(self, event_name: str, callback):
        """
        Unsubscribe from an event.
        :param str event_name: Event name
        :param callback: Callback
        """
        if event_name in self.callbacks:
            if callback in self.callbacks[event_name]:
                self.callbacks[event_name].remove(callback)
                if len(self.callbacks[event_name]) == 0:
                    self.shared_hub.unsubscribe(self.process_id, event_name)
                    del self.callbacks[event_name]

    def trigger(self, event_name: str, *args, **kwargs):
        """
        Trigger an event.
        :param str event_name: Event name
        :param args: Event arguments
        :param kwargs: Event keyword arguments
        """
        self.shared_hub.trigger(event_name, *args, **kwargs)


# Create the hub
class Manager(BaseManager):
    SharedHub = None


def new_hub():
    manager = Manager()
    manager.register("SharedHub", SharedHub)
    manager.start()
    return manager.SharedHub()
