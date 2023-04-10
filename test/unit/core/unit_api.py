import unittest
from unittest.mock import Mock

from kuix.core.ipc import API, NotRemoteError
from kuix.core.utils import Colors


class TestApi(API):

    def __init__(self):
        super().__init__()
        self.value = False

    def unittest_method(self, a, b, *args, **kwargs):
        self.value = True
        return a + b


class UnitApi(unittest.TestCase):

    def setUp(self):
        # Shared hub mock
        self.hub = Mock()

        self.api = None  # PLACEHOLDER FOR API

    def instance(self):
        print(Colors.MAGENTA + "Api 1/ Instance" + Colors.END)

        # 1/ Instance
        self.api = TestApi()

    def remote(self):
        print(Colors.MAGENTA + "Api 2/ Remote" + Colors.END)
        # 1/ Enable remote
        self.api._enable_remote("P_UNITTEST", self.hub)
        self.assertEqual(self.api.remote, True)
        self.assertEqual(self.api.process_id, "P_UNITTEST")
        self.assertEqual(self.api.shared_hub, self.hub)

        # 2/ Test forwarding
        # Mock setup
        self.hub.call.return_value = 10
        res = self.api.unittest_method(10, 20, a=30, b=40)
        self.assertEqual(res, 10)
        self.hub.call.assert_called_with("P_UNITTEST", "unittest_method", 10, 20, a=30, b=40)

    def raw_call(self):
        print(Colors.MAGENTA + "Api 3/ Raw call" + Colors.END)
        # 1/ Register raw call
        not_remote_api = TestApi()
        not_remote_api._register_raw_call("unittest_raw_method", lambda x: x)
        self.assertIn("unittest_raw_method", dir(not_remote_api))

        # 2/ Raw call
        # Not remote
        with self.assertRaises(NotRemoteError):
            not_remote_api._raw_call("unittest_raw_method", 10)
        # Raw call
        self.api._raw_call("unittest_raw_method", x=10)
        self.hub.call.assert_called_with("P_UNITTEST", "unittest_raw_method", x=10)

        # 3/ Not remote register raw_call
        not_remote_api._register_raw_call("unittest_raw_method2", lambda x: x)
        self.assertIn("unittest_raw_method2", dir(not_remote_api))

        # 4/ is raw call
        self.assertTrue(not_remote_api._is_raw_call_registered("unittest_raw_method2"))
        self.assertFalse(not_remote_api._is_raw_call_registered("unittest_raw_method3"))
        self.assertFalse(self.api._is_raw_call_registered("unittest_raw_method"))

        # 4/ Unregister raw call
        not_remote_api._unregister_raw_call("unittest_raw_method2")
        self.assertNotIn("unittest_raw_method2", dir(not_remote_api))

    def runTest(self):
        print(Colors.CYAN + Colors.BOLD + f"--- RUNNING Api UNIT TEST ---" + Colors.END)
        self.instance()
        self.remote()
        self.raw_call()
        print(Colors.CYAN + Colors.BOLD + f"--- PASSED Api UNIT TEST ---" + Colors.END)


if __name__ == '__main__':
    unittest.main()
