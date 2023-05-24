import time
import unittest
from colorama import Fore, Style
from kuix.core.exceptions import KuixException, Contextualize


class UnitExceptions(unittest.TestCase):

    def setUp(self):
        pass

    def unit_kuix_exception(self):
        print(Fore.MAGENTA + "Exceptions 1/ Kuix Exception" + Fore.RESET)
        # 1/ Initialization
        ex = KuixException("Err")
        self.assertEqual("Err", str(ex))

        # 2/ Contextualize
        ex.contextualize("Context").contextualize("Context2")
        self.assertEqual(["Context", "Context2"], ex.context)

        # 3/ Add
        ex2 = KuixException("Err2").contextualize("Context3")
        ex += ex2
        self.assertEqual([ex2], ex.exceptions)

        # 4/ Format
        # used to add traceback frames to the exception
        try:
            raise Exception("Err")
        except Exception as e:
            ex += e
        ex.format(Fore.CYAN)  # We just check that there is no error

    def unit_contextualize(self):
        print(Fore.MAGENTA + "Exceptions 2/ Contextualize" + Fore.RESET)
        # 1/ All in one
        try:
            with Contextualize("Context"):
                raise KuixException("Err")
        except KuixException as e:
            self.assertEqual(["Context"], e.context)

        # 2/ Default message
        try:
            with Contextualize(1):
                raise KuixException("Err")
        except KuixException as e:
            exp = ["Unable to set context. Context must be a string. This line has no relation with the error !"]
            self.assertEqual(exp, e.context)

        # 3/ No exception
        with Contextualize("Context"):
            pass

    def runTest(self):
        print(Fore.CYAN + "\033[1m" + f"--- RUNNING Exceptions UNIT TEST ---" + Style.RESET_ALL)
        self.unit_kuix_exception()
        self.unit_contextualize()
        print(Fore.CYAN + "\033[1m" + f"--- PASSED Exceptions UNIT TEST ---\n" + Style.RESET_ALL)
        time.sleep(0.1)


if __name__ == '__main__':
    unittest.main()
