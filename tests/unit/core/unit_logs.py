import os
import sys
import time
import shutil
import unittest
from colorama import Fore, Style

from kuix.core.exceptions import KuixException
from kuix.core.logs import logger, kuix_io, KuixIO, Log, Levels, Logger
from unittest.mock import patch, Mock


class UnitLogs(unittest.TestCase):

    def setUp(self):
        pass

    def unit_kuix_io(self):
        print(Fore.MAGENTA + "Logger 1/ Kuix IO" + Style.RESET_ALL)
        # We will use the global instance
        # Path the stdout with a mock object
        with patch('sys.__stdout__') as mock_stdout:
            # 1/ Write
            kuix_io.write("Test")
            mock_stdout.write.assert_called_once_with("Test")

            # 2/ Flush
            kuix_io.flush()
            mock_stdout.flush.assert_called_once()
            with open("/tmp/out.kuix", "r") as f:
                self.assertIn("Test", f.read())

            # 3/ Close
            kio = KuixIO("/tmp/out.kuix")
            kio.kuix.close()
            kio.kuix = Mock()
            kio.close()
            mock_stdout.close.assert_called_once()
            kio.kuix.close.assert_called_once()

    def unit_log(self):
        print(Fore.MAGENTA + "Logger 2/ Log" + Style.RESET_ALL)
        # 1/ Initialization
        log = Log("Test", Levels.INFO, 0)

        # 2/ to_dict
        # We check that there is no error
        log.to_dict()

        # 3/ to_string
        # We check that there is no error
        log.to_string()

    def unit_logger(self):
        print(Fore.MAGENTA + "Logger 3/ Logger" + Style.RESET_ALL)
        # 1/ Initialization
        _logger = Logger("/tmp/kuix_tmp_logs")
        with open('/tmp/kuix_tmp_logs/info.json', 'r') as f:
            self.assertEqual('', f.read())

        # 2/ Log
        # Patch stdout
        with patch('sys.stdout') as mock_stdout:
            # Wrong level exception
            with self.assertRaises(KuixException):
                _logger.log("Test", "WRONG_LVL")

            # Log
            now = str(int(time.time()))
            _logger.log("Test", Levels.INFO)
            mock_stdout.write.assert_called()
            with open('/tmp/kuix_tmp_logs/info.json', 'r') as f:
                self.assertEqual('{\n"time": ' + now + ',\n"data": "Test",\n"level": "INFO"\n}\n', f.read())

            # Debug and verbose mode
            mock_stdout.reset_mock()
            _logger.log("Test", Levels.DEBUG)
            mock_stdout.write.assert_not_called()
            _logger.log("Test", Levels.DEBUG)
            mock_stdout.write.assert_not_called()
            _logger.enable_debug()
            _logger.log("Test", Levels.DEBUG)
            mock_stdout.write.assert_called()
            mock_stdout.reset_mock()
            _logger.enable_verbose()
            _logger.log("Test", Levels.TRACE)
            mock_stdout.write.assert_called()

        # 3/ Log shortcuts
        _logger.log = Mock()
        _logger.trace("Test")
        _logger.log.assert_called_once_with("Test", Levels.TRACE)
        _logger.info("Test")
        _logger.log.assert_called_with("Test", Levels.INFO)
        _logger.warning("Test")
        _logger.log.assert_called_with("Test", Levels.WARNING)
        _logger.error("Test")
        _logger.log.assert_called_with("Test", Levels.ERROR)
        _logger.critical("Test")
        _logger.log.assert_called_with("Test", Levels.CRITICAL)
        _logger.debug("Test")
        _logger.log.assert_called_with("Test", Levels.DEBUG)

    def unit_hook(self):
        print(Fore.MAGENTA + "Logger 4/ Hook" + Style.RESET_ALL)
        with patch("kuix.core.logs.logger") as mock_logger:
            # 1/ Call
            sys.excepthook(None, "VALUE", None)
            mock_logger.critical.assert_called_once_with("VALUE")
            # 2/ Exception
            mock_logger.reset_mock()
            mock_logger.critical.side_effect = Exception("Test")
            with patch("sys.stdout") as mock_stdout:
                sys.excepthook(None, "VALUE", None)
                exp = "Error while logging: Test"
                self.assertIn(exp, [call[0][0] for call in mock_stdout.write.call_args_list[:-1]])



    def runTest(self):
        print(Fore.CYAN + "\033[1m" + f"--- RUNNING Logger UNIT TEST ---" + Style.RESET_ALL)
        self.unit_kuix_io()
        self.unit_log()
        self.unit_logger()
        self.unit_hook()
        print(Fore.CYAN + "\033[1m" + f"--- PASSED Logger UNIT TEST ---\n" + Style.RESET_ALL)
        time.sleep(0.1)

    def tearDown(self) -> None:
        # Remove the temp directory
        shutil.rmtree("/tmp/kuix_tmp_logs")


if __name__ == '__main__':
    unittest.main()
