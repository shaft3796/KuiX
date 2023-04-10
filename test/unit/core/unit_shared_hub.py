import threading
import time
import unittest

from kuix.core.event import Events
from kuix.core.ipc import new_hub, SharedHub
from kuix.core.logger import logger
from kuix.core.utils import Colors


class UnitSharedHub(unittest.TestCase):

    def setUp(self):
        self.hub = None  # PLACEHOLDER FOR SHARED HUB

    def instance(self):
        print(Colors.MAGENTA + "SharedHub 1/ Instance" + Colors.END)
        self.hub = SharedHub()
        new_hub()

    def call(self):
        print(Colors.MAGENTA + "SharedHub 2/ Call" + Colors.END)

        # 1/ Call
        def resp():
            time.sleep(0.1)
            self.hub.set_response("P_UNITTEST", 100)

        threading.Thread(target=resp).start()
        response = self.hub.call("P_UNITTEST", "unittest_method", 10, 20, a=30, b=40)
        self.assertEqual(100, response)

        # 2/ Get Call
        call = self.hub.get_call("P_UNITTEST")
        expected = {'method': 'unittest_method', 'args': (10, 20), 'kwargs': {'a': 30, 'b': 40}}
        self.assertEqual(expected, call)

        # 3/ No exception
        self.hub.get_call("P_UNKNOWN")
        self.hub.set_response("P_UNKNOWN", 200)

    def clear_process(self):
        print(Colors.MAGENTA + "SharedHub 3/ Clear process" + Colors.END)
        self.hub.clear_process("P_UNITTEST")
        self.hub.clear_process("P2")
        self.assertNotIn("P_UNITTEST", self.hub.calls)
        self.assertNotIn("P2", self.hub.calls)
        self.assertNotIn("P_UNITTEST", self.hub.responses)
        self.assertNotIn("P2", self.hub.responses)

    def subscription(self):
        print(Colors.MAGENTA + "SharedHub 4/ Subscription" + Colors.END)

        # 1/ Subscription
        self.hub.subscribe("P_UNITTEST", Events.UNITTEST_EVENT)
        self.assertIn("P_UNITTEST", self.hub.events)
        self.assertIn(Events.UNITTEST_EVENT, self.hub.events["P_UNITTEST"])
        self.assertEqual(self.hub.events["P_UNITTEST"][Events.UNITTEST_EVENT], [])

        # 2/ Unsubscription
        self.hub.unsubscribe("P_UNITTEST", Events.UNITTEST_EVENT)
        self.assertNotIn("P_UNITTEST", self.hub.events)

    def triggering(self):
        print(Colors.MAGENTA + "SharedHub 5/ Triggering" + Colors.END)

        # 1/ Triggering
        self.hub.subscribe("P_UNITTEST", Events.UNITTEST_EVENT)
        self.hub.trigger(Events.UNITTEST_EVENT, 10, 20, a=30, b=40)
        self.assertEqual(self.hub.events["P_UNITTEST"][Events.UNITTEST_EVENT], [((10, 20), {'a': 30, 'b': 40})])

        # 2/ Get Events
        events = self.hub.get_events("P_UNITTEST", Events.UNITTEST_EVENT)
        self.assertEqual(events, [((10, 20), {'a': 30, 'b': 40})])
        self.assertEqual(self.hub.events["P_UNITTEST"][Events.UNITTEST_EVENT], [])

        # 3/ No exception
        self.hub.get_events("P_UNKNOWN", Events.UNITTEST_EVENT)
        self.hub.trigger("P_UNKNOWN", Events.UNITTEST_EVENT, 10, 20, a=30, b=40)

    def runTest(self):
        print(Colors.CYAN + Colors.BOLD + f"--- RUNNING SharedHub UNIT TEST ---" + Colors.END)
        self.instance()
        self.call()
        self.clear_process()
        self.subscription()
        self.triggering()
        print(Colors.CYAN + Colors.BOLD + f"--- PASSED SharedHub UNIT TEST ---" + Colors.END)


if __name__ == '__main__':
    unittest.main()
