import threading
import time
import unittest
from kuix.core.utils import Colors, Lockable


class Test(Lockable):

    def __init__(self):
        super().__init__()
        self.value = 0

    @Lockable.locked
    def take(self, value):
        self.value = value
        time.sleep(1)


class UnitUtils(unittest.TestCase):

    def setUp(self):
        pass

    def unit_lockable(self):
        print(Colors.MAGENTA + "Utils 1/ lockable" + Colors.END)
        # 1/ Instance
        lockable = Lockable()

        # 2/ locked decorator
        test = Test()
        threading.Thread(target=test.take, args=(1,)).start()
        while test.value == 0:
            pass
        threading.Thread(target=test.take, args=(2,)).start()
        time.sleep(0.1)
        self.assertEqual(test.value, 1)
        while test.value == 1:
            pass
        self.assertEqual(test.value, 2)

    def runTest(self):
        print(Colors.CYAN + Colors.BOLD + f"--- RUNNING Utils UNIT TEST ---" + Colors.END)
        self.unit_lockable()
        print(Colors.CYAN + Colors.BOLD + f"--- PASSED Utils UNIT TEST ---\n" + Colors.END)
        time.sleep(0.1)


if __name__ == '__main__':
    unittest.main()
