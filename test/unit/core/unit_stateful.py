import unittest

from kuix.core.stateful import Stateful, StateError
from kuix.core.utils import Colors


class Test(Stateful):

    @Stateful.open_method
    def open(self):
        pass

    @Stateful.start_method
    def start(self):
        pass

    @Stateful.stop_method
    def stop(self):
        pass

    @Stateful.close_method
    def close(self):
        pass

    @Stateful.require_running
    def test_method(self):
        pass


class UnitStateful(unittest.TestCase):

    def setUp(self):
        pass

    def instance(self):
        print(Colors.MAGENTA + "Stateful 1/ instance" + Colors.END)
        # 1/ New instance
        s = Stateful()
        self.assertFalse(s.OPENED)
        self.assertFalse(s.RUNNING)
        self.assertFalse(s.CLOSED)

    def state_check_methods(self):
        print(Colors.MAGENTA + "Stateful 2/ state check methods" + Colors.END)
        # 2/ State check methods
        s = Stateful()
        self.assertFalse(s.is_opened())
        self.assertFalse(s.is_running())
        self.assertFalse(s.is_closed())

    def state_set_methods(self):
        print(Colors.MAGENTA + "Stateful 3/ state set methods" + Colors.END)
        # 3/ State set methods
        s = Stateful()
        # Open
        s.method_set_opened()
        self.assertTrue(s.is_opened())
        self.assertFalse(s.is_running())
        self.assertFalse(s.is_closed())
        # Running
        s.method_set_running()
        self.assertTrue(s.is_opened())
        self.assertTrue(s.is_running())
        self.assertFalse(s.is_closed())
        # Not running
        s.method_set_not_running()
        self.assertTrue(s.is_opened())
        self.assertFalse(s.is_running())
        self.assertFalse(s.is_closed())
        # Closed
        s.method_set_closed()
        self.assertTrue(s.is_opened())
        self.assertFalse(s.is_running())
        self.assertTrue(s.is_closed())

    def decorators_check(self):
        print(Colors.MAGENTA + "Stateful 4/ decorators check" + Colors.END)
        # 1/ State set decorators
        s = Test()
        # Open
        s.open()
        self.assertTrue(s.is_opened())
        self.assertFalse(s.is_running())
        self.assertFalse(s.is_closed())
        # Running
        s.start()
        self.assertTrue(s.is_opened())
        self.assertTrue(s.is_running())
        self.assertFalse(s.is_closed())
        # Not running
        s.stop()
        self.assertTrue(s.is_opened())
        self.assertFalse(s.is_running())
        self.assertFalse(s.is_closed())
        # Closed
        s.close()
        self.assertTrue(s.is_opened())
        self.assertFalse(s.is_running())
        self.assertTrue(s.is_closed())

        # 2/ State check exception decorators
        s = Test()
        # Not running for methods
        with self.assertRaises(StateError):
            s.test_method()
        # Not opened
        with self.assertRaises(StateError):
            s.start()
        with self.assertRaises(StateError):
            s.stop()
        with self.assertRaises(StateError):
            s.close()
        s.open()
        # Already opened
        with self.assertRaises(StateError):
            s.open()
        # Not running
        with self.assertRaises(StateError):
            s.stop()
        s.start()
        # Already running
        with self.assertRaises(StateError):
            s.start()
        # Still running
        with self.assertRaises(StateError):
            s.close()
        s.stop()
        s.close()
        # Already closed
        with self.assertRaises(StateError):
            s.close()

    def runTest(self):
        print(Colors.CYAN + Colors.BOLD + f"--- RUNNING Stateful UNIT TEST ---" + Colors.END)
        self.instance()
        self.state_check_methods()
        self.state_set_methods()
        self.decorators_check()
        print(Colors.CYAN + Colors.BOLD + f"--- PASSED Stateful UNIT TEST ---" + Colors.END)


if __name__ == '__main__':
    unittest.main()
