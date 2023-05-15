from kuix.core.logger import logger

import time
import unittest
from unittest.mock import Mock

from kuix.core.utils import Colors
from kuix.worker_components.base_worker_component import BaseWorkerComponent, WorkerComponentCoreMethodCallError


class UnitBaseWorkerComponent(unittest.TestCase):

    def setUp(self):
        self.component = None  # PLACEHOLDER

    def unit_instance(self):
        print(Colors.MAGENTA + "BaseWorkerComponent 1/ Instance " + Colors.END)
        # 1/ Instance
        self.component = BaseWorkerComponent(Mock())
        # 2/ State
        self.assertFalse(self.component.is_opened())
        self.assertFalse(self.component.is_running())
        self.assertFalse(self.component.is_closed())

    def unit_state_change(self):
        print(Colors.MAGENTA + "BaseWorkerComponent 2/ State Change " + Colors.END)
        # 1/ No Except Base
        self.component.open()
        self.component.start()
        self.component.stop()
        self.component.close()

        # 2/ Except Base
        self.component = BaseWorkerComponent(Mock())
        self.component.__open__ = Mock(side_effect=Exception())
        self.component.__start__ = Mock(side_effect=Exception())
        self.component.__stop__ = Mock(side_effect=Exception())
        self.component.__close__ = Mock(side_effect=Exception())
        with self.assertRaises(WorkerComponentCoreMethodCallError):
            self.component.open()
        self.component.method_set_opened()
        with self.assertRaises(WorkerComponentCoreMethodCallError):
            self.component.start()
        self.component.method_set_running()
        with self.assertRaises(WorkerComponentCoreMethodCallError):
            self.component.stop()
        self.component.method_set_not_running()
        with self.assertRaises(WorkerComponentCoreMethodCallError):
            self.component.close()
        self.component.method_set_closed()
        self.component.__open__.assert_called_once()
        self.component.__start__.assert_called_once()
        self.component.__stop__.assert_called_once()
        self.component.__close__.assert_called_once()

    def runTest(self):
        print(Colors.CYAN + Colors.BOLD + f"--- RUNNING BaseWorkerComponent UNIT TEST ---" + Colors.END)
        self.unit_instance()
        self.unit_state_change()
        print(Colors.CYAN + Colors.BOLD + f"--- PASSED BaseWorkerComponent UNIT TEST ---\n" + Colors.END)
        time.sleep(0.1)


if __name__ == '__main__':
    unittest.main()
