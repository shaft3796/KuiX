# Utils
from unit.core.unit_utils import UnitUtils
# Exceptions
from unit.core.unit_exceptions import UnitExceptions
# Logger
from unit.core.unit_logger import UnitLogger
# Stateful
from unit.core.unit_stateful import UnitStateful
# SharedHub
from unit.core.unit_shared_hub import UnitSharedHub
# API
from unit.core.unit_api import UnitApi
# Connector
from unit.core.unit_connector import UnitConnector
# Worker Components
from unit.worker_components.unit_base_worker_component import UnitBaseWorkerComponent
# Worker
from unit.worker.unit_base_worker import UnitBaseWorker
# Kuix Components
from unit.kuix_components.unit_base_kuix_component import UnitBaseKuixComponent
# KxProcess
from unit.core.unit_kx_process import UnitKxProcess
# Kuix
from unit.core.unit_kuix import UnitKuix

# --- Built-in Worker Components ---
# --- Built-in Kuix Components ---


import unittest


def run_unit_tests():
    suite = unittest.TestSuite()
    # Utils
    suite.addTest(UnitUtils())
    # Exceptions
    suite.addTest(UnitExceptions())
    # Logger
    suite.addTest(UnitLogger())
    # Stateful
    suite.addTest(UnitStateful())
    # SharedHub
    suite.addTest(UnitSharedHub())
    # API
    suite.addTest(UnitApi())
    # Connector
    suite.addTest(UnitConnector())
    # Worker Components
    suite.addTest(UnitBaseWorkerComponent())
    # Worker
    suite.addTest(UnitBaseWorker())
    # Kuix Components
    suite.addTest(UnitBaseKuixComponent())
    # KxProcess
    suite.addTest(UnitKxProcess())
    # Kuix
    suite.addTest(UnitKuix())
    # --- Built-in Worker Components ---
    # WorkerCommunicatorComponent
    # --- Built-in Kuix Components ---
    # Run
    runner = unittest.TextTestRunner()
    runner.run(suite)


if __name__ == '__main__':
    run_unit_tests()
