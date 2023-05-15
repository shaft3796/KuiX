import threading
import time
import unittest
from unittest.mock import Mock, patch

import kuix.core.ipc
from kuix.core.event import EventSubscriptionError, CallbackRequirements
from kuix.core.ipc import Connector, UnknownCustomCallError
from kuix.core.logger import logger

from kuix.core.utils import Colors


class UnitConnector(unittest.TestCase):

    def setUp(self):
        # Mock
        self.hub = Mock()
        # Setup hub
        self.hub.get_events.return_value = []
        self.hub.get_call.return_value = None

        self.api = Mock()

        self.connector = None  # PLACEHOLDER FOR CONNECTOR
        self.remote_connector = None  # PLACEHOLDER FOR REMOTE CONNECTOR

    def unit_instance(self):
        print(Colors.MAGENTA + "Connector 1/ instance " + Colors.END)
        # 1/ instance
        self.connector = Connector("P_UNITTEST_1", self.api, self.hub, "P_UNITTEST_1")
        # Attributes check
        self.assertEqual(self.connector.process_id, "P_UNITTEST_1")
        self.assertEqual(self.connector.api, self.api)
        self.assertEqual(self.connector.shared_hub, self.hub)
        self.assertEqual(self.connector.prefix, "P_UNITTEST_1")
        self.assertEqual(self.connector.alive, True)
        self.assertEqual(self.connector.remote_apis, {})
        self.assertEqual(self.connector.callbacks, {})
        time.sleep(0.1)

        # 2/ Listener thread
        self.assertIn("listener_P_UNITTEST_1", [t.name for t in threading.enumerate()])
        self.hub.get_events.assert_not_called()
        self.hub.get_call.assert_called_with("P_UNITTEST_1")

        # 3/ Remote connector
        self.remote_connector = Connector("P_UNITTEST_MAIN", None, self.hub, "P_UNITTEST_MAIN")

    def unit_remote(self):
        print(Colors.MAGENTA + "Connector 2/ Remote " + Colors.END)

        # 1/ Add API call by type
        class MockApi(Mock):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._enable_remote = Mock(return_value=self)

        self.remote_connector.add_api("P_UNITTEST_1", MockApi)
        self.assertIn("P_UNITTEST_1", self.remote_connector.remote_apis)
        self.remote_connector.remote_apis["P_UNITTEST_1"]._enable_remote.assert_called_once_with("P_UNITTEST_1",
                                                                                                 self.hub)

        # 2/ Add API call by instance
        api = MockApi()
        api.remote = False
        api.enable_remote.return_value = api
        self.remote_connector.add_instanced_api("P_UNITTEST_2", api)
        self.assertIn("P_UNITTEST_2", self.remote_connector.remote_apis)
        self.remote_connector.remote_apis["P_UNITTEST_2"]._enable_remote.assert_called_once_with("P_UNITTEST_2",
                                                                                                 self.hub)

        # 3/ Get API
        self.assertEqual(self.remote_connector.get_api("P_UNITTEST_2"), api)

        # 4/ Remove API
        self.remote_connector.remove_api("P_UNITTEST_1")
        self.assertNotIn("P_UNITTEST_1", self.remote_connector.remote_apis)
        self.remote_connector.remove_api("P_UNITTEST_2")
        self.assertNotIn("P_UNITTEST_2", self.remote_connector.remote_apis)

        self.remote_connector.close()

    def unit_subscription(self):
        print(Colors.MAGENTA + "Connector 3/ subscription " + Colors.END)
        # 1/ Subscription
        callback = lambda x: x
        self.connector.subscribe("test", callback)
        self.assertIn("test", self.connector.callbacks)
        self.assertEqual([callback], self.connector.callbacks["test"])
        self.hub.subscribe.assert_called_once_with("P_UNITTEST_1", "test")

        # 2/ Not callable exception
        with self.assertRaises(EventSubscriptionError):
            self.connector.subscribe("test", "not_callable")

        # 3/ Bad signature exception
        # Adding a callback requirement
        CallbackRequirements.add("test", ["a", "b"])
        with self.assertRaises(EventSubscriptionError):
            self.connector.subscribe("test", lambda x: x)

        # 4/ Unsubscription
        self.connector.unsubscribe("test", callback)
        self.assertNotIn("test", self.connector.callbacks)
        self.hub.unsubscribe.assert_called_once_with("P_UNITTEST_1", "test")

        # 5/ Trigger
        self.connector.trigger("test", 10, 20, a=30, b=40)
        self.hub.trigger.assert_called_once_with("test", 10, 20, a=30, b=40)

    def unit_listener(self):
        print(Colors.MAGENTA + "Connector 4/ listener " + Colors.END)
        # 1/ Event good callback
        _mock = Mock()
        self.connector.subscribe("test2", _mock)
        self.hub.get_events.return_value = [((10, 20), {"a": 30, "b": 40})]
        time.sleep(0.1)
        _mock.assert_called_with(10, 20, a=30, b=40)

        # 2/ Event bad callback
        _logger = Mock()
        with patch("kuix.core.ipc.logger", _logger):
            _mock = Mock(side_effect=Exception("test"))
            self.connector.subscribe("test2", _mock)
            self.hub.get_events.return_value = [((10, 20), {"a": 30, "b": 40})]
            time.sleep(0.1)
            _mock.assert_called_with(10, 20, a=30, b=40)
            _logger.error.assert_called()
            self.hub.get_events.return_value = []
            # Unsubscribe
            self.connector.unsubscribe("test2", _mock)
            time.sleep(0.01)

        # 3/ Call good callback
        call = {"method": "call_test", "args": [10, 20], "kwargs": {"a": 30, "b": 40}}
        self.api.call_test.return_value = 100
        res = None
        def callback(process_id, response):
            nonlocal res
            res = response
            self.hub.get_call.return_value = None

        self.hub.set_response.side_effect = callback
        self.hub.get_call.return_value = call
        time.sleep(0.1)
        self.api.call_test.assert_called_with(10, 20, a=30, b=40)
        self.hub.set_response.assert_called_with("P_UNITTEST_1", 100)
        self.assertEqual(res, 100)

        # 4/ Call bad callback
        call = {"method": "call_test", "args": [10, 20], "kwargs": {"a": 30, "b": 40}}
        e = Exception("test")
        self.api.call_test.side_effect = e
        res = None
        def callback(process_id, response):
            self.hub.get_call.return_value = None
            nonlocal res
            res = response

        self.hub.set_response.side_effect = callback
        self.hub.get_call.return_value = call
        time.sleep(0.1)
        self.api.call_test.assert_called_with(10, 20, a=30, b=40)
        self.hub.set_response.assert_called_with("P_UNITTEST_1", e)
        self.assertEqual(res, e)

        # 5/ Call bad signature
        self.connector.api = None
        call = {"method": "call_test", "args": [10, 20], "kwargs": {"a": 30, "b": 40}}
        res = None
        def callback(process_id, response):
            self.hub.get_call.return_value = None
            nonlocal res
            res = response

        self.hub.set_response.side_effect = callback
        self.hub.get_call.return_value = call
        time.sleep(0.1)
        self.assertIsInstance(res, UnknownCustomCallError)

    def unit_close(self):
        print(Colors.MAGENTA + "Connector 5/ close " + Colors.END)
        # 1/ Close
        self.connector.close()
        self.assertEqual(self.connector.alive, False)
        # Check if listener thread is closed
        self.assertNotIn("listener_P_UNITTEST_1", [t.name for t in threading.enumerate()])

    def runTest(self):
        print(Colors.CYAN + Colors.BOLD + f"--- RUNNING Connector UNIT TEST ---" + Colors.END)
        self.unit_instance()
        self.unit_remote()
        self.unit_subscription()
        self.unit_listener()
        self.unit_close()
        print(Colors.CYAN + Colors.BOLD + f"--- PASSED Connector UNIT TEST ---\n" + Colors.END)
        time.sleep(0.1)


if __name__ == '__main__':
    unittest.main()
