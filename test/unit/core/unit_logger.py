import os
import sys
import threading
import time
import unittest
from kuix.core.logger import logger, Log, KuixIO, kuix_override
from kuix.core.utils import Colors


class UnitLogger(unittest.TestCase):

    def setUp(self):
        pass

    def kuix_io(self):
        print(Colors.MAGENTA + "Logger 1/ KuixIO" + Colors.END)
        kuix_override()  # We have to force override because of the unit tests
        # 1/ Check instance
        kuix_io = sys.stdout
        self.assertTrue(isinstance(kuix_io, KuixIO))

        # 2/ Check redirection
        expected = str(time.time())
        print(expected)
        kuix_io.flush()  # Force flushing
        with open("/tmp/kuix_out.txt", "r") as f:
            actual = f.read()
            # isolate the last line
            actual = actual.split("\n")[-2]
        self.assertEqual(expected, actual)

    def log_cls(self):
        print(Colors.MAGENTA + "Logger 2/ Log cls" + Colors.END)
        # 1/ Instance
        log = Log("msg", "INFO", "UNKNOWN", "2020-01-01 00:00:00")
        self.assertEqual(log.data, "msg")
        self.assertEqual(log.type, "INFO")
        self.assertEqual(log.route, "UNKNOWN")
        self.assertEqual(log.log_time, "2020-01-01 00:00:00")

        # 2/ To dict
        log_dict = log.to_dict()
        self.assertEqual(log_dict["data"], "msg")
        self.assertEqual(log_dict["type"], "INFO")
        self.assertEqual(log_dict["route"], "UNKNOWN")
        self.assertEqual(log_dict["time"], "2020-01-01 00:00:00")

        # 3/ To string
        log_str = log.to_string()
        self.assertEqual(log_str, f"{Colors.BGREEN}{Colors.BLACK}[2020-01-01 00:00:00] INFO from UNKNOWN:{Colors.END}"
                                  f"{Colors.GREEN} msg{Colors.END}")

    def logger_instance(self):
        print(Colors.MAGENTA + "Logger 3/ Logger instance" + Colors.END)

        # 1/ log method
        sys.stdout.muted = True  # Mute std
        expected = f"{Colors.BGREEN}{Colors.BLACK}[{time.strftime('%d-%m-%y %H:%M:%S')}] INFO from UNKNOWN:" \
                   f"{Colors.END}{Colors.GREEN} {Colors.END}\n"
        logger.log("", "INFO")
        sys.stdout.flush()  # Force flushing
        with open("/tmp/kuix_out.txt", "r") as f:
            # Read last line
            actual = f.readlines()[-1]
        sys.stdout.muted = False  # Unmute std
        self.assertEqual(expected, actual)

        # 2/ Shortcut methods
        sys.stdout.muted = True  # Mute std
        # TRACE
        logger.trace("test1")
        sys.stdout.flush()  # Force flushing
        with open("/tmp/kuix_out.txt", "r") as f:
            self.assertNotIn("test1", f.readlines()[-1])
        logger.enable_verbose()
        logger.trace("test1")
        sys.stdout.flush()  # Force flushing
        with open("/tmp/kuix_out.txt", "r") as f:
            self.assertIn("test1", f.readlines()[-1])

        # INFO
        logger.info("test2")
        sys.stdout.flush()  # Force flushing
        with open("/tmp/kuix_out.txt", "r") as f:
            self.assertIn("test2", f.readlines()[-1])

        # WARN
        logger.warning("test3")
        sys.stdout.flush()  # Force flushing
        with open("/tmp/kuix_out.txt", "r") as f:
            self.assertIn("test3", f.readlines()[-1])

        # ERROR
        logger.error("test4")
        sys.stdout.flush()  # Force flushing
        with open("/tmp/kuix_out.txt", "r") as f:
            self.assertIn("test4", f.readlines()[-1])

        # CRITICAL
        logger.critical("test5")
        sys.stdout.flush()  # Force flushing
        with open("/tmp/kuix_out.txt", "r") as f:
            self.assertIn("test5", f.readlines()[-1])

        # DEBUG
        logger.debug("test6")
        sys.stdout.flush()  # Force flushing
        with open("/tmp/kuix_out.txt", "r") as f:
            self.assertIn("test6", f.readlines()[-1])

        # 3/ file logging
        logger.enable_file_logging("/tmp/kuix")
        self.assertTrue(os.path.exists("/tmp/kuix"))
        self.assertTrue(os.path.exists("/tmp/kuix/unknown.kuix"))
        self.assertTrue(os.path.exists("/tmp/kuix/info.kuix"))
        self.assertTrue(os.path.exists("/tmp/kuix/warning.kuix"))
        self.assertTrue(os.path.exists("/tmp/kuix/error.kuix"))
        self.assertTrue(os.path.exists("/tmp/kuix/critical.kuix"))
        self.assertTrue(os.path.exists("/tmp/kuix/debug.kuix"))
        logger.info("test10")
        logger.warning("test11")
        logger.error("test12")
        logger.critical("test13")
        logger.debug("test14")
        logger.unknown("test15")
        with open("/tmp/kuix/info.kuix", "r") as f:
            self.assertIn("test10", f.read())
        with open("/tmp/kuix/warning.kuix", "r") as f:
            self.assertIn("test11", f.read())
        with open("/tmp/kuix/error.kuix", "r") as f:
            self.assertIn("test12", f.read())
        with open("/tmp/kuix/critical.kuix", "r") as f:
            self.assertIn("test13", f.read())
        with open("/tmp/kuix/debug.kuix", "r") as f:
            self.assertIn("test14", f.read())
        with open("/tmp/kuix/unknown.kuix", "r") as f:
            self.assertIn("test15", f.read())

        sys.stdout.muted = False  # Unmute std

    def runTest(self):
        print(Colors.CYAN + Colors.BOLD + f"--- RUNNING Logger UNIT TEST ---" + Colors.END)
        self.log_cls()
        self.kuix_io()
        self.logger_instance()
        print(Colors.CYAN + Colors.BOLD + f"--- PASSED Logger UNIT TEST ---" + Colors.END)


if __name__ == '__main__':
    unittest.main()
