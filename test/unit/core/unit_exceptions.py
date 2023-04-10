import unittest

from kuix.core.exception import GenericException, _dump_exception, format_exception_stack, cast, Context
from kuix.core.logger import logger
from kuix.core.utils import Colors


class UnitExceptions(unittest.TestCase):

    def setUp(self):
        pass

    def generic_exception(self):
        print(Colors.MAGENTA + "Exceptions 1/ generic exception" + Colors.END)
        # 1/ Instance
        e = GenericException("Test")
        self.assertEqual(e.base_msg, "Test")

        # 2/ Add Context
        e = GenericException("Test")
        self.assertEqual([], e.ctx)
        e.add_ctx("TestCtx").add_ctx("TestCtx2")
        self.assertEqual(["TestCtx", "TestCtx2"], e.ctx)

        # 3/ Str
        e = GenericException("Test")
        self.assertEqual("Test", str(e))

    def dump_exception(self):
        print(Colors.MAGENTA + "Exceptions 2/ dump exception" + Colors.END)
        # 1/ Call
        e0 = GenericException("Test0").add_ctx("TestCtx01").add_ctx("TestCtx02")
        e1 = GenericException("Test1").add_ctx("TestCtx11").add_ctx("TestCtx2")
        e = e0 + e1
        e2 = Exception("Test2")
        dump = _dump_exception(e)
        dump2 = _dump_exception(e2)
        # dump
        self.assertEqual(2, len(dump))
        self.assertEqual("Test0", dump[0]["base_msg"])
        self.assertEqual(["TestCtx01", "TestCtx02"], dump[0]["ctx"])
        self.assertEqual("GenericException", dump[0]["type"])
        self.assertEqual("Test1", dump[1]["base_msg"])
        self.assertEqual(["TestCtx11", "TestCtx2"], dump[1]["ctx"])
        self.assertEqual("GenericException", dump[1]["type"])
        # dump2
        self.assertEqual(1, len(dump2))
        self.assertEqual("Test2", dump2[0]["base_msg"])
        self.assertEqual([], dump2[0]["ctx"])
        self.assertEqual("Exception", dump2[0]["type"])

    def generic_exception_2(self):
        print(Colors.MAGENTA + "Exceptions 3/ generic exception 2" + Colors.END)

        # 1/ Add
        e0 = GenericException("Test0").add_ctx("TestCtx01").add_ctx("TestCtx02")
        e1 = Exception("Test1")
        e = e0 + e1
        self.assertEqual("Test0", e.base_msg)
        self.assertEqual(["TestCtx01", "TestCtx02"], e.ctx)
        self.assertEqual("GenericException", type(e).__name__)
        self.assertEqual("Exception", e.initial_type)
        self.assertEqual("Test1", e.initial_msg)
        self.assertEqual(1, len(e.tracebacks))

    def format_exception(self):
        print(Colors.MAGENTA + "Exceptions 4/ format exception" + Colors.END)

        # 1/ Format
        e0 = GenericException("Test0").add_ctx("TestCtx01").add_ctx("TestCtx02") + GenericException("Test1")
        e = None  # PLACEHOLDER
        try:
            raise e0
        except GenericException as _e:
            e = _e
        frm = format_exception_stack(e)
        self.assertIn("Test0", frm)
        self.assertIn("TestCtx01", frm)
        self.assertIn("TestCtx02", frm)

        # 2/ No Color
        frm = format_exception_stack(e, no_color=True)
        self.assertNotIn(Colors.RED, frm)

    def cast(self):
        print(Colors.MAGENTA + "Exceptions 5/ cast" + Colors.END)
        e = Exception("Test")
        e1 = cast(e, "casted")
        self.assertEqual("casted", e1.base_msg)
        self.assertEqual("GenericException", type(e1).__name__)

    def context_manager(self):
        print(Colors.MAGENTA + "Exceptions 6/ context manager" + Colors.END)

        # 1/ Instance
        ctx = Context("foo")
        self.assertEqual("foo", ctx.ctx)
        ctx = Context(1)
        expected = "Unable to set context. Context must be a string. This line has no relation with the error !"
        self.assertEqual(expected, ctx.ctx)

        # 2/ Context manager
        try:
            with Context("foo"):
                raise GenericException("Test")
        except GenericException as e:
            self.assertEqual(["foo"], e.ctx)
        # no exception
        with Context("foo"):
            pass

    def runTest(self):
        print(Colors.CYAN + Colors.BOLD + f"--- RUNNING Exceptions UNIT TEST ---" + Colors.END)
        self.generic_exception()
        self.dump_exception()
        self.generic_exception_2()
        self.format_exception()
        self.cast()
        self.context_manager()
        print(Colors.CYAN + Colors.BOLD + f"--- PASSED Exceptions UNIT TEST ---" + Colors.END)


if __name__ == '__main__':
    unittest.main()
