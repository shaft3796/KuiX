import time
import unittest
from unittest.mock import Mock, patch

from kuix.core.event import Events
from kuix.core.utils import Colors
from kuix.workers.base_worker import BaseWorker, WorkerCoreMethodCallError


class UnitBaseWorker(unittest.TestCase):

    def setUp(self):
        self.worker = None  # PLACEHOLDER
        self.component = None  # PLACEHOLDER

    def unit_instance(self):
        print(Colors.MAGENTA + "BaseWorker 1/ Instance" + Colors.END)
        # 1/ Instance
        self.worker = BaseWorker("UNITTEST")

        # 2/ State
        self.assertFalse(self.worker.is_opened())
        self.assertFalse(self.worker.is_running())
        self.assertFalse(self.worker.is_closed())

        # 3/ Components
        self.assertEqual(len(self.worker.components), 0)
        self.component = Mock()
        with patch("kuix.core.logger.logger.warning") as mock_logger:
            self.assertEqual(self.component, self.worker.add_component("UNITTEST_COMP", self.component))
            mock_logger.assert_called_once()
        self.assertEqual(len(self.worker.components), 1)
        # Removing
        self.worker.remove_component("UNITTEST_COMP")
        self.assertEqual(len(self.worker.components), 0)
        # Add manually
        self.worker.components["UNITTEST_COMP"] = self.component


    def unit_state_change(self):
        print(Colors.MAGENTA + "BaseWorker 2/ State Change" + Colors.END)
        # 1/ No Except Base
        process_api = Mock()
        process_api.get_kx_id.return_value = "UNITTEST"
        self.worker.process_api = process_api
        self.worker.open()
        process_api.trigger_event.assert_called_once_with(Events.WORKER_OPENED, "UNITTEST", "UNITTEST")
        self.worker.start()
        process_api.trigger_event.assert_called_with(Events.WORKER_STARTED, "UNITTEST", "UNITTEST")
        self.worker.stop()
        process_api.trigger_event.assert_called_with(Events.WORKER_STOPPED, "UNITTEST", "UNITTEST")
        self.worker.close()
        process_api.trigger_event.assert_called_with(Events.WORKER_CLOSED, "UNITTEST", "UNITTEST")

        # 2/ Except Base
        self.worker.OPENED = False
        self.worker.RUNNING = False
        self.worker.CLOSED = False
        self.worker.__open__ = Mock(side_effect=Exception())
        self.worker.__start__ = Mock(side_effect=Exception())
        self.worker.__stop__ = Mock(side_effect=Exception())
        self.worker.__close__ = Mock(side_effect=Exception())
        with self.assertRaises(WorkerCoreMethodCallError):
            self.worker.open()
        self.worker.method_set_opened()
        with self.assertRaises(WorkerCoreMethodCallError):
            self.worker.start()
        self.worker.method_set_running()
        with self.assertRaises(WorkerCoreMethodCallError):
            self.worker.stop()
        self.worker.method_set_not_running()
        with self.assertRaises(WorkerCoreMethodCallError):
            self.worker.close()
        self.worker.method_set_closed()
        self.worker.__open__.assert_called_once()
        self.worker.__start__.assert_called_once()
        self.worker.__stop__.assert_called_once()
        self.worker.__close__.assert_called_once()

        # 3/ Except Component
        self.worker.OPENED = False
        self.worker.RUNNING = False
        self.worker.CLOSED = False
        self.worker.__open__ = Mock()
        self.worker.__start__ = Mock()
        self.worker.__stop__ = Mock()
        self.worker.__close__ = Mock()
        self.worker.components["UNITTEST_COMP"].open = Mock(side_effect=Exception())
        self.worker.components["UNITTEST_COMP"].start = Mock(side_effect=Exception())
        self.worker.components["UNITTEST_COMP"].stop = Mock(side_effect=Exception())
        self.worker.components["UNITTEST_COMP"].close = Mock(side_effect=Exception())

        with self.assertRaises(WorkerCoreMethodCallError):
            self.worker.open()
        self.worker.method_set_opened()
        with self.assertRaises(WorkerCoreMethodCallError):
            self.worker.start()
        self.worker.method_set_running()
        with self.assertRaises(WorkerCoreMethodCallError):
            self.worker.stop()
        self.worker.method_set_not_running()
        with self.assertRaises(WorkerCoreMethodCallError):
            self.worker.close()
        self.worker.method_set_closed()
        self.worker.components["UNITTEST_COMP"].open.assert_called_once()
        self.worker.components["UNITTEST_COMP"].start.assert_called_once()
        self.worker.components["UNITTEST_COMP"].stop.assert_called_once()
        self.worker.components["UNITTEST_COMP"].close.assert_called_once()

    def runTest(self):
        print(Colors.CYAN + Colors.BOLD + f"--- RUNNING BaseWorker UNIT TEST ---" + Colors.END)
        self.unit_instance()
        self.unit_state_change()
        print(Colors.CYAN + Colors.BOLD + f"--- PASSED BaseWorker UNIT TEST ---\n" + Colors.END)
        time.sleep(0.1)


if __name__ == '__main__':
    unittest.main()
