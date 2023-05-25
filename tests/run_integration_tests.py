import unittest


def run_integration_tests():
    suite = unittest.TestSuite()
    # Run
    runner = unittest.TextTestRunner()
    runner.run(suite)


if __name__ == '__main__':
    run_integration_tests()
