import os
import shutil
import time
import unittest
from unittest.mock import Mock, patch

import kuix.core.kuix_core
from kuix.core.kuix_core import KuixAPI, UnknownKxProcessError, UnknownComponentError, Kuix, KuixSetupError, \
    AlreadyConfiguredError, NotConfiguredError, NotSetupError, KxProcessAlreadyExistsError, ClosedError
from kuix.core.kx_process import WorkerAlreadyAddedError, UnknownWorkerError, WorkerMethodCallError, \
    UnknownComponentMethodError
from kuix.core.utils import Colors
from kuix.core.logger import logger
from kuix.kuix_components.base_kuix_component import KuixComponentCoreMethodCallError


class UnitKuix(unittest.TestCase):

    def setUp(self):
        self.kuix = None  # PLACEHOLDER

    def unit_api(self):
        print(Colors.MAGENTA + "Kuix 1/ API" + Colors.END)
        # 1/ Instance
        kuix = Mock()
        api = KuixAPI(kuix)

        # 2/ Call all methods
        # Add component
        component = Mock()
        api.add_component("C1", component)
        kuix.add_component.assert_called_once_with("C1", component)

        # Load config
        api._load_config()
        kuix._load_config.assert_called_once()
        api._load_json_config()
        kuix._load_json_config.assert_called_once()

        # Is configured
        kuix.is_configured.value = True
        self.assertTrue(api.is_configured())

        # Is setup
        kuix.is_setup.value = True
        self.assertTrue(api.is_setup())

        # Is closed
        kuix.is_closed.value = True
        self.assertTrue(api.is_closed())

        # Setup
        api.setup()
        kuix.setup.assert_called_once()

        # Close
        api.close()
        kuix.close.assert_called_once()

        # Create Process
        api.create_process("P1", 10, 20, a=30, b=40)
        kuix.create_process.assert_called_once_with("P1", 10, 20, a=30, b=40)

        # Is process
        kuix.is_process.return_value = True
        self.assertTrue(api.is_process("P1"))
        kuix.is_process.assert_called_once_with("P1")

        # Get process
        kuix.get_process.return_value = "P1"
        self.assertEqual(api.get_process("P1"), "P1")
        kuix.get_process.assert_called_once_with("P1")

        # Close process
        api.close_process("P1")
        kuix.close_process.assert_called_once_with("P1", True)

        # -- Abstractions --
        # Process call
        process_mock = Mock()
        kuix.get_process.return_value = process_mock
        mock_component = Mock()
        mock_component.method.return_value = "OK"
        kuix.components = {"C1": mock_component}

        api.call_kuix_component("C1", "method", 10, 20, a=30, b=40)
        mock_component.method.assert_called_once_with(10, 20, a=30, b=40)
        # Exception
        with self.assertRaises(UnknownComponentError):
            api.call_kuix_component("C2", "method", 10, 20, a=30, b=40)
        kuix.components = {"C1": ""}
        with self.assertRaises(UnknownComponentMethodError):
            api.call_kuix_component("C1", "method2", 10, 20, a=30, b=40)

        # add worker
        kuix.workers = {}
        mock_worker = Mock()
        mock_worker.worker_identifier = "W1"
        api.add_worker("P1", mock_worker)
        self.assertEqual(kuix.workers["W1"], "P1")
        # exception
        process_mock.add_worker.side_effect = WorkerAlreadyAddedError("W1")
        with self.assertRaises(WorkerAlreadyAddedError):
            api.add_worker("P1", mock_worker)
        kuix.is_process.return_value = False
        with self.assertRaises(UnknownKxProcessError):
            api.add_worker("P2", mock_worker)
        kuix.is_process.return_value = True

        # load worker
        kuix.workers = {}
        mock_worker = Mock()
        mock_worker.worker_identifier = "W1"
        api.load_worker("P1", mock_worker)
        self.assertEqual(kuix.workers["W1"], "P1")
        # exception
        process_mock.add_worker.side_effect = WorkerAlreadyAddedError("W1")
        with self.assertRaises(WorkerAlreadyAddedError):
            api.add_worker("P1", mock_worker)
        kuix.is_process.return_value = False
        with self.assertRaises(UnknownKxProcessError):
            api.add_worker("P2", mock_worker)
        kuix.is_process.return_value = True

        # Is worker in process
        process_mock.is_worker.return_value = True
        self.assertTrue(api.is_worker_in_process("P1", "W1"))
        process_mock.is_worker.assert_called_once_with("W1")
        kuix.is_process.return_value = False
        with self.assertRaises(UnknownKxProcessError):
            api.is_worker_in_process("P2", "W1")
        kuix.is_process.return_value = True

        # Is worker
        self.assertTrue(api.is_worker("W1"))

        # Remove worker
        kuix.is_process.return_value = True
        kuix.get_process.return_value = process_mock
        api.remove_worker("W1")
        process_mock.remove_worker.assert_called_once_with("W1")
        self.assertNotIn("W1", kuix.workers)

        # Is Worker Opened
        kuix.workers = {"W1": "P1"}
        process_mock.is_worker_opened.return_value = True
        self.assertTrue(api.is_worker_opened("W1"))
        process_mock.is_worker_opened.assert_called_once_with("W1")

        # Is Worker Running
        process_mock.is_worker_running.return_value = True
        self.assertTrue(api.is_worker_running("W1"))
        process_mock.is_worker_running.assert_called_once_with("W1")

        # Process Id Of Worker
        self.assertEqual(api.get_process_id_of_worker("W1"), "P1")
        kuix.workers = {}
        with self.assertRaises(UnknownWorkerError):
            api.get_process_id_of_worker("W1")

        # Open Worker
        kuix.workers = {"W1": "P1"}
        api.open_worker("W1")
        process_mock.open_worker.assert_called_once_with("W1")

        # Start Worker
        kuix.workers = {"W1": "P1"}
        api.start_worker("W1")
        process_mock.start_worker.assert_called_once_with("W1")

        # Stop Worker
        kuix.workers = {"W1": "P1"}
        api.stop_worker("W1")
        process_mock.stop_worker.assert_called_once_with("W1")

        # Close Worker
        kuix.workers = {"W1": "P1"}
        api.close_worker("W1")
        process_mock.close_worker.assert_called_once_with("W1")

        # Kill Worker
        kuix.workers = {"W1": "P1"}
        api.kill_worker("W1")
        process_mock.kill_worker.assert_called_once_with("W1")

        # Is component
        component = Mock()
        kuix.components = {"C1": component}
        self.assertTrue(api.is_component("C1"))
        self.assertFalse(api.is_component("C2"))

        # Get component
        self.assertEqual(api.get_component("C1"), component)
        with self.assertRaises(UnknownComponentError):
            api.get_component("C2")

        # Remove component
        api.remove_component("C1")
        self.assertNotIn("C1", kuix.components)
        with self.assertRaises(UnknownComponentError):
            api.remove_component("C1")

        # Is Component Opened
        kuix.components = {"C1": component}
        component.is_opened.return_value = True
        self.assertTrue(api.is_component_opened("C1"))
        component.is_opened.assert_called_once_with()
        with self.assertRaises(UnknownComponentError):
            api.is_component_opened("C2")

        # Is Component Running
        kuix.components = {"C1": component}
        component.is_running.return_value = True
        self.assertTrue(api.is_component_running("C1"))
        component.is_running.assert_called_once_with()
        with self.assertRaises(UnknownComponentError):
            api.is_component_running("C2")

        # Is Component Closed
        kuix.components = {"C1": component}
        component.is_closed.return_value = True
        self.assertTrue(api.is_component_closed("C1"))
        component.is_closed.assert_called_once_with()
        with self.assertRaises(UnknownComponentError):
            api.is_component_closed("C2")

        # Open Component
        kuix.components = {"C1": component}
        api.open_component("C1")
        component.open.assert_called_once_with()
        with self.assertRaises(UnknownComponentError):
            api.open_component("C2")

        # Start Component
        kuix.components = {"C1": component}
        api.start_component("C1")
        component.start.assert_called_once_with()
        with self.assertRaises(UnknownComponentError):
            api.start_component("C2")

        # Stop Component
        kuix.components = {"C1": component}
        api.stop_component("C1")
        component.stop.assert_called_once_with()
        with self.assertRaises(UnknownComponentError):
            api.stop_component("C2")

        # Close Component
        kuix.components = {"C1": component}
        api.close_component("C1")
        component.close.assert_called_once_with()
        with self.assertRaises(UnknownComponentError):
            api.close_component("C2")

        # Subscribe
        kuix.connector = Mock()
        api.subscribe("UNITTEST_EVENT", "callback")
        kuix.connector.subscribe.assert_called_once_with("UNITTEST_EVENT", "callback")

        # Unsubscribe
        kuix.connector = Mock()
        api.unsubscribe("UNITTEST_EVENT", "callback")
        kuix.connector.unsubscribe.assert_called_once_with("UNITTEST_EVENT", "callback")

        # Trigger event
        kuix.connector = Mock()
        api.trigger_event("UNITTEST_EVENT", "data")
        kuix.connector.trigger_event.assert_called_once_with("UNITTEST_EVENT", "data")

    def unit_instance(self):
        print(Colors.MAGENTA + "Kuix 2/ Instance" + Colors.END)
        # 1/ Instance
        self.kuix = Kuix('.')
        # Check for the filesystem
        self.assertTrue(os.path.exists('./kuix'))
        self.assertTrue(os.path.exists('./kuix/logs'))
        self.assertTrue(os.path.exists('./kuix/persistence'))
        self.assertEqual(self.kuix.path, './kuix/')
        # Check exception
        with self.assertRaises(KuixSetupError):
            Kuix('//')

    def unit_basics(self):
        print(Colors.MAGENTA + "Kuix 3/ Basics" + Colors.END)
        # 1/ Add Component
        with patch('kuix.core.kuix_core.logger') as logger_mock:
            mock_component = Mock()
            self.assertEqual(mock_component, self.kuix.add_component("C1", mock_component))
            self.assertEqual(self.kuix.components, {"C1": mock_component})
            logger_mock.warning.assert_called_once_with(
                kuix.core.kuix_core.NOT_INHERITED_COMPONENT_WARNING.format(self.kuix.prefix,
                                                                           type(mock_component).__name__, "C1"),
                kuix.core.kuix_core.ROUTE)
        # 2/ get Api
        self.assertEqual(self.kuix.get_api(), self.kuix.api)

        # 3/ Load config
        self.kuix.configured = False
        self.kuix._load_config()
        self.assertTrue(self.kuix.configured)
        # Exception
        with self.assertRaises(AlreadyConfiguredError):
            self.kuix._load_config()
        self.kuix.configured = False
        self.kuix._load_json_config()
        self.assertTrue(self.kuix.configured)
        # Exception
        with self.assertRaises(AlreadyConfiguredError):
            self.kuix._load_json_config()

        # 4/ Kuix Setup
        with patch("kuix.core.kuix_core.Connector") as mock_connector_cls:
            with patch("kuix.core.kuix_core.new_hub") as mock_new_hub:
                mock_connector = Mock()
                mock_connector_cls.return_value = mock_connector
                mock_hub = Mock()
                mock_new_hub.return_value = mock_hub
                self.kuix.setup()
                self.assertTrue(self.kuix.is_setup)
                self.assertEqual(self.kuix.connector, mock_connector)
                self.assertEqual(self.kuix.shared_hub, mock_hub)
                mock_connector_cls.assert_called_once_with("main", self.kuix.api, mock_hub)
                # Do nothing if already setup
                mock_connector_cls.reset_mock()
                self.kuix.setup()
                mock_connector_cls.assert_not_called()
                # Require Configured Exception
                self.kuix.configured = False
                with self.assertRaises(NotConfiguredError):
                    self.kuix.setup()
                self.kuix.configured = True

        # 5/ Kuix Close
        mock_process = Mock()
        mock_component.reset_mock()
        bad_mock_component = Mock()
        bad_mock_component.close.side_effect = KuixComponentCoreMethodCallError("close")
        self.kuix.kx_processes = {"P1": mock_process}
        self.kuix.components = {"C1": mock_component, "C2": bad_mock_component}
        with patch('kuix.core.kuix_core.logger') as logger_mock:
            self.kuix.close()
        mock_process.close.assert_called_once()
        mock_component.close.assert_called_once()
        bad_mock_component.close.assert_called_once()
        logger_mock.warning.assert_called_once()
        mock_connector.close.assert_called_once()
        self.assertTrue(self.kuix.is_closed)
        with self.assertRaises(ClosedError):
            self.kuix.close()
        self.kuix.is_closed = False

    def unit_processes(self):
        print(Colors.MAGENTA + "Kuix 4/ Processes" + Colors.END)
        #  1/ Create Process
        self.kuix.kx_processes = {}
        with patch("kuix.core.kuix_core.KxProcessAPI") as mock_kx_process_api_cls:
            mock_kx_process_api = Mock()
            mock_kx_process_api_cls.return_value = mock_kx_process_api
            with patch("kuix.core.kuix_core.new_kx_process") as mock_new_process:
                def callback(*args, **kwargs):
                    self.kuix.__created__ = True

                mock_new_process.side_effect = callback
                self.kuix.create_process("P1")
        self.kuix.connector.subscribe.assert_called_once()
        mock_new_process.assert_called_once_with("P1", self.kuix.path, self.kuix.shared_hub)
        mock_kx_process_api_cls.assert_called_once_with(None)
        mock_kx_process_api._enable_remote.assert_called_once_with("P1", self.kuix.shared_hub)
        self.assertEqual(self.kuix.kx_processes, {"P1": mock_kx_process_api})
        self.kuix.connector.add_instanced_api.assert_called_once_with("P1", mock_kx_process_api)
        # Exception
        with self.assertRaises(KxProcessAlreadyExistsError):
            self.kuix.create_process("P1")
        self.kuix.is_setup = False
        with self.assertRaises(NotSetupError):
            self.kuix.create_process("P2")
        self.kuix.is_setup = True

        # 2/ Is process
        self.assertTrue(self.kuix.is_process("P1"))
        self.assertFalse(self.kuix.is_process("P2"))
        # Exception
        self.kuix.is_setup = False
        with self.assertRaises(NotSetupError):
            self.kuix.is_process("P1")
        self.kuix.is_setup = True

        # 3/ Get process
        self.assertEqual(self.kuix.get_process("P1"), mock_kx_process_api)
        # Exception
        self.kuix.is_setup = False
        with self.assertRaises(NotSetupError):
            self.kuix.get_process("P1")
        self.kuix.is_setup = True
        with self.assertRaises(UnknownKxProcessError):
            self.kuix.get_process("P2")

        # 4/ Close Process
        self.kuix.kx_processes = {"P1": mock_kx_process_api}
        self.kuix.workers = {"W1": "P1"}
        self.kuix.close_process("P1")
        mock_kx_process_api.kill.assert_called_once()
        self.assertEqual(self.kuix.kx_processes, {})
        self.assertEqual(self.kuix.workers, {})
        # With close
        mock_kx_process_api.reset_mock()
        self.kuix.kx_processes = {"P1": mock_kx_process_api}
        self.kuix.close_process("P1", kill=False)
        mock_kx_process_api.close.assert_called_once()
        self.assertEqual(self.kuix.kx_processes, {})
        # Exception
        self.kuix.is_setup = False
        with self.assertRaises(NotSetupError):
            self.kuix.close_process("P1")
        self.kuix.is_setup = True
        with self.assertRaises(UnknownKxProcessError):
            self.kuix.close_process("P2")
        mock_kx_process_api.reset_mock()
        mock_kx_process_api.close.side_effect = WorkerMethodCallError("close")
        self.kuix.kx_processes = {"P1": mock_kx_process_api}
        with self.assertRaises(WorkerMethodCallError):
            self.kuix.close_process("P1", kill=False)

    def runTest(self):
        print(Colors.CYAN + Colors.BOLD + f"--- RUNNING Kuix UNIT TEST ---" + Colors.END)
        self.unit_api()
        self.unit_instance()
        self.unit_basics()
        self.unit_processes()
        print(Colors.CYAN + Colors.BOLD + f"--- PASSED Kuix UNIT TEST ---\n" + Colors.END)
        time.sleep(0.1)

    def tearDown(self):
        # Remove the filesystem
        shutil.rmtree('./kuix', ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
