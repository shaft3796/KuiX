from kuix.core.logger import logger

import time
import unittest
from unittest.mock import Mock

from kuix.core.utils import Colors
from kuix.kuix_components.base_kuix_component import BaseKuixComponent, KuixComponentCoreMethodCallError


class UnitBaseKuixComponent(unittest.TestCase):

    def setUp(self):
        self.component = None  # PLACEHOLDER

    def unit_instance(self):
        print(Colors.MAGENTA + "BaseKuixComponent 1/ Instance " + Colors.END)
        # 1/ Instance
        self.component = BaseKuixComponent(Mock())
        # 2/ State
        self.assertFalse(self.component.is_opened())
        self.assertFalse(self.component.is_running())
        self.assertFalse(self.component.is_closed())

    def unit_state_change(self):
        print(Colors.MAGENTA + "BaseKuixComponent 2/ State Change " + Colors.END)
        # 1/ No Except Base
        self.component.open()
        self.component.start()
        self.component.stop()
        self.component.close()

        # 2/ Except Base
        self.component = BaseKuixComponent(Mock())
        self.component.__open__ = Mock(side_effect=Exception())
        self.component.__start__ = Mock(side_effect=Exception())
        self.component.__stop__ = Mock(side_effect=Exception())
        self.component.__close__ = Mock(side_effect=Exception())
        with self.assertRaises(KuixComponentCoreMethodCallError):
            self.component.open()
        self.component.method_set_opened()
        with self.assertRaises(KuixComponentCoreMethodCallError):
            self.component.start()
        self.component.method_set_running()
        with self.assertRaises(KuixComponentCoreMethodCallError):
            self.component.stop()
        self.component.method_set_not_running()
        with self.assertRaises(KuixComponentCoreMethodCallError):
            self.component.close()
        self.component.method_set_closed()
        self.component.__open__.assert_called_once()
        self.component.__start__.assert_called_once()
        self.component.__stop__.assert_called_once()
        self.component.__close__.assert_called_once()

    def runTest(self):
        print(Colors.CYAN + Colors.BOLD + f"--- RUNNING BaseKuixComponent UNIT TEST ---" + Colors.END)
        self.unit_instance()
        self.unit_state_change()
        print(Colors.CYAN + Colors.BOLD + f"--- PASSED BaseKuixComponent UNIT TEST ---\n" + Colors.END)
        time.sleep(0.1)


if __name__ == '__main__':
    unittest.main()
