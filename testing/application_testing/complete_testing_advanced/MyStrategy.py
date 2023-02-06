import time

from src.strategies.BaseStrategy import BaseStrategy


class MyStrategy(BaseStrategy):

    def __init__(self, process, identifier):
        super().__init__(process, identifier)
        self._name = "MyStrategy"
        self._version = "0.0.1"
        self._author = "KuiX"
        self._description = "MyStrategy"

    def strategy(self):
        while True:
            self.process.send("log", {"worker": self.identifier, "message": "Hello from MyStrategy!"})
            self.check_status()
            time.sleep(1)

