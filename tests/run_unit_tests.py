# Exceptions
from unit.core.unit_exceptions import UnitExceptions
# Utils
from unit.core.unit_utils import UnitUtils
# Logs
from unit.core.unit_logs import UnitLogs

# --- Built-in Worker Components ---
# --- Built-in Kuix Components ---


import unittest


def run_unit_tests():
    suite = unittest.TestSuite()
    # Exceptions
    suite.addTest(UnitExceptions())
    # Utils
    suite.addTest(UnitUtils())
    # Logs
    suite.addTest(UnitLogs())

    # --- Built-in Worker Components ---
    # --- Built-in Kuix Components ---

    # Run
    runner = unittest.TextTestRunner()
    runner.run(suite)


if __name__ == '__main__':
    run_unit_tests()
