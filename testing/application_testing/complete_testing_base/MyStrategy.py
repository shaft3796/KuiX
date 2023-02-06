import time

from src.strategies.BaseStrategy import BaseStrategy


class MyStrategy(BaseStrategy):

    def __init__(self, identifier):
        super().__init__(identifier)
        self._name = "MyStrategy"
        self._version = "0.0.1"
        self._author = "KuiX"
        self._description = "MyStrategy"

    def strategy(self):
        while True:
            print("Hello World!")
            self.check_status()
            time.sleep(1)

    def stop_strategy(self):
        print("Stopping MyStrategy")
