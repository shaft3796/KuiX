import threading
import time
import unittest
from unittest.mock import patch

from colorama import Fore, Style

from kuix.core.utils import Lockable, Stateful, AlreadyBuiltError, NotBuiltError, AlreadyRunningError, NotRunningError, \
    NotDestroyedError, AlreadyDestroyedError


class UnitUtils(unittest.TestCase):

    def setUp(self):
        pass

    def unit_lockable(self):
        print(Fore.MAGENTA + "Utils 1/ Lockable" + Style.RESET_ALL)

        # 1/ Lock
        class TestLockable(Lockable):
            def __init__(self):
                super().__init__()

            @Lockable.locked
            def test(self):
                time.sleep(0.5)

        test_lockable = TestLockable()
        now = time.time()
        t1, t2 = threading.Thread(target=test_lockable.test), threading.Thread(target=test_lockable.test)
        t1.start(), t2.start()
        t1.join(), t2.join()
        self.assertGreaterEqual(time.time() - now, 1)

    def unit_stateful(self):
        print(Fore.MAGENTA + "Utils 2/ Stateful" + Style.RESET_ALL)

        class TestStateful(Stateful):
            def __init__(self):
                super().__init__()

            @Stateful.require_not_built
            def req_not_built(self):
                pass

            @Stateful.require_built
            def req_built(self):
                pass

            @Stateful.require_running
            def req_running(self):
                pass

            @Stateful.require_not_running
            def req_not_running(self):
                pass

            @Stateful.require_destroyed
            def req_destroyed(self):
                pass

            @Stateful.require_not_destroyed
            def req_not_destroyed(self):
                pass

            @Stateful.build_method
            def build(self):
                pass

            @Stateful.start_method
            def start(self):
                pass

            @Stateful.stop_method
            def stop(self):
                pass

            @Stateful.destroy_method
            def destroy(self):
                pass

        test = TestStateful()

        # 1/ Check methods
        self.assertFalse(test.is_built())
        self.assertFalse(test.is_running())
        self.assertFalse(test.is_destroyed())

        # 2/ Set methods
        test.set_built()
        self.assertTrue(test.is_built())
        test.set_running()
        self.assertTrue(test.is_running())
        test.set_destroyed()
        self.assertTrue(test.is_destroyed())

        # 3/ Check decorators

        # Built
        test = TestStateful()
        with self.assertRaises(NotBuiltError):
            test.req_built()
        test.req_not_built()
        test.set_built()
        with self.assertRaises(AlreadyBuiltError):
            test.req_not_built()
        test.req_built()

        # Running
        test = TestStateful()
        with self.assertRaises(NotRunningError):
            test.req_running()
        test.req_not_running()
        test.set_running()
        with self.assertRaises(AlreadyRunningError):
            test.req_not_running()
        test.req_running()

        # Destroyed
        test = TestStateful()
        with self.assertRaises(NotDestroyedError):
            test.req_destroyed()
        test.req_not_destroyed()
        test.set_destroyed()
        with self.assertRaises(AlreadyDestroyedError):
            test.req_not_destroyed()
        test.req_destroyed()

        # 4/ Check abstractions
        test = TestStateful()

        test.build()
        self.assertTrue(test.is_built())

        test.start()
        self.assertTrue(test.is_running())

        test.stop()
        self.assertFalse(test.is_running())

        test.destroy()
        self.assertTrue(test.is_destroyed())

    def runTest(self):
        print(Fore.CYAN + "\033[1m" + f"--- RUNNING Utils UNIT TEST ---" + Style.RESET_ALL)
        self.unit_lockable()
        self.unit_stateful()
        print(Fore.CYAN + "\033[1m" + f"--- PASSED Utils UNIT TEST ---\n" + Style.RESET_ALL)
        time.sleep(0.1)


if __name__ == '__main__':
    unittest.main()
