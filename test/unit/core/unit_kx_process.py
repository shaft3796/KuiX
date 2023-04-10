import time
import unittest
from unittest.mock import Mock, patch

from kuix.core.event import Events
from kuix.core.exception import GenericException
from kuix.core.kuix_core import KuixAPI
from kuix.core.kx_process import KxProcessAPI, KxProcess, WorkerAlreadyAddedError, UnknownWorkerError, WorkerStateError, \
    WorkerMethodCallError, new_kx_process, UnknownComponentError, UnknownComponentMethodError
from kuix.core.utils import Colors
from kuix.core.logger import logger


class UnitKxProcess(unittest.TestCase):

    def setUp(self):
        self.kx_process = None  # PLACEHOLDER

    def unit_api(self):
        print(Colors.MAGENTA + "KxProcess 1/ API" + Colors.END)
        # 1/ Instance
        process = Mock()
        api = KxProcessAPI(process)

        # 2/ Call all methods
        # get_kx_id
        process.kx_id = 1
        self.assertEqual(api.get_kx_id(), 1)

        # close
        api.close()
        process.close.assert_called_once()

        # kill
        api.kill()
        process.kill.assert_called_once()

        # is_worker
        process.is_worker.return_value = True
        self.assertTrue(api.is_worker("worker"))
        process.is_worker.assert_called_once_with("worker")

        # add_worker
        api.add_worker("worker")
        process.add_worker.assert_called_once_with("worker")

        # remove_worker
        api.remove_worker("worker")
        process.remove_worker.assert_called_once_with("worker")

        # get_worker
        process.get_worker.return_value = "worker"
        self.assertEqual(api.get_worker("worker"), "worker")
        process.get_worker.assert_called_once_with("worker")

        # open_worker
        api.open_worker("worker")
        process.open_worker.assert_called_once_with("worker")

        # start_worker
        api.start_worker("worker")
        process.start_worker.assert_called_once_with("worker")

        # stop_worker
        api.stop_worker("worker")
        process.stop_worker.assert_called_once_with("worker")

        # close_worker
        api.close_worker("worker")
        process.close_worker.assert_called_once_with("worker")

        # kill_worker abstraction
        process.reset_mock()
        worker_mock = Mock()
        worker_mock.is_opened.return_value = True
        worker_mock.is_running.return_value = True
        process.get_worker.return_value = worker_mock
        api.kill_worker("worker")
        process.get_worker.assert_called_with("worker")
        worker_mock.is_opened.assert_called_once()
        worker_mock.is_running.assert_called_once()
        process.stop_worker.assert_called_once_with("worker")
        process.close_worker.assert_called_once_with("worker")
        process.remove_worker.assert_called_once_with("worker")

        # load_worker_abstraction
        process.reset_mock()
        worker_mock = Mock()
        worker_mock.worker_identifier = "worker"
        api.load_worker(worker_mock)
        process.add_worker.assert_called_once_with(worker_mock)
        process.open_worker.assert_called_once_with("worker")
        process.start_worker.assert_called_once_with("worker")



        # 3/ Call abstractions
        mock_worker = Mock()
        mock_component = Mock()
        mock_component.method.return_value = "result"
        process.get_worker.return_value = mock_worker
        mock_worker.components = {"component": mock_component}
        res = api.call_worker_component("worker", "component", "method", "args", kwarg="kwarg")
        self.assertEqual(res, "result")
        # Exception 1: UnknownComponentError
        with self.assertRaises(UnknownComponentError):
            api.call_worker_component("worker", "unknown", "method", "args", kwarg="kwarg")
        # Exception 2: UnknownComponentMethodError
        with self.assertRaises(UnknownComponentMethodError):
            api.call_worker_component("worker", "component", "unknown", "args", kwarg="kwarg")

        # worker state
        worker = Mock()
        worker.is_opened.return_value = True
        worker.is_running.return_value = True
        worker.is_closed.return_value = True
        process.get_worker.return_value = worker
        self.assertTrue(api.is_worker_opened("worker"))
        self.assertTrue(api.is_worker_running("worker"))
        self.assertTrue(api.is_worker_closed("worker"))
        process.get_worker.assert_called_with("worker")
        worker.is_opened.assert_called_once()
        worker.is_running.assert_called_once()
        worker.is_closed.assert_called_once()

        # trigger_event
        api.trigger_event("event", "args", kwarg="kwarg")
        process.connector.trigger.assert_called_once_with("event", "args", kwarg="kwarg")

    @patch("kuix.core.kx_process.os.kill")
    @patch("kuix.core.kx_process.Connector")
    @patch("kuix.core.kx_process.KxProcessAPI")
    def unit_instance(self, mock1, mock2, os_kill):
        print(Colors.MAGENTA + "KxProcess 2/ Instance" + Colors.END)
        # Setup mock
        mock_hub = Mock()
        mock_core_api = Mock()
        mock_connector = Mock()
        mock_connector.get_api.return_value = mock_core_api
        mock_kx_api = Mock()
        mock1.return_value = mock_kx_api
        mock2.return_value = mock_connector
        mock_worker = Mock()

        # 1/ Instance
        self.kx_process = KxProcess("UNITTEST", "./", mock_hub)
        self.assertEqual(mock_connector, self.kx_process.connector)
        self.assertEqual(mock_kx_api, self.kx_process.api)
        mock_connector.add_api.assert_called_once_with("main", KuixAPI)
        mock_connector.get_api.assert_called_once_with("main")
        self.assertEqual(mock_core_api, self.kx_process.core_api)

        # 1/ Is Worker
        self.assertFalse(self.kx_process.is_worker("W1"))

        # 2/ Add Worker
        mock_connector.trigger.reset_mock()
        mock_worker.worker_identifier = "W1"
        self.kx_process.add_worker(mock_worker)
        self.assertTrue(self.kx_process.is_worker("W1"))
        self.assertEqual(mock_worker.process_api, self.kx_process.api)
        mock_connector.trigger.assert_called_once_with(Events.WORKER_ADDED, "UNITTEST", "W1")
        # Exception 1 Already added
        with self.assertRaises(WorkerAlreadyAddedError):
            self.kx_process.add_worker(mock_worker)

        # 3/ Remove Worker
        mock_connector.trigger.reset_mock()
        self.kx_process.remove_worker("W1")
        self.assertFalse(self.kx_process.is_worker("W1"))
        mock_connector.trigger.assert_called_once_with(Events.WORKER_REMOVED, "UNITTEST", "W1")
        # Exception 1 Not added
        with self.assertRaises(UnknownWorkerError):
            self.kx_process.remove_worker("W1")
        # Exception 2 state error
        mock_worker.is_opened.return_value = True
        mock_worker.is_running.return_value = True
        mock_worker.is_closed.return_value = False
        self.kx_process.add_worker(mock_worker)
        with self.assertRaises(WorkerStateError):
            self.kx_process.remove_worker("W1")

        # 4/ Get Worker
        self.assertEqual(mock_worker, self.kx_process.get_worker("W1"))
        # Exception 1 Not added
        with self.assertRaises(UnknownWorkerError):
            self.kx_process.get_worker("Made with ♥ by Shaft")

        # 5/ Open Worker
        self.kx_process.open_worker("W1")
        mock_worker.open.assert_called_once()
        # With exception
        mock_worker.open.reset_mock()
        mock_worker.open.side_effect = Exception("Test")
        with self.assertRaises(GenericException) as e:
            self.kx_process.open_worker("W1")
        self.assertEqual(1, len(e.exception.ctx))
        mock_worker.open.assert_called_once()

        # 6/ Start Worker
        self.kx_process.start_worker("W1")
        mock_worker.start.assert_called_once()
        # With exception
        mock_worker.start.reset_mock()
        mock_worker.start.side_effect = Exception("Test")
        with self.assertRaises(GenericException) as e:
            self.kx_process.start_worker("W1")
        self.assertEqual(1, len(e.exception.ctx))
        mock_worker.start.assert_called_once()

        # 7/ Stop Worker
        self.kx_process.stop_worker("W1")
        mock_worker.stop.assert_called_once()
        # With exception
        mock_worker.stop.reset_mock()
        mock_worker.stop.side_effect = Exception("Test")
        with self.assertRaises(GenericException) as e:
            self.kx_process.stop_worker("W1")
        self.assertEqual(1, len(e.exception.ctx))
        mock_worker.stop.assert_called_once()

        # 8/ Close Worker
        mock_connector.trigger.reset_mock()
        mock_worker.is_opened.return_value = True
        mock_worker.is_closed.return_value = True
        self.kx_process.close_worker("W1")
        mock_worker.close.assert_called_once()
        mock_connector.trigger.assert_called_once_with(Events.WORKER_REMOVED, "UNITTEST", "W1")
        # With exception
        self.kx_process.add_worker(mock_worker)
        mock_worker.close.reset_mock()
        mock_worker.close.side_effect = Exception("Test")
        with self.assertRaises(GenericException) as e:
            self.kx_process.close_worker("W1")
        self.assertEqual(1, len(e.exception.ctx))
        mock_worker.close.assert_called_once()

        # 9/ Close
        mock_worker.is_running.return_value = True
        mock_worker.is_opened.return_value = True
        # reset side effect
        mock_worker.stop.reset_mock()
        mock_worker.stop.side_effect = None
        mock_worker.close.reset_mock()
        mock_worker.close.side_effect = None
        # second worker
        mworker2 = Mock()
        mworker2.worker_identifier = "W2"
        mworker2.is_running.return_value = False
        mworker2.is_opened.return_value = False
        self.kx_process.add_worker(mworker2)
        self.kx_process.close()
        mock_worker.stop.assert_called_once()
        mock_worker.close.assert_called_once()
        mock_kx_api.trigger_event.assert_called_once_with(Events.PROCESS_CLOSED, "UNITTEST")
        mock_connector.close.assert_called_once()
        mock_hub.clear_process.assert_called_once_with("UNITTEST")
        os_kill.assert_called_once()
        # Reset mocks
        mock_worker.stop.reset_mock()
        mock_worker.close.reset_mock()
        mock_kx_api.trigger_event.reset_mock()
        mock_connector.close.reset_mock()
        mock_hub.clear_process.reset_mock()
        os_kill.reset_mock()

        # With exception
        mock_worker.is_running.return_value = True
        # reset side effect
        mock_worker.stop.reset_mock()
        mock_worker.stop.side_effect = Exception("Test")

        with self.assertRaises(WorkerMethodCallError) as e:
            self.kx_process.close()

        # 10/ Kill
        # Patch the close method of the kx process
        self.kx_process.close = Mock()
        self.kx_process.kill()
        self.kx_process.close.assert_called_once()

        # With exception
        self.kx_process.close.reset_mock()
        self.kx_process.close.side_effect = Exception("Test")
        self.kx_process.kill()
        self.kx_process.close.assert_called_once()
        self.kx_process.api.trigger_event.assert_called_once_with(Events.PROCESS_CLOSED, "UNITTEST")
        self.kx_process.connector.close.assert_called_once()
        self.kx_process.shared_hub.clear_process.assert_called_once_with("UNITTEST")
        os_kill.assert_called_once()

        # 11/ new_kx_process
        mock_connector = Mock()
        mock2.return_value = mock_connector
        new_kx_process("UNITTEST", "", mock_hub)
        mock_connector.trigger.assert_called_once_with(Events.PROCESS_CREATED, "UNITTEST")

    def runTest(self):
        print(Colors.CYAN + Colors.BOLD + f"--- RUNNING KxProcess UNIT TEST ---" + Colors.END)
        self.unit_api()
        self.unit_instance()
        print(Colors.CYAN + Colors.BOLD + f"--- PASSED KxProcess UNIT TEST ---\n" + Colors.END)
        time.sleep(0.1)


if __name__ == '__main__':
    unittest.main()
